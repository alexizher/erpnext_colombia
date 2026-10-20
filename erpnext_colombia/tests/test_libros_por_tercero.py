import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from erpnext_colombia.tests.utils import asiento, cuenta, empresa_prueba, nuevo_tercero

MARCA = "datos-libros-tercero"
UNO = "901777001"
DOS = "901777002"


def cargar_movimientos(empresa):
	if frappe.db.exists("Journal Entry", {"company": empresa, "user_remark": MARCA, "docstatus": 1}):
		return
	nuevo_tercero(UNO, "Libros Uno S.A.S.")
	nuevo_tercero(DOS, "Libros Dos S.A.S.")
	for fecha, lineas in (
		("2026-01-15", [("111005", 1_000_000, 0, UNO), ("413595", 0, 1_000_000, UNO)]),
		("2026-03-10", [("111005", 200_000, 0, UNO), ("413595", 0, 200_000, UNO)]),
		("2026-03-20", [("519595", 50_000, 0, DOS), ("111005", 0, 50_000, DOS)]),
	):
		je = asiento(
			empresa,
			fecha,
			[{"cuenta": c, "debe": d, "haber": h, "tercero": t} for c, d, h, t in lineas],
			enviar=False,
		)
		je.user_remark = MARCA
		je.save()
		je.submit()


def filtros(empresa, **otros):
	return frappe._dict({"company": empresa, "from_date": "2026-02-01", "to_date": "2026-03-31", **otros})


class TestBalancePorTercero(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.empresa = empresa_prueba()
		cargar_movimientos(cls.empresa)

	def ejecutar(self, **otros):
		from erpnext_colombia.erpnext_colombia.report.balance_de_prueba_por_tercero.balance_de_prueba_por_tercero import (
			execute,
		)

		_columnas, filas = execute(filtros(self.empresa, **otros))
		return {(f["account"], f["tercero"]): f for f in filas if f.get("tercero")}

	def test_saldo_inicial_movimientos_y_final(self):
		filas = self.ejecutar(tercero=UNO)
		caja = filas[(cuenta("111005"), UNO)]
		self.assertEqual(
			[flt(caja[k]) for k in ("inicial", "debito", "credito", "final")],
			[1_000_000, 200_000, 0, 1_200_000],
		)
		ingreso = filas[(cuenta("413595"), UNO)]
		self.assertEqual(flt(ingreso["final"]), -1_200_000)
		self.assertEqual(set(filas), {(cuenta("111005"), UNO), (cuenta("413595"), UNO)})

	def test_cuenta_de_grupo_trae_sus_hijas(self):
		grupo = frappe.db.get_value("Account", {"company": self.empresa, "account_number": "11"})
		filas = self.ejecutar(tercero=DOS, account=grupo)
		self.assertEqual(set(filas), {(cuenta("111005"), DOS)})
		self.assertEqual(flt(filas[(cuenta("111005"), DOS)]["credito"]), 50_000)

	def test_trae_el_nombre_y_el_nit_del_tercero(self):
		fila = self.ejecutar(tercero=UNO)[(cuenta("111005"), UNO)]
		self.assertEqual(fila["tercero_nombre"], "Libros Uno S.A.S.")
		self.assertTrue(fila["nit"].startswith(UNO + "-"))


class TestAuxiliarPorTercero(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.empresa = empresa_prueba()
		cargar_movimientos(cls.empresa)

	def ejecutar(self, **otros):
		from erpnext_colombia.erpnext_colombia.report.auxiliar_por_tercero.auxiliar_por_tercero import execute

		_columnas, filas = execute(filtros(self.empresa, **otros))
		return filas

	def test_saldo_inicial_y_saldo_corrido(self):
		filas = self.ejecutar(tercero=UNO, account=cuenta("111005"))
		self.assertEqual(
			[(f.get("voucher_type"), flt(f["debito"]), flt(f["credito"]), flt(f["saldo"])) for f in filas],
			[(None, 0, 0, 1_000_000), ("Journal Entry", 200_000, 0, 1_200_000)],
		)
		self.assertEqual(str(filas[1]["posting_date"]), "2026-03-10")

	def test_un_bloque_por_cuenta_y_tercero(self):
		filas = self.ejecutar(tercero=UNO)
		iniciales = [(f["account"], flt(f["saldo"])) for f in filas if f.get("es_inicial")]
		self.assertEqual(iniciales, [(cuenta("111005"), 1_000_000), (cuenta("413595"), -1_000_000)])

	def test_sin_saldo_inicial_empieza_en_cero(self):
		filas = self.ejecutar(tercero=DOS, account=cuenta("111005"))
		self.assertEqual(flt(filas[0]["saldo"]), 0)
		self.assertEqual(flt(filas[-1]["saldo"]), -50_000)
