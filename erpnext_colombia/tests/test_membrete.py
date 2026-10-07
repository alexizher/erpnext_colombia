import frappe
from frappe.tests import IntegrationTestCase

from erpnext_colombia.membrete import generar_membrete, nombre_membrete
from erpnext_colombia.tests.utils import empresa_prueba, nuevo_tercero


class TestMembrete(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.empresa = empresa_prueba()
		doc = frappe.get_doc("Company", cls.empresa)
		doc.co_tercero = nuevo_tercero("900123456", "Empresa Prueba CO S.A.S.")
		doc.co_representante_legal = "Ana Pérez"
		doc.co_representante_legal_documento = "CC 43123456"
		doc.co_contador = "Daniela Molina"
		doc.co_contador_tarjeta_profesional = "123456-T"
		doc.co_revisor_fiscal = ""
		doc.save()

	def test_al_guardar_la_empresa_se_crea_el_membrete(self):
		self.assertTrue(frappe.db.exists("Letter Head", nombre_membrete(self.empresa)))

	def test_encabezado_lleva_nombre_y_nit(self):
		lh = frappe.get_doc("Letter Head", nombre_membrete(self.empresa))
		self.assertIn("Empresa Prueba CO", lh.content)
		self.assertIn("900123456-8", lh.content)

	def test_pie_lleva_certificacion_y_firmas(self):
		lh = frappe.get_doc("Letter Head", nombre_membrete(self.empresa))
		self.assertIn("artículo 37 de la Ley 222 de 1995", lh.footer)
		self.assertIn("Ana Pérez", lh.footer)
		self.assertIn("T.P. 123456-T", lh.footer)
		self.assertNotIn("Revisor fiscal", lh.footer)

	def test_con_revisor_fiscal_aparece_su_firma(self):
		doc = frappe.get_doc("Company", self.empresa)
		doc.co_revisor_fiscal = "Luis Gómez"
		doc.co_revisor_fiscal_tarjeta_profesional = "654321-T"
		doc.save()
		try:
			lh = frappe.get_doc("Letter Head", nombre_membrete(self.empresa))
			self.assertIn("Revisor fiscal", lh.footer)
			self.assertIn("T.P. 654321-T", lh.footer)
		finally:
			doc.co_revisor_fiscal = ""
			doc.co_revisor_fiscal_tarjeta_profesional = ""
			doc.save()

	def test_generar_dos_veces_no_duplica(self):
		generar_membrete(self.empresa)
		generar_membrete(self.empresa)
		self.assertEqual(frappe.db.count("Letter Head", {"letter_head_name": nombre_membrete(self.empresa)}), 1)

	def test_nombres_con_html_se_escapan(self):
		doc = frappe.get_doc("Company", self.empresa)
		doc.co_contador = "<script>x</script>Daniela"
		doc.save()
		try:
			lh = frappe.get_doc("Letter Head", nombre_membrete(self.empresa))
			self.assertNotIn("<script>", lh.footer)
		finally:
			doc.co_contador = "Daniela Molina"
			doc.save()
