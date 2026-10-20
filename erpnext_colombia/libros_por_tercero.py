"""Saldos y movimientos del libro mayor por cuenta y tercero, para el balance de prueba y el auxiliar."""

from collections import defaultdict

import frappe
from frappe.query_builder import Case
from frappe.query_builder.functions import Sum
from frappe.utils import flt, getdate

SIN_TERCERO = None


class LibroPorTercero:
	"""Lee el GL Entry de una empresa entre dos fechas, opcionalmente para una cuenta (con sus hijas) y un tercero.

	Como en el balance de prueba de ERPNext, es saldo inicial lo anterior a la fecha inicial y lo marcado
	como apertura aunque caiga dentro del rango.
	"""

	def __init__(self, filtros):
		self.empresa = filtros.get("company")
		self.desde = getdate(filtros.get("from_date"))
		self.hasta = getdate(filtros.get("to_date"))
		self.cuenta = filtros.get("account")
		self.tercero = filtros.get("tercero")
		self.gle = frappe.qb.DocType("GL Entry")

	def saldos(self) -> list[dict]:
		gle = self.gle
		inicial = self._es_inicial()
		filas = (
			self._base()
			.select(
				gle.account,
				gle.tercero,
				Sum(Case().when(inicial, gle.debit - gle.credit).else_(0)).as_("inicial"),
				Sum(Case().when(inicial, 0).else_(gle.debit)).as_("debito"),
				Sum(Case().when(inicial, 0).else_(gle.credit)).as_("credito"),
			)
			.groupby(gle.account, gle.tercero)
			.run(as_dict=True)
		)
		filas = [f for f in filas if f.inicial or f.debito or f.credito]
		for f in filas:
			f.final = flt(f.inicial) + flt(f.debito) - flt(f.credito)
		return self._con_nombres(sorted(filas, key=self._orden))

	def movimientos(self) -> list[dict]:
		"""Por cada cuenta y tercero, una fila de saldo inicial y luego sus movimientos con saldo corrido."""
		gle = self.gle
		inicial = self._es_inicial()
		filas = (
			self._base()
			.select(
				gle.account,
				gle.tercero,
				gle.posting_date,
				gle.voucher_type,
				gle.voucher_no,
				gle.remarks.as_("detalle"),
				gle.debit.as_("debito"),
				gle.credit.as_("credito"),
				Case().when(inicial, 1).else_(0).as_("es_inicial"),
			)
			.orderby(gle.posting_date)
			.orderby(gle.creation)
			.run(as_dict=True)
		)
		bloques = defaultdict(lambda: {"inicial": 0.0, "filas": []})
		for f in filas:
			bloque = bloques[(f.account, f.tercero)]
			if f.es_inicial:
				bloque["inicial"] += flt(f.debito) - flt(f.credito)
			else:
				bloque["filas"].append(f)

		salida = []
		for (cuenta, tercero), bloque in sorted(
			bloques.items(), key=lambda b: self._orden(frappe._dict(account=b[0][0], tercero=b[0][1]))
		):
			saldo = bloque["inicial"]
			salida.append(
				frappe._dict(
					account=cuenta,
					tercero=tercero,
					es_inicial=1,
					detalle="Saldo inicial",
					debito=0,
					credito=0,
					saldo=saldo,
				)
			)
			for f in bloque["filas"]:
				saldo += flt(f.debito) - flt(f.credito)
				f.saldo = saldo
				f.es_inicial = 0
				salida.append(f)
		return self._con_nombres(salida)

	def _base(self):
		gle = self.gle
		consulta = (
			frappe.qb.from_(gle)
			.where(gle.company == self.empresa)
			.where(gle.is_cancelled == 0)
			.where(gle.posting_date <= self.hasta)
		)
		if self.cuenta:
			consulta = consulta.where(gle.account.isin(self._cuentas_bajo(self.cuenta)))
		if self.tercero:
			consulta = consulta.where(gle.tercero == self.tercero)
		return consulta

	def _es_inicial(self):
		return (self.gle.posting_date < self.desde) | (self.gle.is_opening == "Yes")

	@staticmethod
	def _cuentas_bajo(cuenta: str) -> list[str]:
		lft, rgt = frappe.db.get_value("Account", cuenta, ["lft", "rgt"])
		return frappe.get_all("Account", filters={"lft": (">=", lft), "rgt": ("<=", rgt)}, pluck="name") or [
			cuenta
		]

	@staticmethod
	def _orden(fila) -> tuple:
		return (fila.account or "", fila.tercero or "")

	@staticmethod
	def _con_nombres(filas: list[dict]) -> list[dict]:
		terceros = {f.tercero for f in filas if f.tercero}
		datos = (
			{
				t.name: t
				for t in frappe.get_all(
					"Tercero",
					filters={"name": ("in", terceros)},
					fields=["name", "nombre_completo", "nit_completo"],
				)
			}
			if terceros
			else {}
		)
		for f in filas:
			t = datos.get(f.tercero)
			f.tercero_nombre = t.nombre_completo if t else None
			f.nit = t.nit_completo if t else None
		return filas
