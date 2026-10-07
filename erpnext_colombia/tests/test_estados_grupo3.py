import frappe
from frappe.tests import IntegrationTestCase

from erpnext_colombia.estados_financieros import sincronizar_plantillas
from erpnext_colombia.tests.estados import cargar_movimientos, ejecutar, valores
from erpnext_colombia.tests.utils import empresa_prueba

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
		self.assertEqual(valores(filas, "Resultado del ejercicio"), [1_100_000, 3_550_000])

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
