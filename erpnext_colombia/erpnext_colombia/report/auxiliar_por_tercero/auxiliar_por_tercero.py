import frappe
from frappe import _

from erpnext_colombia.libros_por_tercero import LibroPorTercero


def execute(filters=None):
	return columnas(), LibroPorTercero(frappe._dict(filters or {})).movimientos()


def columnas():
	return [
		{"fieldname": "posting_date", "label": _("Fecha"), "fieldtype": "Date", "width": 100},
		{
			"fieldname": "account",
			"label": _("Cuenta"),
			"fieldtype": "Link",
			"options": "Account",
			"width": 220,
		},
		{
			"fieldname": "tercero",
			"label": _("Tercero"),
			"fieldtype": "Link",
			"options": "Tercero",
			"width": 110,
		},
		{"fieldname": "tercero_nombre", "label": _("Nombre"), "fieldtype": "Data", "width": 180},
		{"fieldname": "voucher_type", "label": _("Tipo"), "fieldtype": "Data", "width": 120},
		{
			"fieldname": "voucher_no",
			"label": _("Comprobante"),
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 160,
		},
		{"fieldname": "detalle", "label": _("Detalle"), "fieldtype": "Data", "width": 200},
		{"fieldname": "debito", "label": _("Débito"), "fieldtype": "Currency", "width": 130},
		{"fieldname": "credito", "label": _("Crédito"), "fieldtype": "Currency", "width": 130},
		{"fieldname": "saldo", "label": _("Saldo"), "fieldtype": "Currency", "width": 140},
	]
