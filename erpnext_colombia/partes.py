import frappe
from frappe import _
from frappe.utils import getdate

TIPO_ERPNEXT = {"Persona jurídica": "Company", "Persona natural": "Individual"}
CAMPO_NOMBRE = {"Customer": "customer_name", "Supplier": "supplier_name"}
CAMPO_TIPO = {"Customer": "customer_type", "Supplier": "supplier_type"}
NOMBRE_PARTE = {"Customer": _("cliente"), "Supplier": _("proveedor")}
PROPIEDAD = {"Customer": "es_cliente", "Supplier": "es_proveedor"}


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


def _grupo(doctype: str, configuracion: str, campo: str) -> str | None:
	"""El grupo por defecto de la configuración de ventas o compras; si no hay, el primero que no es grupo padre."""
	return frappe.db.get_single_value(configuracion, campo) or frappe.db.get_value(
		doctype, {"is_group": 0}, "name", order_by="lft"
	)


def crear_parte(doctype: str, tercero: str) -> None:
	"""Crea el cliente o el proveedor del tercero si todavía no existe."""
	if frappe.db.exists(doctype, {"co_tercero": tercero}):
		return
	parte = frappe.new_doc(doctype)
	parte.co_tercero = tercero
	if doctype == "Customer":
		parte.customer_group = _grupo("Customer Group", "Selling Settings", "customer_group")
		parte.territory = _grupo("Territory", "Selling Settings", "territory")
	else:
		parte.supplier_group = _grupo("Supplier Group", "Buying Settings", "supplier_group")
	parte.insert()


def marcar_propiedad(doc, method=None):
	"""Un cliente o proveedor creado por su lado deja marcada la propiedad en su tercero."""
	if doc.get("co_tercero"):
		frappe.db.set_value("Tercero", doc.co_tercero, PROPIEDAD[doc.doctype], 1, update_modified=False)
