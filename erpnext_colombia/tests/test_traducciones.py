import glob
import json
import os

import frappe
from frappe import _
from frappe.tests import IntegrationTestCase


def pasos_de_bienvenida() -> list[dict]:
	"""Los pasos de bienvenida que ERPNext muestra en el inicio."""
	carpeta = frappe.get_app_path("erpnext")
	return [
		json.load(open(f)) for f in glob.glob(os.path.join(carpeta, "*", "onboarding_step", "*", "*.json"))
	]


class TestTraducciones(IntegrationTestCase):
	def setUp(self):
		self.idioma = frappe.local.lang
		frappe.local.lang = "es"
		frappe.local.lang_full_dict = None

	def tearDown(self):
		frappe.local.lang = self.idioma
		frappe.local.lang_full_dict = None

	def test_saludo_del_inicio(self):
		self.assertEqual(_("Good morning, {0}").format("Daniela"), "Buenos días, Daniela")
		self.assertEqual(_("{0} of {1} steps done").format(2, 9), "2 de 9 pasos hechos")

	def test_pantalla_de_entrada(self):
		self.assertEqual(_("Forgot password?"), "¿Olvidó su contraseña?")
		self.assertEqual(_("Sign In"), "Iniciar sesión")

	def test_descripcion_con_parrafos(self):
		original = next(
			p["description"] for p in pasos_de_bienvenida() if p.get("title") == "Write its bill of materials"
		)
		self.assertIn("\n\n", original)
		self.assertTrue(_(original).startswith("Las materias primas"), _(original))

	def test_todos_los_pasos_de_bienvenida_en_espanol(self):
		for paso in pasos_de_bienvenida():
			for campo in ("title", "action_label"):
				if texto := paso.get(campo):
					self.assertNotEqual(_(texto), texto, f"{campo} sin traducir: {texto}")

	def test_graficas_vacias_en_espanol(self):
		carpeta = frappe.get_app_path("erpnext")
		for archivo in glob.glob(os.path.join(carpeta, "*", "dashboard_chart", "*", "*.json")):
			if mensaje := json.load(open(archivo)).get("empty_state_message"):
				self.assertNotEqual(_(mensaje), mensaje, f"sin traducir: {mensaje}")

	def test_las_traducciones_anteriores_siguen(self):
		self.assertEqual(_("Obligacion Tributaria"), "Obligación tributaria")

	def test_vista_de_oficina_en_espanol(self):
		# El ícono y el menú de Contabilidad, y lo que muestra su inicio
		self.assertEqual(_("Accounts"), "Contabilidad")
		for texto in (
			"Total Outgoing Bills",
			"Total Incoming Bills",
			"Total Incoming Payment",
			"Receivables & Payables",
			"Registers & Profitability",
			"Budgeting",
			"Configuracion de Honorarios",
			"Honorarios por Cliente",
			"Balance de Prueba por Tercero",
			"Auxiliar por Tercero",
		):
			self.assertNotEqual(_(texto), texto, texto)
