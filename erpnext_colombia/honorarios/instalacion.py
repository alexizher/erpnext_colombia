import frappe

from erpnext_colombia.honorarios.facturacion import CONFIGURACION

ARTICULO = "HONORARIOS"


def configurar():
	crear_articulo()


def crear_articulo():
	"""El servicio con el que salen las facturas de honorarios. Antes del asistente no hay grupos ni unidades."""
	if frappe.db.get_single_value(CONFIGURACION, "articulo"):
		return
	if not frappe.db.exists("Item", ARTICULO):
		if not (frappe.db.exists("Item Group", "Services") and frappe.db.exists("UOM", "Unit")):
			return
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": ARTICULO,
				"item_name": "Honorarios contables",
				"item_group": "Services",
				"stock_uom": "Unit",
				"is_stock_item": 0,
				"include_item_in_manufacturing": 0,
				"is_sales_item": 1,
				"is_purchase_item": 0,
			}
		).insert(ignore_permissions=True)
	frappe.db.set_single_value(CONFIGURACION, "articulo", ARTICULO)
