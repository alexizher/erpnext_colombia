import frappe
from frappe import _

from erpnext_colombia.libros_por_tercero import LibroPorTercero


def execute(filters=None):
	return columnas(), LibroPorTercero(frappe._dict(filters or {})).saldos()


def columnas():
	return [
		{
			"fieldname": "account",
			"label": _("Cuenta"),
			"fieldtype": "Link",
			"options": "Account",
			"width": 260,
		},
		{
			"fieldname": "tercero",
			"label": _("Tercero"),
			"fieldtype": "Link",
			"options": "Tercero",
			"width": 120,
		},
		{"fieldname": "tercero_nombre", "label": _("Nombre"), "fieldtype": "Data", "width": 220},
		{"fieldname": "nit", "label": _("NIT"), "fieldtype": "Data", "width": 120},
		{"fieldname": "inicial", "label": _("Saldo inicial"), "fieldtype": "Currency", "width": 140},
		{"fieldname": "debito", "label": _("Débitos"), "fieldtype": "Currency", "width": 140},
		{"fieldname": "credito", "label": _("Créditos"), "fieldtype": "Currency", "width": 140},
		{"fieldname": "final", "label": _("Saldo final"), "fieldtype": "Currency", "width": 140},
	]
