"""Borradores de factura de venta con los honorarios que tocan en el mes."""

from collections import defaultdict

import frappe
from frappe.utils import add_days, getdate, today

from erpnext_colombia.honorarios.periodicidad import Honorario, Periodo

CONFIGURACION = "Configuracion de Honorarios"


class Facturador:
	"""Crea una factura en borrador por cliente y mes. Daniela la revisa y la envía.

	Un mes ya facturado no se repite, aunque su factura esté cancelada: si Daniela la cancela es porque
	ese mes no se cobra, y para corregirla la enmienda (la enmienda conserva el periodo).
	"""

	def __init__(
		self, empresa, articulo, dia_de_facturacion=1, dias_para_pagar=10, plantilla_impuestos=None, hoy=None
	):
		self.empresa = empresa
		self.articulo = articulo
		self.dia_de_facturacion = dia_de_facturacion or 1
		self.dias_para_pagar = dias_para_pagar or 0
		self.plantilla_impuestos = plantilla_impuestos
		self.hoy = getdate(hoy or today())

	@classmethod
	def desde_configuracion(cls, hoy=None) -> "Facturador":
		valor = lambda campo: frappe.db.get_single_value(CONFIGURACION, campo)  # noqa: E731
		return cls(
			empresa=valor("empresa"),
			articulo=valor("articulo"),
			dia_de_facturacion=valor("dia_de_facturacion"),
			dias_para_pagar=valor("dias_para_pagar"),
			plantilla_impuestos=valor("plantilla_impuestos"),
			hoy=hoy,
		)

	def facturar_si_toca(self) -> list[str]:
		if not self.empresa or self.hoy.day < self.dia_de_facturacion:
			return []
		return self.facturar(Periodo.de(self.hoy))

	def facturar(self, periodo: Periodo) -> list[str]:
		if not self.empresa:
			return []
		creadas = []
		for cliente, honorarios in self._honorarios_por_cliente().items():
			que_tocan = [h for h in honorarios if h.toca_en(periodo)]
			if not que_tocan or self._ya_facturado(cliente, periodo):
				continue
			# Un cliente con datos malos no puede dejar a los demás sin factura.
			try:
				creadas.append(self._crear(cliente, periodo, que_tocan))
			except Exception:
				frappe.log_error(title=f"Honorarios: no se pudo facturar {cliente} {periodo}")
		return creadas

	def _honorarios_por_cliente(self) -> dict[str, list[Honorario]]:
		inactivos = set(frappe.get_all("Customer", filters={"disabled": 1}, pluck="name"))
		filas = frappe.get_all(
			"Honorario del Cliente",
			filters={"parenttype": "Customer"},
			fields=["parent", "concepto", "valor", "periodicidad", "desde", "hasta"],
			order_by="parent, idx",
		)
		por_cliente = defaultdict(list)
		for f in filas:
			if f.parent in inactivos:
				continue
			por_cliente[f.parent].append(
				Honorario(
					f.concepto,
					f.valor,
					f.periodicidad,
					getdate(f.desde),
					getdate(f.hasta) if f.hasta else None,
				)
			)
		return por_cliente

	@staticmethod
	def _ya_facturado(cliente: str, periodo: Periodo) -> bool:
		return bool(
			frappe.db.exists("Sales Invoice", {"customer": cliente, "co_periodo_honorarios": str(periodo)})
		)

	def _crear(self, cliente: str, periodo: Periodo, honorarios: list[Honorario]) -> str:
		factura = frappe.get_doc(
			{
				"doctype": "Sales Invoice",
				"company": self.empresa,
				"customer": cliente,
				# En la moneda de la empresa: si no, ERPNext toma la del sitio y la cuenta por cobrar no cuadra.
				"currency": frappe.get_cached_value("Company", self.empresa, "default_currency"),
				"posting_date": self.hoy,
				"set_posting_time": 1,
				"due_date": add_days(self.hoy, self.dias_para_pagar),
				"co_periodo_honorarios": str(periodo),
				"remarks": f"Honorarios de {periodo.nombre}",
				"taxes_and_charges": self.plantilla_impuestos,
				"items": [
					{
						"item_code": self.articulo,
						"qty": 1,
						"rate": h.valor,
						"price_list_rate": h.valor,
						"description": f"{h.concepto} - {periodo.nombre}",
					}
					for h in honorarios
				],
			}
		)
		if self.plantilla_impuestos:
			factura.append_taxes_from_master()
		factura.insert(ignore_permissions=True)
		return factura.name


def validar_cliente(doc, method=None):
	"""Hook de Customer: un honorario sin valor no se puede facturar."""
	from frappe import _

	for fila in doc.get("co_honorarios") or []:
		if not fila.valor or fila.valor <= 0:
			frappe.throw(_("El honorario {0} no tiene valor.").format(fila.concepto))
		if fila.hasta and getdate(fila.hasta) < getdate(fila.desde):
			frappe.throw(
				_("En el honorario {0}, la fecha hasta es anterior a la fecha desde.").format(fila.concepto)
			)
