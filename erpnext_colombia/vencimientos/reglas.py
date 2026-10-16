import re

import frappe

ESTADOS = ("Pendiente", "En preparación", "Presentada", "Pagada", "No aplica")
ABIERTOS = ("Pendiente", "En preparación")
SEGMENTOS = ("Todos", "Gran contribuyente", "Persona jurídica", "Persona natural")
CONFIGURACION = "Configuracion de Vencimientos"


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
	return frappe.db.get_single_value(CONFIGURACION, "dias_anticipacion") or 15
