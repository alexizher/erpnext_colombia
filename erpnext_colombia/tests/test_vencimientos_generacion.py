from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from erpnext_colombia.tests.utils import cliente_con, fecha_prueba, obligacion_prueba, vencimientos_de
from erpnext_colombia.vencimientos import generacion
from erpnext_colombia.vencimientos.generacion import generar


def preparar_fechas():
	fecha_prueba("Enero de 2030", "2030-02-10", desde=0, hasta=4)
	fecha_prueba("Enero de 2030", "2030-02-11", desde=5, hasta=9)
	fecha_prueba("Febrero de 2030", "2030-03-10", desde=0, hasta=4)
	fecha_prueba("Febrero de 2030", "2030-03-11", desde=5, hasta=9)


def obligacion(desde="2030-01-01", hasta=None):
	return [{"obligacion": obligacion_prueba(), "desde": desde, "hasta": hasta}]


class TestGeneracion(IntegrationTestCase):
	def setUp(self):
		preparar_fechas()

	def test_crea_un_vencimiento_por_periodo_segun_el_digito(self):
		c = cliente_con("900200301", "Gen Uno S.A.S.", obligacion())
		self.assertEqual(generar(cliente=c, anio=2030), [])
		v = vencimientos_de(c)
		self.assertEqual([x.periodo for x in v], ["Enero de 2030", "Febrero de 2030"])
		self.assertEqual(str(v[0].fecha_vencimiento), "2030-02-10")
		self.assertEqual(v[0].estado, "Pendiente")

	def test_generar_dos_veces_no_duplica(self):
		c = cliente_con("900200302", "Gen Dos S.A.S.", obligacion())
		generar(cliente=c, anio=2030)
		generar(cliente=c, anio=2030)
		self.assertEqual(len(vencimientos_de(c)), 2)

	def test_no_crea_antes_de_desde(self):
		c = cliente_con("900200303", "Gen Tres S.A.S.", obligacion(desde="2030-03-01"))
		generar(cliente=c, anio=2030)
		self.assertEqual([x.periodo for x in vencimientos_de(c)], ["Febrero de 2030"])

	def test_no_crea_despues_de_hasta(self):
		c = cliente_con("900200304", "Gen Cuatro S.A.S.", obligacion(hasta="2030-02-28"))
		generar(cliente=c, anio=2030)
		self.assertEqual([x.periodo for x in vencimientos_de(c)], ["Enero de 2030"])

	def test_dos_filas_que_cubren_el_mismo_digito_no_duplican(self):
		fecha_prueba("Enero de 2030", "2030-02-15", segmento="Persona jurídica", desde=0, hasta=9)
		c = cliente_con("900200305", "Gen Cinco S.A.S.", obligacion())
		generar(cliente=c, anio=2030)
		self.assertEqual(len(vencimientos_de(c, periodo="Enero de 2030")), 1)

	def test_documento_sin_digitos_es_problema(self):
		c = cliente_con("PASAPORTEX", "Viajero", obligacion(), tipo="41 - Pasaporte")
		bueno = cliente_con("900200306", "Gen Seis S.A.S.", obligacion())
		problemas = generar(anio=2030)
		self.assertTrue(any("Viajero" in p and "dígitos" in p for p in problemas), problemas)
		self.assertEqual(vencimientos_de(c), [])
		self.assertEqual(len(vencimientos_de(bueno)), 2)

	def test_anio_sin_fechas_es_problema(self):
		c = cliente_con("900200307", "Gen Siete S.A.S.", obligacion(desde="2029-01-01"))
		problemas = generar(cliente=c, anio=2029)
		self.assertTrue(any("Gen Siete" in p and "2029" in p for p in problemas), problemas)

	def test_error_en_un_cliente_no_detiene_a_los_demas(self):
		a = cliente_con("900200308", "Gen Ocho S.A.S.", obligacion())
		b = cliente_con("900200309", "Gen Nueve S.A.S.", obligacion())
		original = generacion.generar_cliente

		def falla_con_a(cliente, anios):
			if cliente == a:
				raise RuntimeError("dato malo")
			return original(cliente, anios)

		with patch("erpnext_colombia.vencimientos.generacion.generar_cliente", side_effect=falla_con_a):
			problemas = generar(anio=2030)
		self.assertTrue(any("Gen Ocho" in p for p in problemas), problemas)
		self.assertEqual(len(vencimientos_de(b)), 2)

	def test_vencimiento_duplicado_a_mano_no_se_guarda(self):
		c = cliente_con("900200310", "Gen Diez S.A.S.", obligacion())
		generar(cliente=c, anio=2030)
		original = frappe.get_doc("Vencimiento", vencimientos_de(c)[0].name)
		copia = frappe.copy_doc(original)
		with self.assertRaisesRegex(frappe.ValidationError, original.name):
			copia.insert()

	def test_base_de_datos_impide_duplicado_aunque_no_pase_por_validate(self):
		# La tarea nocturna y un guardado pueden validar a la vez: la validación sola no basta.
		c = cliente_con("900200311", "Gen Once S.A.S.", obligacion())
		generar(cliente=c, anio=2030)
		copia = frappe.copy_doc(frappe.get_doc("Vencimiento", vencimientos_de(c)[0].name))
		copia.set_new_name()
		with self.assertRaises((frappe.UniqueValidationError, frappe.DuplicateEntryError)):
			copia.db_insert()

	def test_crear_un_vencimiento_que_ya_existe_no_falla(self):
		c = cliente_con("900200312", "Gen Doce S.A.S.", obligacion())
		generar(cliente=c, anio=2030)
		v = vencimientos_de(c)[0]
		f = frappe.get_doc("Fecha Tributaria", frappe.db.get_value("Vencimiento", v.name, "fecha_tributaria"))
		generacion._crear(c, f)
		self.assertEqual(len(vencimientos_de(c)), 2)

	def test_guardar_cliente_con_problema_avisa_en_pantalla(self):
		c = cliente_con("900200313", "Gen Trece S.A.S.", obligacion())
		frappe.clear_messages()
		with patch(
			"erpnext_colombia.vencimientos.generacion.generar_cliente", side_effect=RuntimeError("dato malo")
		):
			generacion.al_guardar_cliente(frappe.get_doc("Customer", c))
		self.assertIn("Gen Trece", " ".join(m.get("message", "") for m in frappe.get_message_log()))
