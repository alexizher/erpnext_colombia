import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from erpnext_colombia.tests.utils import cliente
from erpnext_colombia.vencimientos.reglas import digitos, segmento


class TestReglas(IntegrationTestCase):
	def test_digitos_de_nit_y_cedula(self):
		self.assertEqual(digitos("900123456", 1), 6)
		self.assertEqual(digitos("900123456", 2), 56)
		self.assertEqual(digitos("1.030.567.890", 2), 90)
		self.assertEqual(digitos("43123405", 2), 5)

	def test_documento_sin_digitos(self):
		self.assertIsNone(digitos("AB-CD", 1))
		self.assertIsNone(digitos(None, 2))

	def test_segmento(self):
		self.assertEqual(segmento(True, "Persona natural"), "Gran contribuyente")
		self.assertEqual(segmento(False, "Persona jurídica"), "Persona jurídica")
		self.assertEqual(segmento(False, "Persona natural"), "Persona natural")
		self.assertIsNone(segmento(False, None))

	def test_cliente_guarda_obligaciones_con_desde_por_defecto(self):
		c = frappe.get_doc("Customer", cliente("900111222", "Ficha Uno S.A.S."))
		c.append("co_obligaciones", {"obligacion": "Retención en la fuente"})
		c.co_gran_contribuyente = 0
		c.save()
		c.reload()
		self.assertEqual(c.co_obligaciones[0].obligacion, "Retención en la fuente")
		self.assertEqual(str(c.co_obligaciones[0].desde), today())

	def test_hasta_antes_de_desde_no_se_guarda(self):
		c = frappe.get_doc("Customer", cliente("900111223", "Ficha Dos S.A.S."))
		c.append(
			"co_obligaciones", {"obligacion": "IVA bimestral", "desde": "2026-05-01", "hasta": "2026-04-30"}
		)
		with self.assertRaisesRegex(frappe.ValidationError, "hasta"):
			c.save()

	def test_misma_obligacion_dos_veces_no_se_guarda(self):
		c = frappe.get_doc("Customer", cliente("900111224", "Ficha Tres S.A.S."))
		c.append("co_obligaciones", {"obligacion": "IVA bimestral"})
		c.append("co_obligaciones", {"obligacion": "IVA bimestral"})
		with self.assertRaisesRegex(frappe.ValidationError, "IVA bimestral"):
			c.save()
