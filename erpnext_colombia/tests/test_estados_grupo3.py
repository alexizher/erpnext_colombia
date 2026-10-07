import frappe
from frappe.tests import IntegrationTestCase

from erpnext_colombia.estados_financieros import sincronizar_plantillas
from erpnext_colombia.tests.estados import cargar_movimientos, ejecutar, valores
from erpnext_colombia.tests.utils import asiento, empresa_prueba, nuevo_tercero

ESF = "CO Grupo 3 - Situación financiera"
ER = "CO Grupo 3 - Resultados"


class TestEstadosGrupo3(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.empresa = empresa_prueba()
		sincronizar_plantillas()
		cargar_movimientos(cls.empresa)

	def test_situacion_financiera_cuadra(self):
		filas = ejecutar(ESF, self.empresa)
		self.assertEqual(valores(filas, "Total activo"), [18_100_000, 19_550_000])
		self.assertEqual(valores(filas, "Total pasivo y patrimonio"), [18_100_000, 19_550_000])
		self.assertEqual(valores(filas, "Efectivo y equivalentes al efectivo"), [8_600_000, 10_550_000])
		# El resultado del ejercicio es el del año, como en el estado de resultados; lo de años
		# anteriores sin cerrar va en resultados acumulados.
		self.assertEqual(valores(filas, "Resultado del ejercicio"), [1_100_000, 2_450_000])
		self.assertEqual(valores(filas, "Resultados acumulados"), [0, 1_100_000])

	def test_resultados(self):
		filas = ejecutar(ER, self.empresa)
		self.assertEqual(valores(filas, "Ingresos"), [3_000_000, 2_500_000])
		self.assertEqual(valores(filas, "Costos"), [1_200_000, 0])
		self.assertEqual(valores(filas, "Gastos"), [700_000, 50_000])
		self.assertEqual(valores(filas, "Utilidad (pérdida) del periodo"), [1_100_000, 2_450_000])

	def test_sincronizar_dos_veces_no_duplica_filas(self):
		sincronizar_plantillas()
		n = len(frappe.get_doc("Financial Report Template", ESF).rows)
		sincronizar_plantillas()
		self.assertEqual(len(frappe.get_doc("Financial Report Template", ESF).rows), n)

	def test_cuenta_de_resultado_sin_numero_entra_en_la_utilidad(self):
		padre = frappe.db.get_value("Account", {"company": self.empresa, "account_number": "42"})
		suelta = frappe.get_doc(
			{"doctype": "Account", "company": self.empresa, "account_name": "Ingreso sin número", "parent_account": padre}
		).insert()
		je = asiento(self.empresa, "2026-06-02", [{"cuenta": "111005", "debe": 50_000}], tercero=nuevo_tercero("800197268", "DIAN"), enviar=False)
		je.append(
			"accounts",
			{
				"account": suelta.name,
				"credit_in_account_currency": 50_000,
				"cost_center": frappe.get_cached_value("Company", self.empresa, "cost_center"),
			},
		)
		je.save()
		je.submit()
		try:
			self.assertEqual(valores(ejecutar(ER, self.empresa), "Utilidad (pérdida) del periodo")[1], 2_500_000)
		finally:
			je.cancel()
