"""Del prospecto (Lead) al cliente: el honorario propuesto pasa a ser su honorario mensual."""

import frappe
from frappe.utils import add_months, get_first_day, today

CONCEPTO = "Honorarios contables"


def al_crear_cliente(doc, method=None):
	if not doc.get("lead_name") or doc.get("co_honorarios"):
		return
	propuesto = frappe.db.get_value("Lead", doc.lead_name, "co_honorario_propuesto")
	if propuesto:
		doc.append(
			"co_honorarios",
			{
				"concepto": CONCEPTO,
				"valor": propuesto,
				"periodicidad": "Mensual",
				"desde": get_first_day(add_months(today(), 1)),
			},
		)
