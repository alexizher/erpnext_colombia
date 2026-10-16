from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from erpnext_colombia.tests.utils import cliente_con, fecha_prueba, obligacion_prueba, vencimientos_de
from erpnext_colombia.vencimientos.generacion import generar


def preparar():
	fecha_prueba("Marzo de 2030", "2030-04-10", desde=0, hasta=9)
	fecha_prueba("Abril de 2030", "2030-05-10", desde=0, hasta=9)
	fecha_prueba("Cuota 1 de 2030", "2030-04-20", segmento="Persona jurídica", desde=0, hasta=9)
	fecha_prueba("Cuota 1 de 2030", "2030-02-20", segmento="Gran contribuyente", desde=0, hasta=9)


def obligacion(desde="2030-01-01", hasta=None):
	return [{"obligacion": obligacion_prueba(), "desde": desde, "hasta": hasta}]


class TestConciliacion(IntegrationTestCase):
	def setUp(self):
		preparar()

	def test_poner_hasta_cierra_los_abiertos_posteriores(self):
		c = cliente_con("900300401", "Con Uno S.A.S.", obligacion())
		generar(cliente=c, anio=2030)
		cliente_con("900300401", "Con Uno S.A.S.", obligacion(hasta="2030-04-30"))
		generar(cliente=c, anio=2030)
		abril = vencimientos_de(c, periodo="Abril de 2030")[0]
		self.assertEqual(abril.estado, "No aplica")
		self.assertTrue(abril.cerrado_por_sistema)
		self.assertEqual(vencimientos_de(c, periodo="Marzo de 2030")[0].estado, "Pendiente")

	def test_quitar_obligacion_cierra_abiertos(self):
		c = cliente_con("900300402", "Con Dos S.A.S.", obligacion())
		generar(cliente=c, anio=2030)
		cliente_con("900300402", "Con Dos S.A.S.", [])
		generar(cliente=c, anio=2030)
		self.assertTrue(all(v.estado == "No aplica" for v in vencimientos_de(c)))

	def test_no_toca_lo_presentado(self):
		c = cliente_con("900300403", "Con Tres S.A.S.", obligacion())
		generar(cliente=c, anio=2030)
		marzo = frappe.get_doc("Vencimiento", vencimientos_de(c, periodo="Marzo de 2030")[0].name)
		marzo.estado = "Presentada"
		marzo.save()
		cliente_con("900300403", "Con Tres S.A.S.", [])
		generar(cliente=c, anio=2030)
		self.assertEqual(vencimientos_de(c, periodo="Marzo de 2030")[0].estado, "Presentada")

	def test_cambio_de_segmento_reconcilia(self):
		c = cliente_con("900300404", "Con Cuatro S.A.S.", obligacion())
		generar(cliente=c, anio=2030)
		self.assertEqual(
			str(vencimientos_de(c, periodo="Cuota 1 de 2030")[0].fecha_vencimiento), "2030-04-20"
		)
		cliente_con("900300404", "Con Cuatro S.A.S.", obligacion(), gran_contribuyente=1)
		generar(cliente=c, anio=2030)
		cuota = vencimientos_de(c, periodo="Cuota 1 de 2030")
		self.assertEqual(len(cuota), 1)
		# La fila de persona jurídica ya no aplica y la de gran contribuyente sí, con el mismo periodo:
		# el vencimiento sigue abierto y pasa a la fecha nueva.
		self.assertEqual(cuota[0].estado, "Pendiente")
		self.assertEqual(str(cuota[0].fecha_vencimiento), "2030-02-20")

	def test_no_aplica_manual_no_se_reabre(self):
		c = cliente_con("900300405", "Con Cinco S.A.S.", obligacion())
		generar(cliente=c, anio=2030)
		v = frappe.get_doc("Vencimiento", vencimientos_de(c, periodo="Abril de 2030")[0].name)
		v.estado = "No aplica"
		v.save()
		generar(cliente=c, anio=2030)
		self.assertEqual(vencimientos_de(c, periodo="Abril de 2030")[0].estado, "No aplica")

	def test_reabre_lo_que_cerro_el_sistema(self):
		c = cliente_con("900300406", "Con Seis S.A.S.", obligacion())
		generar(cliente=c, anio=2030)
		cliente_con("900300406", "Con Seis S.A.S.", [])
		generar(cliente=c, anio=2030)
		cliente_con("900300406", "Con Seis S.A.S.", obligacion())
		generar(cliente=c, anio=2030)
		self.assertTrue(all(v.estado == "Pendiente" for v in vencimientos_de(c)))

	def test_cliente_desactivado_cierra_abiertos(self):
		c = cliente_con("900300407", "Con Siete S.A.S.", obligacion())
		generar(cliente=c, anio=2030)
		frappe.db.set_value("Customer", c, "disabled", 1)
		generar(cliente=c, anio=2030)
		self.assertTrue(all(v.estado == "No aplica" for v in vencimientos_de(c)))

	def test_corregir_fecha_mueve_abiertos_y_deja_comentario(self):
		f = fecha_prueba("Mayo de 2030", "2030-06-10", desde=0, hasta=9)
		c = cliente_con("900300408", "Con Ocho S.A.S.", obligacion())
		generar(cliente=c, anio=2030)
		f.reload()
		f.fecha = "2030-06-12"
		f.save()
		v = vencimientos_de(c, periodo="Mayo de 2030")[0]
		self.assertEqual(str(v.fecha_vencimiento), "2030-06-12")
		comentarios = frappe.get_all(
			"Comment", filters={"reference_doctype": "Vencimiento", "reference_name": v.name}, pluck="content"
		)
		self.assertTrue(any("2030-06-10" in x and "2030-06-12" in x for x in comentarios), comentarios)

	def test_corregir_fecha_no_mueve_presentados(self):
		f = fecha_prueba("Junio de 2030", "2030-07-10", desde=0, hasta=9)
		c = cliente_con("900300409", "Con Nueve S.A.S.", obligacion())
		generar(cliente=c, anio=2030)
		v = frappe.get_doc("Vencimiento", vencimientos_de(c, periodo="Junio de 2030")[0].name)
		v.estado = "Presentada"
		v.save()
		f.reload()
		f.fecha = "2030-07-14"
		f.save()
		self.assertEqual(str(vencimientos_de(c, periodo="Junio de 2030")[0].fecha_vencimiento), "2030-07-10")

	def test_guardar_cliente_genera_sus_vencimientos(self):
		with patch("erpnext_colombia.vencimientos.generacion.generar") as g:
			c = cliente_con("900300410", "Con Diez S.A.S.", obligacion())
		g.assert_called_with(cliente=c)
