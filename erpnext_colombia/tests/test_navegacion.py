import json

import frappe
from frappe.tests import IntegrationTestCase

from erpnext_colombia.campos import CAMPOS
from erpnext_colombia.instalacion import configurar


class TestNavegacion(IntegrationTestCase):
	def test_dock_tiene_oficina(self):
		riel = frappe.get_all(
			"Dock", filters={"app": "erpnext_colombia", "standard": 1}, fields=["name", "mount_on"]
		)
		self.assertEqual([r.mount_on for r in riel], ["erpnext"])
		items = frappe.get_all("Dock Item", filters={"parent": riel[0].name}, fields=["title", "link_to"])
		self.assertEqual([(i.title, i.link_to) for i in items], [("Oficina", "Oficina")])

	def test_oficina_abre_en_el_tablero_y_trae_vencimientos(self):
		barra = frappe.get_doc("Sidebar", "Oficina")
		self.assertEqual((barra.items[0].link_type, barra.items[0].link_to), ("Dashboard", "Vencimientos"))
		destinos = {i.link_to for i in barra.items}
		for destino in (
			"Vencimiento",
			"Customer",
			"Vencimientos por Cliente",
			"Configuracion de Vencimientos",
		):
			self.assertIn(destino, destinos)
		self.assertFalse(frappe.db.exists("Sidebar", "Vencimientos"))

	def test_contabilidad_trae_terceros_y_estados_niif(self):
		configurar()
		capa = frappe.get_doc("Custom Sidebar", {"module": "Accounts", "user": ""})
		agregados = [i for i in capa.sidebar_items if i.added]
		self.assertIn(("Link", "DocType", "Tercero"), [(i.type, i.link_type, i.link_to) for i in agregados])
		plantillas = {json.loads(i.filters)[0][3] for i in agregados if i.link_type == "Report" and i.filters}
		self.assertIn("CO Grupo 2 - Situación financiera", plantillas)
		self.assertIn("CO Grupo 3 - Resultados", plantillas)

	def test_estados_en_orden_contable_por_grupo(self):
		from erpnext_colombia.navegacion import filas_de_contabilidad

		reportes = [
			f["label"] for f in filas_de_contabilidad() if f.get("link_type") == "Report" and f.get("filters")
		]
		self.assertEqual(
			reportes,
			[
				"Grupo 2 - Situación financiera",
				"Grupo 2 - Resultado integral",
				"Grupo 2 - Flujos de efectivo",
				"Grupo 2 - Cambios en el patrimonio",
				"Grupo 3 - Situación financiera",
				"Grupo 3 - Resultados",
			],
		)

	def test_configurar_dos_veces_no_duplica_la_seccion(self):
		configurar()
		configurar()
		capa = frappe.get_doc("Custom Sidebar", {"module": "Accounts", "user": ""})
		etiquetas = [i.label for i in capa.sidebar_items if i.added]
		self.assertEqual(len(etiquetas), len(set(etiquetas)))

	def test_campos_de_empresa_solo_para_colombia(self):
		for campo in CAMPOS["Company"]:
			self.assertEqual(campo.get("depends_on"), "eval:doc.country=='Colombia'", campo["fieldname"])

	def test_contabilidad_trae_los_libros_por_tercero(self):
		configurar()
		capa = frappe.get_doc("Custom Sidebar", {"module": "Accounts", "user": ""})
		reportes = {i.link_to for i in capa.sidebar_items if i.added and i.link_type == "Report"}
		self.assertIn("Balance de Prueba por Tercero", reportes)
		self.assertIn("Auxiliar por Tercero", reportes)

	def test_oficina_trae_honorarios_y_prospectos(self):
		destinos = {i.link_to for i in frappe.get_doc("Sidebar", "Oficina").items}
		for destino in ("Honorarios por Cliente", "Configuracion de Honorarios", "Sales Invoice", "Lead"):
			self.assertIn(destino, destinos)
