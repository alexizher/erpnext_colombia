import frappe
from erpnext.accounts.doctype.accounting_dimension_filter.accounting_dimension_filter import (
	get_dimension_filter_map,
)
from frappe.tests import IntegrationTestCase

from erpnext_colombia.cuentas import (
	aplicar_a_empresa,
	clasificacion_por_defecto,
	empresas_con_puc,
	exige_tercero,
)
from erpnext_colombia.tests.utils import asiento, cuenta, empresa_extranjera, empresa_prueba, nuevo_tercero


class TestCuentas(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.empresa = empresa_prueba()
		aplicar_a_empresa(cls.empresa)

	def test_clasificacion_por_prefijo(self):
		self.assertEqual(clasificacion_por_defecto("110505", "Asset"), "Corriente")
		self.assertEqual(clasificacion_por_defecto("151605", "Asset"), "No corriente")
		self.assertEqual(clasificacion_por_defecto("2705", "Liability"), "No corriente")
		self.assertEqual(clasificacion_por_defecto("413595", "Income"), None)
		self.assertEqual(clasificacion_por_defecto("310505", "Equity"), None)

	def test_cuenta_sin_numero_queda_corriente(self):
		self.assertEqual(clasificacion_por_defecto(None, "Asset"), "Corriente")
		self.assertEqual(clasificacion_por_defecto("", "Liability"), "Corriente")

	def test_prefijos_que_exigen_tercero(self):
		self.assertTrue(exige_tercero("130505"))
		self.assertTrue(exige_tercero("236540"))
		self.assertFalse(exige_tercero("110505"))
		self.assertFalse(exige_tercero(None))

	def test_cuentas_de_la_empresa_quedan_clasificadas(self):
		self.assertEqual(frappe.db.get_value("Account", cuenta("110505"), "co_clasificacion_niif"), "Corriente")
		self.assertEqual(frappe.db.get_value("Account", cuenta("151605"), "co_clasificacion_niif"), "No corriente")

	def test_filtro_exige_tercero_en_236540(self):
		mapa = get_dimension_filter_map()
		self.assertTrue(mapa[("tercero", cuenta("236540"))]["is_mandatory"])
		self.assertNotIn(("tercero", cuenta("110505")), mapa)

	# 2408 (IVA por pagar) es de tipo Tax: ERPNext no pide cliente ni proveedor ahí, así que lo único que
	# exige el tercero es el filtro de la app. Las 2365 son Payable y ERPNext ya exige el proveedor.
	def test_no_deja_contabilizar_iva_sin_tercero(self):
		from erpnext.exceptions import MandatoryAccountDimensionError

		with self.assertRaises(MandatoryAccountDimensionError):
			asiento(self.empresa, "2026-04-01", [{"cuenta": "519595", "debe": 1000}, {"cuenta": "2408", "haber": 1000}])

	def test_con_tercero_si_contabiliza(self):
		t = nuevo_tercero("800197268", "DIAN")
		je = asiento(self.empresa, "2026-04-02", [{"cuenta": "519595", "debe": 1000}, {"cuenta": "2408", "haber": 1000}], tercero=t)
		self.assertEqual(je.docstatus, 1)

	def test_cuenta_nueva_de_23_entra_al_filtro(self):
		padre = frappe.db.get_value("Account", {"company": self.empresa, "account_number": "2365"})
		nueva = frappe.get_doc(
			{
				"doctype": "Account",
				"company": self.empresa,
				"account_name": "Retención prueba",
				"account_number": "236599",
				"parent_account": padre,
			}
		).insert()
		nueva.reload()
		self.assertEqual(nueva.co_clasificacion_niif, "Corriente")
		self.assertTrue(get_dimension_filter_map()[("tercero", nueva.name)]["is_mandatory"])

	def test_aplicar_dos_veces_no_duplica_el_filtro(self):
		aplicar_a_empresa(self.empresa)
		aplicar_a_empresa(self.empresa)
		self.assertEqual(frappe.db.count("Accounting Dimension Filter", {"company": self.empresa}), 1)

	def test_empresa_sin_puc_se_salta(self):
		nombre = "Empresa Sin PUC"
		if not frappe.db.exists("Company", nombre):
			frappe.get_doc(
				{
					"doctype": "Company",
					"company_name": nombre,
					"abbr": "ESP",
					"default_currency": "COP",
					"country": "Colombia",
					"chart_of_accounts": "Standard",
					"create_chart_of_accounts_based_on": "Standard Template",
				}
			).insert()
		self.assertNotIn(nombre, empresas_con_puc())
		aplicar_a_empresa(nombre)
		self.assertFalse(frappe.db.exists("Accounting Dimension Filter", {"company": nombre}))

	def test_migrar_no_vuelve_a_meter_una_cuenta_quitada_del_filtro(self):
		nombre = frappe.db.get_value("Accounting Dimension Filter", {"company": self.empresa})
		filtro = frappe.get_doc("Accounting Dimension Filter", nombre)
		quitada = cuenta("236540")
		filtro.accounts = [f for f in filtro.accounts if f.applicable_on_account != quitada]
		filtro.save()
		aplicar_a_empresa(self.empresa)
		self.assertFalse(("tercero", quitada) in get_dimension_filter_map(), "la cuenta quitada volvió al filtro")

	def test_una_empresa_con_error_no_bloquea_la_migracion(self):
		from unittest.mock import patch

		from erpnext_colombia.instalacion import configurar

		with patch("erpnext_colombia.cuentas.aplicar_a_empresa", side_effect=Exception("dato malo")):
			configurar()
		self.assertTrue(frappe.db.exists("Error Log", {"error": ("like", "%dato malo%")}))

	def test_empresa_con_cuentas_del_puc_se_reconoce_aunque_no_diga_la_plantilla(self):
		# Empresa creada a partir de otra existente: chart_of_accounts queda vacío.
		frappe.db.set_value("Company", self.empresa, "chart_of_accounts", None)
		try:
			self.assertIn(self.empresa, empresas_con_puc())
		finally:
			frappe.db.set_value("Company", self.empresa, "chart_of_accounts", "Colombia PUC")

	def test_empresa_con_puc_de_otro_pais_se_salta(self):
		nombre = empresa_extranjera()
		self.assertNotIn(nombre, empresas_con_puc())
		aplicar_a_empresa(nombre)
		self.assertFalse(frappe.db.exists("Accounting Dimension Filter", {"company": nombre}))
		self.assertFalse(frappe.db.get_value("Account", cuenta("110505", nombre), "co_clasificacion_niif"))


class TestCuentasPorDefecto(IntegrationTestCase):
	EMPRESA = "Empresa Nueva CO"

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		if not frappe.db.exists("Company", cls.EMPRESA):
			frappe.get_doc(
				{
					"doctype": "Company",
					"company_name": cls.EMPRESA,
					"abbr": "ENC",
					"default_currency": "COP",
					"country": "Colombia",
					"chart_of_accounts": "Colombia PUC",
					"create_chart_of_accounts_based_on": "Standard Template",
				}
			).insert()

	def _numero(self, campo, empresa=None):
		cuenta_ = frappe.db.get_value("Company", empresa or self.EMPRESA, campo)
		return frappe.db.get_value("Account", cuenta_, "account_number")

	def test_empresa_nueva_con_puc_queda_con_las_cuentas_del_puc(self):
		self.assertEqual(self._numero("default_receivable_account"), "130505")
		self.assertEqual(self._numero("default_payable_account"), "2205")
		self.assertEqual(self._numero("stock_received_but_not_billed"), "233595")
		self.assertEqual(self._numero("round_off_account"), "429581")

	def test_ingresos_por_defecto_no_es_cultivo_de_cereales(self):
		# ERPNext toma la primera cuenta de ingresos del PUC, 410505.
		self.assertEqual(self._numero("default_income_account"), "415550")

	def test_empresa_nueva_con_puc_sin_inventario_perpetuo(self):
		self.assertFalse(frappe.db.get_value("Company", self.EMPRESA, "enable_perpetual_inventory"))

	def test_guardar_despues_no_pisa_un_cambio_a_mano(self):
		empresa = frappe.get_doc("Company", self.EMPRESA)
		empresa.default_receivable_account = cuenta("130510", self.EMPRESA)
		empresa.save()
		self.assertEqual(self._numero("default_receivable_account"), "130510")

	def test_empresa_de_otro_pais_no_se_toca(self):
		self.assertNotEqual(self._numero("default_receivable_account", empresa_extranjera()), "130505")
