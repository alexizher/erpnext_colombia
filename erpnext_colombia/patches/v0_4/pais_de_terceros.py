import frappe

from erpnext_colombia.pais import PAIS


def execute():
	"""Los terceros creados antes del campo país son todos de Colombia."""
	tercero = frappe.qb.DocType("Tercero")
	frappe.qb.update(tercero).set(tercero.pais, PAIS).where(
		tercero.pais.isnull() | (tercero.pais == "")
	).run()
