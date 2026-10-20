import frappe
from frappe.tests import IntegrationTestCase

from erpnext_colombia.oficina.perfil import MODULOS_VISIBLES, PERFIL, RUTA_INICIO

CORREO = "perfil.oficina@example.com"
OTRO = "sin.perfil@example.com"


def usuario(correo, perfil=None):
	if frappe.db.exists("User", correo):
		u = frappe.get_doc("User", correo)
	else:
		u = frappe.get_doc(
			{"doctype": "User", "email": correo, "first_name": "Prueba", "send_welcome_email": 0}
		)
		u.append("roles", {"role": "Accounts Manager"})
		u.append("roles", {"role": "System Manager"})
	u.module_profile = perfil
	u.save()
	return u


class TestPerfilOficina(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		from erpnext_colombia.instalacion import configurar

		configurar()

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_perfil_oculta_lo_que_no_es_de_la_oficina(self):
		bloqueados = {f.module for f in frappe.get_doc("Module Profile", PERFIL).block_modules}
		for modulo in ("Stock", "Manufacturing", "Projects", "Website", "Selling", "Buying"):
			self.assertIn(modulo, bloqueados)
		self.assertFalse(bloqueados & MODULOS_VISIBLES)

	def test_al_asignar_el_perfil_entra_por_oficina(self):
		u = usuario(CORREO, PERFIL)
		u.reload()
		self.assertEqual(u.default_app, "erpnext_colombia")
		from frappe.apps import get_route

		self.assertEqual(get_route("erpnext_colombia"), RUTA_INICIO)

	def test_su_barra_tiene_oficina_y_contabilidad(self):
		from frappe.desk.doctype.dock.dock import resolve_app_dock

		usuario(CORREO, PERFIL)
		frappe.set_user(CORREO)
		riel = [(e["link_to"], e["title"]) for e in resolve_app_dock("erpnext") if not e.get("hidden")]
		self.assertEqual(riel, [("Oficina", "Oficina"), ("Accounts", "Contabilidad")])

	def test_oficina_conserva_clientes_y_prospectos(self):
		from frappe.desk.doctype.sidebar.sidebar import resolve_sidebar

		usuario(CORREO, PERFIL)
		barra = resolve_sidebar("Oficina", CORREO)
		destinos = {i["link_to"] for i in barra.items}
		self.assertIn("Customer", destinos)
		self.assertIn("Lead", destinos)

	def test_usuario_sin_perfil_ve_todo(self):
		from frappe.desk.doctype.dock.dock import resolve_app_dock

		u = usuario(OTRO)
		self.assertFalse(u.block_modules)
		self.assertNotEqual(u.default_app, "erpnext_colombia")
		frappe.set_user(OTRO)
		riel = [e["link_to"] for e in resolve_app_dock("erpnext")]
		self.assertIn("Stock", riel)

	def test_quitar_el_perfil_devuelve_la_vista_completa(self):
		from frappe.desk.doctype.dock.dock import get_dock

		usuario(CORREO, PERFIL)
		u = usuario(CORREO, None)
		self.assertNotEqual(u.default_app, "erpnext_colombia")
		self.assertIsNone(get_dock("erpnext", user=CORREO))
