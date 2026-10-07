import frappe
from frappe.tests import IntegrationTestCase


class TestInstalacion(IntegrationTestCase):
	def test_app_instalada_en_el_sitio(self):
		self.assertIn("erpnext_colombia", frappe.get_installed_apps())

	def test_modulo_registrado(self):
		self.assertTrue(frappe.db.exists("Module Def", "ERPNext Colombia"))
