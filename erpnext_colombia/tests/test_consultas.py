import frappe
from frappe.tests import IntegrationTestCase

from erpnext_colombia.estados_financieros.consultas import resultado_del_periodo
from erpnext_colombia.tests.utils import empresa_prueba

PERIODOS = [{"from_date": "2026-01-01", "to_date": "2026-12-31"}]


class TestConsultas(IntegrationTestCase):
	def test_sin_empresa_se_rechaza(self):
		with self.assertRaisesRegex(frappe.ValidationError, "Falta la empresa"):
			resultado_del_periodo(frappe._dict(), PERIODOS)

	def test_usuario_sin_permiso_no_consulta(self):
		empresa = empresa_prueba()
		frappe.set_user("Guest")
		try:
			with self.assertRaises(frappe.PermissionError):
				resultado_del_periodo(frappe._dict(company=empresa), PERIODOS)
		finally:
			frappe.set_user("Administrator")
