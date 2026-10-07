from erpnext_colombia.partes import tercero_de

PARTE_DEL_ENCABEZADO = {
	"Sales Invoice": ("Customer", "customer"),
	"Purchase Invoice": ("Supplier", "supplier"),
}
PARTES_CON_TERCERO = ("Customer", "Supplier")


def completar_tercero(doc, method=None):
	if doc.doctype == "Journal Entry":
		for fila in doc.get("accounts"):
			if not fila.get("tercero") and fila.party_type in PARTES_CON_TERCERO:
				fila.tercero = tercero_de(fila.party_type, fila.party)
		return

	if doc.get("tercero"):
		return
	if doc.doctype == "Payment Entry":
		if doc.party_type in PARTES_CON_TERCERO:
			doc.tercero = tercero_de(doc.party_type, doc.party)
		return
	doctype_parte, campo = PARTE_DEL_ENCABEZADO[doc.doctype]
	doc.tercero = tercero_de(doctype_parte, doc.get(campo))
