"""La DIAN como tercero y proveedor: a ella se le deben las retenciones (2365) y los impuestos."""

import frappe

NIT = "800197268"
RAZON_SOCIAL = "Dirección de Impuestos y Aduanas Nacionales"
GRUPO = "Entidades públicas"
GRUPO_RAIZ = "All Supplier Groups"


def crear_dian() -> None:
	# Antes del asistente inicial no hay grupos de proveedores; la próxima migración la crea.
	if not frappe.db.exists("Supplier Group", GRUPO_RAIZ):
		return
	if not frappe.db.exists("Tercero", NIT):
		frappe.get_doc(
			{
				"doctype": "Tercero",
				"tipo_documento": "31 - NIT",
				"numero_documento": NIT,
				"razon_social": RAZON_SOCIAL,
			}
		).insert(ignore_permissions=True)
	if frappe.db.exists("Supplier", {"co_tercero": NIT}):
		return
	frappe.get_doc({"doctype": "Supplier", "co_tercero": NIT, "supplier_group": _grupo()}).insert(
		ignore_permissions=True
	)


def _grupo() -> str:
	if not frappe.db.exists("Supplier Group", GRUPO):
		frappe.get_doc(
			{"doctype": "Supplier Group", "supplier_group_name": GRUPO, "parent_supplier_group": GRUPO_RAIZ}
		).insert(ignore_permissions=True)
	return GRUPO
