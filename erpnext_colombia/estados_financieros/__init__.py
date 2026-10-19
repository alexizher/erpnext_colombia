import frappe

MODULO = "ERPNext Colombia"


def plantillas():
	"""Definiciones de las plantillas NIIF de la app: grupo 2 y luego grupo 3, cada uno en el orden
	de sus estados (situación financiera primero)."""
	from erpnext_colombia.estados_financieros import grupo3

	definiciones = list(grupo3.PLANTILLAS)
	try:
		from erpnext_colombia.estados_financieros import grupo2
	except ImportError:
		return definiciones
	return list(grupo2.PLANTILLAS) + definiciones


def sincronizar_plantillas():
	"""Crea o reemplaza las plantillas de la app. Las filas se reescriben enteras en cada migración."""
	for definicion in plantillas():
		nombre = definicion["name"]
		if frappe.db.exists("Financial Report Template", nombre):
			doc = frappe.get_doc("Financial Report Template", nombre)
		else:
			doc = frappe.new_doc("Financial Report Template")
			doc.template_name = nombre
		doc.report_type = definicion["report_type"]
		doc.module = MODULO
		doc.set("rows", [])
		for fila in definicion["rows"]:
			doc.append("rows", fila)
		doc.flags.ignore_permissions = True
		frappe.flags.in_import = True  # evita que Frappe exporte la plantilla a archivos JSON
		try:
			doc.save()
		finally:
			frappe.flags.in_import = False
