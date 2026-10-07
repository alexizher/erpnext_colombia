import frappe
from frappe.tests import IntegrationTestCase

from erpnext_colombia.estados_financieros import sincronizar_plantillas
from erpnext_colombia.tests.estados import cargar_movimientos, ejecutar, valores
from erpnext_colombia.tests.utils import asiento, empresa_prueba, nuevo_tercero

ESF2 = "CO Grupo 2 - Situación financiera"
ERI2 = "CO Grupo 2 - Resultado integral"
EFE2 = "CO Grupo 2 - Flujos de efectivo"
ECP2 = "CO Grupo 2 - Cambios en el patrimonio"
ESF3 = "CO Grupo 3 - Situación financiera"
ER3 = "CO Grupo 3 - Resultados"


class TestEstadosGrupo2(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.empresa = empresa_prueba()
		sincronizar_plantillas()
		cargar_movimientos(cls.empresa)

	def test_activo_igual_pasivo_mas_patrimonio(self):
		filas = ejecutar(ESF2, self.empresa)
		self.assertEqual(valores(filas, "Total activo"), valores(filas, "Total pasivo y patrimonio"))
		self.assertEqual(valores(filas, "Total activo"), [18_100_000, 19_550_000])

	def test_corriente_mas_no_corriente_da_el_total(self):
		filas = ejecutar(ESF2, self.empresa)
		ac, anc, atot = (valores(filas, t) for t in ("Total activo corriente", "Total activo no corriente", "Total activo"))
		self.assertEqual([a + b for a, b in zip(ac, anc)], atot)
		self.assertEqual(anc, [5_700_000, 5_700_000])

	def test_prestamo_reclasificado_a_no_corriente(self):
		filas = ejecutar(ESF2, self.empresa)
		antes = valores(filas, "Obligaciones financieras de largo plazo")
		cuenta = frappe.db.get_value("Account", {"company": self.empresa, "account_number": "210505"})
		frappe.db.set_value("Account", cuenta, "co_clasificacion_niif", "No corriente")
		try:
			despues = valores(ejecutar(ESF2, self.empresa), "Obligaciones financieras de largo plazo")
		finally:
			frappe.db.set_value("Account", cuenta, "co_clasificacion_niif", "Corriente")
		self.assertEqual([d - a for a, d in zip(antes, despues)], [5_000_000, 5_000_000])

	def test_utilidad_coincide_entre_resultado_integral_y_grupo3(self):
		utilidad2 = valores(ejecutar(ERI2, self.empresa), "Resultado del periodo")
		utilidad3 = valores(ejecutar(ER3, self.empresa), "Utilidad (pérdida) del periodo")
		self.assertEqual(utilidad2, utilidad3)
		self.assertEqual(utilidad2, [1_100_000, 2_450_000])

	def test_grupo2_y_grupo3_dan_los_mismos_totales(self):
		f2, f3 = ejecutar(ESF2, self.empresa), ejecutar(ESF3, self.empresa)
		self.assertEqual(valores(f2, "Total activo"), valores(f3, "Total activo"))
		self.assertEqual(valores(f2, "Total patrimonio"), valores(f3, "Total patrimonio"))

	def test_flujo_de_efectivo_cuadra_con_la_variacion_de_11(self):
		filas = ejecutar(EFE2, self.empresa)
		# variación de la caja: 2025 parte de 0 y cierra en 8.600.000; 2026 sube 1.950.000
		self.assertEqual(valores(filas, "Aumento (disminución) neto del efectivo"), [8_600_000, 1_950_000])
		self.assertEqual(valores(filas, "Efectivo al final del periodo"), [8_600_000, 10_550_000])

	def test_cambios_en_el_patrimonio_cuadra_con_el_balance(self):
		ecp = ejecutar(ECP2, self.empresa)
		esf = ejecutar(ESF2, self.empresa)
		self.assertEqual(valores(ecp, "Total patrimonio al final"), valores(esf, "Total patrimonio"))
		self.assertEqual(valores(ecp, "Capital - saldo final"), [10_000_000, 10_000_000])

	def test_cuenta_sin_numero_aparece_en_otros(self):
		padre = frappe.db.get_value("Account", {"company": self.empresa, "account_number": "11"})
		suelta = frappe.get_doc(
			{"doctype": "Account", "company": self.empresa, "account_name": "Caja sin número", "parent_account": padre}
		).insert()
		t = nuevo_tercero("800197268", "DIAN")
		je = asiento(
			self.empresa,
			"2026-06-01",
			[{"cuenta": "111005", "haber": 100_000}],
			tercero=t,
			enviar=False,
		)
		je.append(
			"accounts",
			{
				"account": suelta.name,
				"debit_in_account_currency": 100_000,
				"cost_center": frappe.get_cached_value("Company", self.empresa, "cost_center"),
			},
		)
		je.save()
		je.submit()
		try:
			filas = ejecutar(ESF2, self.empresa)
			self.assertEqual(valores(filas, "Total activo")[1], 19_550_000)
			self.assertEqual(valores(filas, "Otros activos corrientes")[1], 100_000)
		finally:
			je.cancel()

	def test_cuenta_sin_clasificacion_cuenta_como_corriente(self):
		caja = frappe.db.get_value("Account", {"company": self.empresa, "account_number": "111005"})
		frappe.db.set_value("Account", caja, "co_clasificacion_niif", None)
		try:
			filas = ejecutar(ESF2, self.empresa)
			self.assertEqual(valores(filas, "Total activo"), [18_100_000, 19_550_000])
		finally:
			frappe.db.set_value("Account", caja, "co_clasificacion_niif", "Corriente")
