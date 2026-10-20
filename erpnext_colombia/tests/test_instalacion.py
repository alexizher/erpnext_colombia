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

	def test_configurar_dos_veces_deja_una_dimension(self):
		from erpnext_colombia.instalacion import configurar

		configurar()
		configurar()
		self.assertEqual(frappe.db.count("Accounting Dimension", {"document_type": "Tercero"}), 1)
		self.assertTrue(frappe.get_meta("GL Entry").has_field("tercero"))
		self.assertTrue(frappe.get_meta("Journal Entry Account").has_field("tercero"))


class TestDianComoProveedor(IntegrationTestCase):
	"""Las retenciones (2365) y los pagos de impuestos se le deben a la DIAN: tiene que estar como proveedor."""

	def test_dian_es_tercero_y_proveedor(self):
		from erpnext_colombia.instalacion import configurar

		configurar()
		dian = frappe.get_doc("Tercero", "800197268")
		self.assertEqual(dian.nit_completo, "800197268-4")
		self.assertEqual(dian.naturaleza, "Persona jurídica")
		self.assertEqual(frappe.db.count("Supplier", {"co_tercero": "800197268"}), 1)

	def test_configurar_dos_veces_deja_un_proveedor_dian(self):
		from erpnext_colombia.instalacion import configurar

		configurar()
		configurar()
		self.assertEqual(frappe.db.count("Supplier", {"co_tercero": "800197268"}), 1)
