import re

import frappe
from frappe.utils import cint

ESTADOS = ("Pendiente", "En preparación", "Presentada", "Pagada", "No aplica")
ABIERTOS = ("Pendiente", "En preparación")
SEGMENTOS = ("Todos", "Gran contribuyente", "Persona jurídica", "Persona natural")
CONFIGURACION = "Configuracion de Vencimientos"
DIAS_POR_DEFECTO = 15


def digitos(numero_documento: str | None, cifras: int) -> int | None:
	"""Último o dos últimos dígitos numéricos del documento, sin el DV. None si no tiene dígitos."""
	solo = re.sub(r"\D", "", numero_documento or "")
	if not solo:
		return None
	return int(solo[-cifras:])


def segmento(gran_contribuyente: bool, naturaleza: str | None) -> str | None:
	if gran_contribuyente:
		return "Gran contribuyente"
	return naturaleza or None


def responsable() -> str:
	return frappe.db.get_single_value(CONFIGURACION, "responsable") or "Administrator"


def dias_anticipacion() -> int:
	"""0 es válido (avisar el mismo día). get_single_value devuelve 0 también cuando nunca se guardó,
	así que se mira si hay un valor guardado."""
	singles = frappe.qb.DocType("Singles")
	guardado = (
		frappe.qb.from_(singles)
		.select(singles.value)
		.where((singles.doctype == CONFIGURACION) & (singles.field == "dias_anticipacion"))
		.run()
	)
	if not guardado or guardado[0][0] in (None, ""):
		return DIAS_POR_DEFECTO
	return cint(guardado[0][0])
