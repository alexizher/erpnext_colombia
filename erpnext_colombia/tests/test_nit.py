from frappe.tests import UnitTestCase

from erpnext_colombia.nit import codigo_tipo, digito_verificacion, limpiar_numero


class TestNit(UnitTestCase):
	def test_digito_de_nit_publicos(self):
		# DIAN, Bancolombia, Ecopetrol, Davivienda
		for numero, esperado in [
			("800197268", 4),
			("890903938", 8),
			("899999068", 1),
			("860034313", 7),
		]:
			self.assertEqual(digito_verificacion(numero), esperado, numero)

	def test_limpia_puntos_guiones_y_espacios(self):
		self.assertEqual(limpiar_numero(" 900.123-456 ", "31 - NIT"), "900123456")

	def test_pasaporte_conserva_letras_en_mayuscula(self):
		self.assertEqual(limpiar_numero("ab-12.345", "41 - Pasaporte"), "AB12345")

	def test_codigo_tipo(self):
		self.assertEqual(codigo_tipo("31 - NIT"), "31")
		self.assertEqual(codigo_tipo(""), "")
