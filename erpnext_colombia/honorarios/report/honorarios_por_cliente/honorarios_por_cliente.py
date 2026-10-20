import frappe
from frappe import _
from frappe.query_builder import Case
from frappe.query_builder.functions import Count, Min, Sum
from frappe.utils import flt


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return columnas(), filas(filters)


def filas(filters) -> list[dict]:
	"""Facturas de honorarios enviadas en el rango, sumadas por cliente."""
	fv = frappe.qb.DocType("Sales Invoice")
	consulta = (
		frappe.qb.from_(fv)
		.select(
			fv.customer,
			fv.customer_name,
			fv.tercero,
			Count(fv.name).as_("facturas"),
			Sum(fv.grand_total).as_("facturado"),
			Sum(fv.outstanding_amount).as_("saldo"),
			Min(Case().when(fv.outstanding_amount > 0, fv.posting_date)).as_("pendiente_desde"),
		)
		.where(fv.docstatus == 1)
		.where(fv.co_periodo_honorarios.isnotnull() & (fv.co_periodo_honorarios != ""))
		.where(fv.company == filters.company)
		.where(fv.posting_date[filters.from_date : filters.to_date])
		.groupby(fv.customer, fv.customer_name, fv.tercero)
		.orderby(fv.customer_name)
	)
	if filters.customer:
		consulta = consulta.where(fv.customer == filters.customer)
	resultado = consulta.run(as_dict=True)
	nits = (
		dict(
			frappe.get_all(
				"Tercero",
				filters={"name": ("in", {f.tercero for f in resultado if f.tercero})},
				fields=["name", "nit_completo"],
				as_list=True,
			)
		)
		if resultado
		else {}
	)
	for f in resultado:
		f.pagado = flt(f.facturado) - flt(f.saldo)
		f.nit = nits.get(f.tercero)
	return resultado


def columnas():
	return [
		{
			"fieldname": "customer",
			"label": _("Cliente"),
			"fieldtype": "Link",
			"options": "Customer",
			"width": 120,
		},
		{"fieldname": "customer_name", "label": _("Nombre"), "fieldtype": "Data", "width": 220},
		{"fieldname": "nit", "label": _("NIT"), "fieldtype": "Data", "width": 120},
		{"fieldname": "facturas", "label": _("Facturas"), "fieldtype": "Int", "width": 90},
		{"fieldname": "facturado", "label": _("Facturado"), "fieldtype": "Currency", "width": 140},
		{"fieldname": "pagado", "label": _("Pagado"), "fieldtype": "Currency", "width": 140},
		{"fieldname": "saldo", "label": _("Saldo"), "fieldtype": "Currency", "width": 140},
		{"fieldname": "pendiente_desde", "label": _("Debe desde"), "fieldtype": "Date", "width": 110},
	]
