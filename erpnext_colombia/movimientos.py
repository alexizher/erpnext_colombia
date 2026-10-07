from erpnext_colombia.partes import tercero_de

PARTE_DEL_ENCABEZADO = {
	"Sales Invoice": ("Customer", "customer"),
	"Purchase Invoice": ("Supplier", "supplier"),
}
PARTES_CON_TERCERO = ("Customer", "Supplier")


def completar_tercero(doc, method=None):
	"""El tercero de una factura, un pago o una línea con cliente/proveedor es siempre el de esa parte.

	Se reemplaza en cada validación, no solo cuando está vacío: si Daniela cambia el cliente de un
	borrador, o duplica un documento y cambia la parte, el tercero viejo no debe quedarse.
	"""
	if doc.doctype == "Journal Entry":
		for fila in doc.get("accounts"):
			if fila.party_type in PARTES_CON_TERCERO and (t := tercero_de(fila.party_type, fila.party)):
				fila.tercero = t
		return

	if doc.doctype == "Payment Entry":
		doctype_parte, nombre = doc.party_type, doc.party
	else:
		doctype_parte, campo = PARTE_DEL_ENCABEZADO[doc.doctype]
		nombre = doc.get(campo)
	if doctype_parte in PARTES_CON_TERCERO and (t := tercero_de(doctype_parte, nombre)):
		doc.tercero = t
