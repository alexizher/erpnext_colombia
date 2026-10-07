import frappe
from frappe.tests import IntegrationTestCase


def nuevo_tercero(**campos):
	datos = {
		"doctype": "Tercero",
		"tipo_documento": "31 - NIT",
		"numero_documento": "800197268",
		"razon_social": "Dirección de Impuestos y Aduanas Nacionales",
	}
	datos.update(campos)
	return frappe.get_doc(datos)


class TestTercero(IntegrationTestCase):
	def test_nit_calcula_digito_y_nit_completo(self):
		t = nuevo_tercero(numero_documento="800.197.268").insert()
		self.assertEqual(t.name, "800197268")
		self.assertEqual(t.digito_verificacion, "4")
		self.assertEqual(t.nit_completo, "800197268-4")
		self.assertEqual(t.naturaleza, "Persona jurídica")
		self.assertEqual(t.nombre_completo, "Dirección de Impuestos y Aduanas Nacionales")

	def test_rechaza_digito_equivocado_y_dice_el_correcto(self):
		with self.assertRaisesRegex(frappe.ValidationError, "es 8, no 3"):
			nuevo_tercero(numero_documento="890903938", digito_verificacion="3").insert()

	def test_rechaza_dv_pegado_al_numero(self):
		# 8001972684 = NIT de la DIAN con su DV pegado al final
		with self.assertRaisesRegex(frappe.ValidationError, "dígito de verificación va en su propio campo"):
			nuevo_tercero(numero_documento="800197268-4").insert()

	def test_rechaza_numero_duplicado(self):
		nuevo_tercero(numero_documento="899999068", razon_social="Ecopetrol").insert()
		with self.assertRaises(frappe.DuplicateEntryError):
			nuevo_tercero(numero_documento="899.999.068", razon_social="Otra").insert()

	def test_persona_natural_arma_nombre_y_no_lleva_digito(self):
		t = nuevo_tercero(
			tipo_documento="13 - Cédula de ciudadanía",
			numero_documento="1.030.567.890",
			razon_social=None,
			primer_apellido="Molina",
			segundo_apellido="Rojas",
			primer_nombre="Daniela",
			otros_nombres="",
		).insert()
		self.assertEqual(t.naturaleza, "Persona natural")
		self.assertEqual(t.nombre_completo, "Daniela Molina Rojas")
		self.assertFalse(t.digito_verificacion)
		self.assertEqual(t.nit_completo, "1030567890")

	def test_persona_natural_exige_primer_apellido_y_nombre(self):
		with self.assertRaisesRegex(frappe.ValidationError, "primer apellido y el primer nombre"):
			nuevo_tercero(
				tipo_documento="13 - Cédula de ciudadanía",
				numero_documento="52123456",
				razon_social=None,
			).insert()

	def test_persona_juridica_exige_razon_social(self):
		with self.assertRaisesRegex(frappe.ValidationError, "razón social"):
			nuevo_tercero(numero_documento="860034313", razon_social=None).insert()

	def test_numero_vacio_se_rechaza(self):
		with self.assertRaisesRegex(frappe.ValidationError, "número de documento"):
			nuevo_tercero(numero_documento=" .- ").insert()
