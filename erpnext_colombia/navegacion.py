"""Entradas de la app en el menú de Contabilidad de ERPNext.

Ese menú es un Sidebar de ERPNext y la app no puede escribir su archivo. Frappe deja que el sitio le
agregue filas en su propia capa (Custom Sidebar sin usuario); van al final y no mueven las de ERPNext.
"""

import json

from frappe.desk.doctype.custom_sidebar.custom_sidebar import add_site_sidebar_item

MODULO_CONTABILIDAD = "Accounts"
SECCION = "Terceros y NIIF"
PREFIJO_PLANTILLA = "CO "


def _seccion() -> dict:
	return {"type": "Section Break", "label": SECCION, "icon": "landmark", "indent": 1, "collapsible": 1}


def _enlace(etiqueta: str, tipo: str, destino: str, icono: str, filtros: list | None = None) -> dict:
	fila = {
		"type": "Link",
		"label": etiqueta,
		"link_type": tipo,
		"link_to": destino,
		"icon": icono,
		"child": 1,
	}
	if filtros:
		fila["filters"] = json.dumps(filtros)
	return fila


def _estado_financiero(plantilla: dict) -> dict:
	"""El reporte de ERPNext (Balance Sheet, Cash Flow...) abierto con la plantilla NIIF ya escogida."""
	reporte = plantilla["report_type"]
	return _enlace(
		plantilla["name"].removeprefix(PREFIJO_PLANTILLA),
		"Report",
		reporte,
		"sheet",
		[[reporte, "report_template", "=", plantilla["name"]]],
	)


def filas_de_contabilidad() -> list[dict]:
	from erpnext_colombia.estados_financieros import plantillas

	return [
		_seccion(),
		_enlace("Terceros", "DocType", "Tercero", "users"),
		*(_estado_financiero(p) for p in plantillas()),
	]


def agregar_a_contabilidad() -> None:
	# add_site_sidebar_item salta la fila que ya está, así que migrar varias veces no duplica.
	for fila in filas_de_contabilidad():
		add_site_sidebar_item(MODULO_CONTABILIDAD, fila)
