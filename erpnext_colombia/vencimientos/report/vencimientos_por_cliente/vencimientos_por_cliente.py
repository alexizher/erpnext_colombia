import frappe
from frappe import _


def execute(filters=None):
	filters = frappe._dict(filters or {})
	condiciones = {"anio": filters.anio} if filters.anio else {}
	for campo in ("cliente", "obligacion", "estado"):
		if filters.get(campo):
			condiciones[campo] = filters.get(campo)
	filas = frappe.get_all(
		"Vencimiento",
		filters=condiciones,
		fields=[
			"name",
			"cliente",
			"cliente_nombre",
			"tercero",
			"obligacion",
			"periodo",
			"fecha_vencimiento",
			"estado",
			"radicado",
			"fecha_presentacion",
		],
		order_by="cliente_nombre, fecha_vencimiento",
	)
	nits = dict(
		frappe.get_all(
			"Tercero",
			filters={"name": ("in", {f.tercero for f in filas if f.tercero})},
			fields=["name", "nit_completo"],
			as_list=True,
		)
	)
	for f in filas:
		f.nit = nits.get(f.tercero)
	return columnas(), filas


def columnas():
	return [
		{
			"fieldname": "name",
			"label": _("Vencimiento"),
			"fieldtype": "Link",
			"options": "Vencimiento",
			"width": 140,
		},
		{"fieldname": "cliente_nombre", "label": _("Cliente"), "fieldtype": "Data", "width": 200},
		{"fieldname": "nit", "label": _("NIT"), "fieldtype": "Data", "width": 130},
		{
			"fieldname": "obligacion",
			"label": _("Obligación"),
			"fieldtype": "Link",
			"options": "Obligacion Tributaria",
			"width": 160,
		},
		{"fieldname": "periodo", "label": _("Periodo"), "fieldtype": "Data", "width": 150},
		{"fieldname": "fecha_vencimiento", "label": _("Vence"), "fieldtype": "Date", "width": 100},
		{"fieldname": "estado", "label": _("Estado"), "fieldtype": "Data", "width": 120},
		{"fieldname": "radicado", "label": _("Radicado"), "fieldtype": "Data", "width": 160},
		{"fieldname": "fecha_presentacion", "label": _("Presentada el"), "fieldtype": "Date", "width": 110},
	]
