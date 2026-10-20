"""Vista de oficina: lo que ve quien lleva la oficina contable, sin el resto de ERPNext.

Se asigna con el perfil de módulos "Oficina contable" en la ficha del usuario. Con él:

- el menú oculta los módulos que no son de la oficina ni de la contabilidad. Es solo navegación:
  los permisos siguen siendo los de sus roles, y un cliente o un artículo se abre igual;
- la barra de íconos queda con Oficina primero y Contabilidad después;
- al entrar llega al tablero de la oficina.

Quitar el perfil devuelve la vista completa.
"""

import frappe
from frappe.desk.doctype.dock.dock import _save_layer, get_dock
from frappe.utils.modules import get_blockable_module_names

PERFIL = "Oficina contable"
APP = "erpnext_colombia"
RIEL = "erpnext"
RUTA_INICIO = "/desk/dashboard-view/Vencimientos"
MODULOS_VISIBLES = frozenset({"Oficina", "Accounts", "ERPNext Colombia", "Vencimientos", "Honorarios"})
# El título del ícono no pasa por la traducción: sin él diría "Accounts".
BARRA = (
	{"link_type": "Sidebar", "link_to": "Oficina"},
	{"link_type": "Sidebar", "link_to": "Accounts", "title": "Contabilidad"},
)


def configurar() -> None:
	"""Crea o pone al día el perfil. Un módulo nuevo de cualquier app queda oculto también."""
	bloquear = [m for m in get_blockable_module_names() if m not in MODULOS_VISIBLES]
	if frappe.db.exists("Module Profile", PERFIL):
		perfil = frappe.get_doc("Module Profile", PERFIL)
		if {f.module for f in perfil.block_modules} == set(bloquear):
			return
	else:
		perfil = frappe.new_doc("Module Profile")
		perfil.module_profile_name = PERFIL
	perfil.set("block_modules", [{"module": m} for m in bloquear])
	perfil.save(ignore_permissions=True)


def tiene_el_perfil(doc) -> bool:
	return doc.get("module_profile") == PERFIL


def al_validar_usuario(doc, method=None):
	if tiene_el_perfil(doc):
		doc.default_app = APP
		return
	if _lo_tenia(doc):
		# Lo que el perfil puso se va con él; lo que el usuario eligió aparte se queda.
		if doc.default_app == APP:
			doc.default_app = ""
		if {f.module for f in doc.block_modules} == _modulos_del_perfil():
			doc.set("block_modules", [])


def al_guardar_usuario(doc, method=None):
	if tiene_el_perfil(doc):
		_save_layer(RIEL, list(BARRA), user=doc.name, require_visible=False)
	elif _lo_tenia(doc) and (barra := get_dock(RIEL, user=doc.name)):
		frappe.delete_doc("Dock", barra.name, ignore_permissions=True)


def _lo_tenia(doc) -> bool:
	antes = doc.get_doc_before_save()
	return bool(antes) and tiene_el_perfil(antes)


def _modulos_del_perfil() -> set[str]:
	return set(
		frappe.get_all(
			"Block Module", filters={"parenttype": "Module Profile", "parent": PERFIL}, pluck="module"
		)
	)
