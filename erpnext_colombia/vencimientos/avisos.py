import frappe
from frappe import _
from frappe.desk.form import assign_to
from frappe.utils import add_days, getdate, today

from erpnext_colombia.vencimientos.reglas import ABIERTOS, dias_anticipacion, responsable


def abrir_todos(hoy=None) -> int:
	limite = add_days(getdate(hoy or today()), dias_anticipacion())
	creados = 0
	for v in frappe.get_all(
		"Vencimiento",
		filters={"estado": ("in", ABIERTOS), "fecha_vencimiento": ("<=", limite)},
		fields=["name", "asignado_a", "fecha_vencimiento", "titulo"],
	):
		usuario = v.asignado_a or responsable()
		if frappe.db.exists(
			"ToDo",
			{
				"reference_type": "Vencimiento",
				"reference_name": v.name,
				"allocated_to": usuario,
				"status": "Open",
			},
		):
			continue
		assign_to._add(
			{
				"assign_to": [usuario],
				"doctype": "Vencimiento",
				"name": v.name,
				"date": v.fecha_vencimiento,
				"description": _("Vence {0}: {1}").format(v.fecha_vencimiento, v.titulo),
			},
			ignore_permissions=True,
		)
		creados += 1
	return creados


def cerrar_si_termino(doc):
	if doc.estado not in ABIERTOS and doc.has_value_changed("estado"):
		assign_to.close_all_assignments("Vencimiento", doc.name, ignore_permissions=True)
