import frappe
from frappe import _
from frappe.utils import getdate

from erpnext_colombia.pais import PAIS

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


def _por_defecto(configuracion: str, campo: str, etiqueta: str) -> str:
	"""Grupo o territorio por defecto de Ventas o Compras. Sin él no se adivina: escoger uno al azar
	deja clientes en "Government" o "Rest Of The World"."""
	valor = frappe.db.get_single_value(configuracion, campo)
	if campo == "territory" and not valor and frappe.db.exists("Territory", PAIS):
		valor = PAIS
	if not valor:
		frappe.throw(
			_("Para crear el {0} desde el tercero, escoja {1} por defecto en {2}.").format(
				_("cliente") if configuracion == "Selling Settings" else _("proveedor"),
				etiqueta,
				_("Configuración de ventas") if configuracion == "Selling Settings" else _("Configuración de compras"),
			)
		)
	return valor


def crear_parte(doctype: str, tercero: str) -> None:
	"""Crea el cliente o el proveedor del tercero si todavía no existe."""
	if frappe.db.exists(doctype, {"co_tercero": tercero}):
		return
	parte = frappe.new_doc(doctype)
	parte.co_tercero = tercero
	if doctype == "Customer":
		parte.customer_group = _por_defecto("Selling Settings", "customer_group", _("el grupo de clientes"))
		parte.territory = _por_defecto("Selling Settings", "territory", _("el territorio"))
	else:
		parte.supplier_group = _por_defecto("Buying Settings", "supplier_group", _("el grupo de proveedores"))
	parte.insert()


def marcar_propiedad(doc, method=None):
	"""Un cliente o proveedor creado por su lado deja marcada la propiedad en su tercero."""
	if doc.get("co_tercero"):
		frappe.db.set_value("Tercero", doc.co_tercero, PROPIEDAD[doc.doctype], 1, update_modified=False)
