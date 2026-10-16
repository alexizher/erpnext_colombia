import frappe
from frappe.tests import IntegrationTestCase

from erpnext_colombia.tests.utils import cliente_con, fecha_prueba, obligacion_prueba
from erpnext_colombia.vencimientos.generacion import generar


class TestVistas(IntegrationTestCase):
	def test_reporte_filtra_por_cliente_y_anio(self):
		from erpnext_colombia.vencimientos.report.vencimientos_por_cliente.vencimientos_por_cliente import (
			execute,
		)

		fecha_prueba("Diciembre de 2030", "2031-01-10", anio=2031, desde=0, hasta=9)
		c = cliente_con(
			"900600701", "Vis Uno S.A.S.", [{"obligacion": obligacion_prueba(), "desde": "2030-01-01"}]
		)
		generar(cliente=c, anio=2031)
		columnas, filas = execute(frappe._dict({"anio": 2031, "cliente": c}))
		self.assertIn("radicado", [col["fieldname"] for col in columnas])
		self.assertEqual([f["periodo"] for f in filas], ["Diciembre de 2030"])

	def test_cliente_muestra_sus_vencimientos(self):
		datos = frappe.get_meta("Customer").get_dashboard_data()
		self.assertEqual(datos.non_standard_fieldnames.get("Vencimiento"), "cliente")
		self.assertTrue(any("Vencimiento" in grupo["items"] for grupo in datos.transactions))

	def test_kanban_existe(self):
		self.assertEqual(frappe.db.get_value("Kanban Board", "Vencimientos", "field_name"), "estado")

	def test_tarjetas_tablero_y_barra(self):
		tarjetas = ("Vencidos sin presentar", "Vencen esta semana", "Próximos 15 días")
		for tarjeta in tarjetas:
			self.assertTrue(frappe.db.exists("Number Card", tarjeta), tarjeta)
		tablero = frappe.get_doc("Dashboard", "Vencimientos")
		self.assertEqual([c.card for c in tablero.cards], list(tarjetas))
		barra = frappe.get_doc("Sidebar", "Vencimientos")
		self.assertEqual((barra.items[0].link_type, barra.items[0].link_to), ("Dashboard", "Vencimientos"))
		riel = frappe.get_all(
			"Dock", filters={"app": "erpnext_colombia", "standard": 1}, fields=["name", "mount_on"]
		)
		self.assertEqual([r.mount_on for r in riel], ["erpnext"])
		items = frappe.get_all("Dock Item", filters={"parent": riel[0].name}, pluck="link_to")
		self.assertEqual(items, ["Vencimientos"])

	def test_la_barra_abre_en_la_misma_pestana(self):
		barra = frappe.get_doc("Sidebar", "Vencimientos")
		self.assertEqual([i.label for i in barra.items if i.open_in_new_tab], [])
