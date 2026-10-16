import frappe

OBLIGACIONES = [
	{"nombre": "Renta PN", "formulario": "210", "responsabilidad_rut": "05", "tiene_pago": 1},
	{"nombre": "Renta PJ", "formulario": "110", "responsabilidad_rut": "05", "tiene_pago": 1},
	{"nombre": "IVA bimestral", "formulario": "300", "responsabilidad_rut": "48", "tiene_pago": 1},
	{"nombre": "IVA cuatrimestral", "formulario": "300", "responsabilidad_rut": "48", "tiene_pago": 1},
	{"nombre": "Retención en la fuente", "formulario": "350", "responsabilidad_rut": "07", "tiene_pago": 1},
	{
		"nombre": "Exógena",
		"formulario": "Formatos 1001 y siguientes",
		"responsabilidad_rut": "14",
		"tiene_pago": 0,
	},
	{"nombre": "RST anticipo bimestral", "formulario": "2593", "responsabilidad_rut": "47", "tiene_pago": 1},
	{"nombre": "RST anual", "formulario": "260", "responsabilidad_rut": "47", "tiene_pago": 1},
]


def sincronizar_obligaciones():
	for datos in OBLIGACIONES:
		if frappe.db.exists("Obligacion Tributaria", datos["nombre"]):
			doc = frappe.get_doc("Obligacion Tributaria", datos["nombre"])
			doc.update(datos)
			doc.save(ignore_permissions=True)
		else:
			frappe.get_doc({"doctype": "Obligacion Tributaria", **datos}).insert(ignore_permissions=True)
