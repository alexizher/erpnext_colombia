import frappe
from frappe.tests import IntegrationTestCase

from erpnext_colombia.nit import digito_verificacion

# Números que solo usa este módulo. Renombrar hace commit, así que se limpian antes de cada prueba.
NUMEROS = [
	"901000111", "901000222", "901000333", "901000444", "901000555", "901000560", "901000561",
	"901000571", "901000581", "901000591", "901000601", "901000611", "1030567897", "1030567811",
]


def nuevo_tercero(**campos):
	datos = {
		"doctype": "Tercero",
		"tipo_documento": "31 - NIT",
		"numero_documento": "901000111",
		"razon_social": "Uno S.A.S.",
	}
	datos.update(campos)
	return frappe.get_doc(datos)


class TestTercero(IntegrationTestCase):
	def setUp(self):
		for numero in NUMEROS:
			for cliente in frappe.get_all("Customer", filters={"co_tercero": numero}, pluck="name"):
				frappe.delete_doc("Customer", cliente, force=True, ignore_permissions=True)
			if frappe.db.exists("Tercero", numero):
				frappe.delete_doc("Tercero", numero, force=True, ignore_permissions=True)

	def test_nit_calcula_digito_y_nit_completo(self):
		t = nuevo_tercero(numero_documento="901.000.111").insert()
		self.assertEqual(t.name, "901000111")
		self.assertEqual(t.digito_verificacion, "8")
		self.assertEqual(t.nit_completo, "901000111-8")
		self.assertEqual(t.naturaleza, "Persona jurídica")
		self.assertEqual(t.nombre_completo, "Uno S.A.S.")

	def test_rechaza_digito_equivocado_y_dice_el_correcto(self):
		with self.assertRaisesRegex(frappe.ValidationError, "es 7, no 3"):
			nuevo_tercero(numero_documento="901000222", digito_verificacion="3").insert()

	def test_dv_escrito_con_guion_se_separa_del_numero(self):
		t = nuevo_tercero(numero_documento="901.000.333-6").insert()
		self.assertEqual(t.name, "901000333")
		self.assertEqual(t.digito_verificacion, "6")

	def test_dv_con_guion_equivocado_se_rechaza(self):
		with self.assertRaisesRegex(frappe.ValidationError, "es 5, no 3"):
			nuevo_tercero(numero_documento="901000444-3").insert()

	def test_cedula_de_10_digitos_como_nit_se_acepta(self):
		# Su último dígito coincide con el DV de los nueve primeros, y aun así es un número válido.
		t = nuevo_tercero(
			numero_documento="1030567897",
			razon_social=None,
			naturaleza="Persona natural",
			primer_apellido="Molina",
			primer_nombre="Daniela",
		).insert()
		self.assertEqual(t.name, "1030567897")

	def test_nombre_escrito_en_la_entrada_rapida_no_reemplaza_al_numero(self):
		t = nuevo_tercero(numero_documento="901000555", razon_social="Cinco")
		t.set("__newname", "Cinco")
		t.insert()
		self.assertEqual(t.name, "901000555")

	def test_numero_es_unico_aunque_se_fuerce_otro_nombre(self):
		nuevo_tercero(numero_documento="901000560", razon_social="Seis").insert()
		otro = nuevo_tercero(numero_documento="901000560", razon_social="Otra")
		otro.set("__newname", "otro-nombre")
		with self.assertRaises(frappe.DuplicateEntryError):
			otro.insert()

	def test_renombrar_limpia_el_numero(self):
		t = nuevo_tercero(numero_documento="901000561", razon_social="Error S.A.S.").insert()
		nuevo = frappe.rename_doc("Tercero", t.name, "901.000.571", force=True)
		self.assertEqual(nuevo, "901000571")
		self.assertEqual(
			frappe.db.get_value("Tercero", "901000571", "nit_completo"), f"901000571-{digito_verificacion('901000571')}"
		)

	def test_renombrar_actualiza_el_nit_del_cliente(self):
		t = nuevo_tercero(numero_documento="901000581", razon_social="Error Dos S.A.S.").insert()
		c = frappe.get_doc(
			{"doctype": "Customer", "co_tercero": t.name, "customer_group": "Commercial", "territory": "Colombia"}
		).insert()
		frappe.rename_doc("Tercero", t.name, "901000591", force=True)
		self.assertEqual(frappe.db.get_value("Customer", c.name, "tax_id"), f"901000591-{digito_verificacion('901000591')}")

	def test_rechaza_numero_duplicado(self):
		nuevo_tercero(numero_documento="901000601", razon_social="Seis Cero").insert()
		with self.assertRaises(frappe.DuplicateEntryError):
			nuevo_tercero(numero_documento="901.000.601", razon_social="Otra").insert()

	def test_persona_natural_arma_nombre_y_no_lleva_digito(self):
		t = nuevo_tercero(
			tipo_documento="13 - Cédula de ciudadanía",
			numero_documento="1.030.567.811",
			razon_social=None,
			primer_apellido="Molina",
			segundo_apellido="Rojas",
			primer_nombre="Daniela",
			otros_nombres="",
		).insert()
		self.assertEqual(t.naturaleza, "Persona natural")
		self.assertEqual(t.nombre_completo, "Daniela Molina Rojas")
		self.assertFalse(t.digito_verificacion)
		self.assertEqual(t.nit_completo, "1030567811")

	def test_persona_natural_exige_primer_apellido_y_nombre(self):
		with self.assertRaisesRegex(frappe.ValidationError, "primer apellido y el primer nombre"):
			nuevo_tercero(
				tipo_documento="13 - Cédula de ciudadanía",
				numero_documento="52123456",
				razon_social=None,
			).insert()

	def test_persona_juridica_exige_razon_social(self):
		with self.assertRaisesRegex(frappe.ValidationError, "razón social"):
			nuevo_tercero(numero_documento="901000611", razon_social=None).insert()

	def test_numero_vacio_se_rechaza(self):
		with self.assertRaisesRegex(frappe.ValidationError, "número de documento"):
			nuevo_tercero(numero_documento=" .- ").insert()
