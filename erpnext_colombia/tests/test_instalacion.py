import frappe
from frappe.tests import IntegrationTestCase


class TestInstalacion(IntegrationTestCase):
	def test_app_instalada_en_el_sitio(self):
		self.assertIn("erpnext_colombia", frappe.get_installed_apps())

	def test_modulo_registrado(self):
		self.assertTrue(frappe.db.exists("Module Def", "ERPNext Colombia"))

	def test_configurar_dos_veces_no_duplica_campos(self):
		from erpnext_colombia.instalacion import configurar

		configurar()
		configurar()
		for doctype in ("Customer", "Supplier", "Company"):
			n = frappe.db.count("Custom Field", {"dt": doctype, "fieldname": "co_tercero"})
			self.assertEqual(n, 1, doctype)
