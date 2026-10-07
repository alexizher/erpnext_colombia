import frappe
from frappe.tests import IntegrationTestCase


def tercero(numero, razon):
	if frappe.db.exists("Tercero", numero):
		return frappe.get_doc("Tercero", numero)
	return frappe.get_doc(
		{"doctype": "Tercero", "tipo_documento": "31 - NIT", "numero_documento": numero, "razon_social": razon}
	).insert()


def nuevo_cliente(t, **campos):
	datos = {
		"doctype": "Customer",
		"co_tercero": t,
		"customer_group": "Commercial",
		"territory": "Colombia",
	}
	datos.update(campos)
	return frappe.get_doc(datos)


class TestPartes(IntegrationTestCase):
	def test_cliente_copia_nombre_nit_y_tipo_del_tercero(self):
		t = tercero("890903938", "Bancolombia S.A.")
		c = nuevo_cliente(t.name).insert()
		self.assertEqual(c.customer_name, "Bancolombia S.A.")
		self.assertEqual(c.tax_id, "890903938-8")
		self.assertEqual(c.customer_type, "Company")

	def test_proveedor_con_el_mismo_tercero_que_un_cliente(self):
		t = tercero("860034313", "Banco Davivienda S.A.")
		nuevo_cliente(t.name).insert()
		s = frappe.get_doc({"doctype": "Supplier", "co_tercero": t.name, "supplier_group": "Local"}).insert()
		self.assertEqual(s.tax_id, "860034313-7")
		self.assertEqual(s.supplier_type, "Company")

	def test_no_deja_dos_clientes_con_el_mismo_tercero(self):
		t = tercero("899999068", "Ecopetrol S.A.")
		primero = nuevo_cliente(t.name).insert()
		with self.assertRaisesRegex(frappe.ValidationError, primero.name):
			nuevo_cliente(t.name, customer_name="Ecopetrol duplicado").insert()

	def test_cliente_sin_tercero_no_se_guarda(self):
		with self.assertRaises(frappe.MandatoryError):
			nuevo_cliente(None, customer_name="Sin NIT").insert()

	def test_persona_natural_queda_individual(self):
		t = frappe.get_doc(
			{
				"doctype": "Tercero",
				"tipo_documento": "13 - Cédula de ciudadanía",
				"numero_documento": "43123456",
				"primer_apellido": "Pérez",
				"primer_nombre": "Ana",
			}
		).insert()
		c = nuevo_cliente(t.name).insert()
		self.assertEqual(c.customer_type, "Individual")
		self.assertEqual(c.tax_id, "43123456")
