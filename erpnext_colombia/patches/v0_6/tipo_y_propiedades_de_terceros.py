import frappe

from erpnext_colombia.contribuyente import responsabilidades_de, tipo_por_defecto
from erpnext_colombia.nit import DOCUMENTOS_DEL_EXTERIOR, codigo_tipo


def execute():
	"""Terceros de antes del tipo de contribuyente: tipo por documento y propiedades por sus enlaces."""
	clientes = set(frappe.get_all("Customer", filters={"co_tercero": ("is", "set")}, pluck="co_tercero"))
	proveedores = set(frappe.get_all("Supplier", filters={"co_tercero": ("is", "set")}, pluck="co_tercero"))
	for t in frappe.get_all(
		"Tercero",
		filters={"tipo_contribuyente": ("in", ("", None))},
		fields=["name", "tipo_documento", "naturaleza"],
	):
		tipo = tipo_por_defecto(t.naturaleza, codigo_tipo(t.tipo_documento) in DOCUMENTOS_DEL_EXTERIOR)
		frappe.db.set_value(
			"Tercero",
			t.name,
			{
				"tipo_contribuyente": tipo,
				**responsabilidades_de(tipo),
				"es_cliente": int(t.name in clientes),
				"es_proveedor": int(t.name in proveedores),
			},
			update_modified=False,
		)
