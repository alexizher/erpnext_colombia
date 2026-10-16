import json
import tempfile
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

from erpnext_colombia.vencimientos import catalogo, fechas


class TestCatalogo(IntegrationTestCase):
	def test_obligaciones_del_catalogo_existen(self):
		for o in catalogo.OBLIGACIONES:
			self.assertTrue(frappe.db.exists("Obligacion Tributaria", o["nombre"]), o["nombre"])
		self.assertEqual(frappe.db.get_value("Obligacion Tributaria", "IVA bimestral", "formulario"), "300")

	def test_sincronizar_obligaciones_es_idempotente(self):
		antes = frappe.db.count("Obligacion Tributaria")
		catalogo.sincronizar_obligaciones()
		catalogo.sincronizar_obligaciones()
		self.assertEqual(frappe.db.count("Obligacion Tributaria"), antes)

	def test_fecha_se_nombra_por_su_clave(self):
		f = fecha("Retención en la fuente", 2031, "Enero de 2031", "Todos", "1", 3, 4, "2031-02-12").insert()
		self.assertEqual(f.name, "Retención en la fuente 2031 Enero de 2031 Todos 03")

	def test_rango_de_digitos_invalido(self):
		with self.assertRaisesRegex(frappe.ValidationError, "dígito"):
			fecha(
				"Retención en la fuente", 2031, "Febrero de 2031", "Todos", "1", 5, 12, "2031-03-12"
			).insert()
		with self.assertRaisesRegex(frappe.ValidationError, "dígito"):
			fecha("Retención en la fuente", 2031, "Marzo de 2031", "Todos", "1", 6, 5, "2031-04-12").insert()

	def test_editar_desde_la_interfaz_marca_corregida_a_mano(self):
		f = fecha("Retención en la fuente", 2031, "Abril de 2031", "Todos", "1", 0, 0, "2031-05-12").insert()
		self.assertFalse(f.corregida_a_mano)
		f.fecha = "2031-05-13"
		f.save()
		self.assertTrue(f.corregida_a_mano)

	def test_sincronizar_no_pisa_lo_corregido_a_mano(self):
		fechas.sincronizar_fechas(carpeta_con([fila("Mayo de 2031", "2031-06-10")]))
		nombre = fechas.clave_fecha(fila("Mayo de 2031", "2031-06-10"))
		self.assertFalse(frappe.db.get_value("Fecha Tributaria", nombre, "corregida_a_mano"))
		f = frappe.get_doc("Fecha Tributaria", nombre)
		f.fecha = "2031-06-11"
		f.save()
		fechas.sincronizar_fechas(carpeta_con([fila("Mayo de 2031", "2031-06-09")]))
		self.assertEqual(str(frappe.db.get_value("Fecha Tributaria", nombre, "fecha")), "2031-06-11")

	def test_sincronizar_actualiza_lo_no_corregido(self):
		fechas.sincronizar_fechas(carpeta_con([fila("Junio de 2031", "2031-07-10")]))
		fechas.sincronizar_fechas(carpeta_con([fila("Junio de 2031", "2031-07-14")]))
		nombre = fechas.clave_fecha(fila("Junio de 2031", "2031-07-14"))
		self.assertEqual(str(frappe.db.get_value("Fecha Tributaria", nombre, "fecha")), "2031-07-14")
		self.assertFalse(frappe.db.get_value("Fecha Tributaria", nombre, "corregida_a_mano"))

	def test_nombres_de_doctype_traducidos(self):
		frappe.local.lang = "es"
		frappe.local.lang_full_dict = None
		self.assertEqual(frappe._("Obligacion Tributaria"), "Obligación tributaria")


def carpeta_con(filas):
	carpeta = Path(tempfile.mkdtemp())
	(carpeta / "2031.json").write_text(json.dumps(filas, ensure_ascii=False))
	return carpeta


def fila(periodo, f):
	return {
		"obligacion": "Retención en la fuente",
		"anio": 2031,
		"periodo": periodo,
		"segmento": "Todos",
		"cifras": "1",
		"digito_desde": 7,
		"digito_hasta": 8,
		"fecha": f,
		"fuente": "prueba",
	}


def fecha(obligacion, anio, periodo, segmento, cifras, desde, hasta, f):
	return frappe.get_doc(
		{
			"doctype": "Fecha Tributaria",
			"obligacion": obligacion,
			"anio": anio,
			"periodo": periodo,
			"segmento": segmento,
			"cifras": cifras,
			"digito_desde": desde,
			"digito_hasta": hasta,
			"fecha": f,
			"fuente": "prueba",
		}
	)
