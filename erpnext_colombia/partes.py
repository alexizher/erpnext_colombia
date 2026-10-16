import frappe
from frappe import _
from frappe.utils import getdate

TIPO_ERPNEXT = {"Persona jurídica": "Company", "Persona natural": "Individual"}
CAMPO_NOMBRE = {"Customer": "customer_name", "Supplier": "supplier_name"}
CAMPO_TIPO = {"Customer": "customer_type", "Supplier": "supplier_type"}
NOMBRE_PARTE = {"Customer": _("cliente"), "Supplier": _("proveedor")}


def tercero_de(doctype: str, nombre: str) -> str | None:
	if not (doctype and nombre):
		return None
	return frappe.get_cached_value(doctype, nombre, "co_tercero")


def antes_de_insertar(doc, method=None):
	"""Customer y Supplier se nombran antes de validar: el nombre tiene que estar puesto aquí."""
	campo = CAMPO_NOMBRE[doc.doctype]
	if not doc.get(campo) and doc.get("co_tercero"):
		doc.set(campo, frappe.db.get_value("Tercero", doc.co_tercero, "nombre_completo"))


def validar_parte(doc, method=None):
	if not doc.get("co_tercero"):
		return
	t = frappe.db.get_value("Tercero", doc.co_tercero, ["nit_completo", "naturaleza"], as_dict=True)
	doc.tax_id = t.nit_completo
	doc.set(CAMPO_TIPO[doc.doctype], TIPO_ERPNEXT[t.naturaleza])
	otro = frappe.db.get_value(doc.doctype, {"co_tercero": doc.co_tercero, "name": ("!=", doc.name)})
	if otro:
		frappe.throw(
			_("El tercero {0} ya es el {1} {2}. Use ese registro.").format(
				doc.co_tercero, NOMBRE_PARTE[doc.doctype], otro
			)
		)
	if doc.doctype == "Customer":
		_validar_obligaciones(doc)


def _validar_obligaciones(doc):
	vistas = set()
	for fila in doc.get("co_obligaciones") or []:
		if fila.obligacion in vistas:
			frappe.throw(_("La obligación {0} está dos veces. Deje una sola fila.").format(fila.obligacion))
		vistas.add(fila.obligacion)
		if fila.hasta and getdate(fila.hasta) < getdate(fila.desde):
			frappe.throw(
				_("En {0}, la fecha hasta ({1}) es anterior a la fecha desde ({2}).").format(
					fila.obligacion, fila.hasta, fila.desde
				)
			)


def validar_empresa(doc, method=None):
	if doc.get("co_tercero"):
		doc.tax_id = frappe.db.get_value("Tercero", doc.co_tercero, "nit_completo")
