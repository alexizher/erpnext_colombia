import json
from pathlib import Path

import frappe

CARPETA = Path(__file__).parent / "fechas"
CAMPOS = (
	"obligacion",
	"anio",
	"periodo",
	"segmento",
	"cifras",
	"digito_desde",
	"digito_hasta",
	"fecha",
	"fuente",
)


def clave_fecha(d) -> str:
	return f"{d.get('obligacion')} {d.get('anio')} {d.get('periodo')} {d.get('segmento')} {int(d.get('digito_desde')):02d}"


def sincronizar_fechas(carpeta: Path | None = None):
	for archivo in sorted((carpeta or CARPETA).glob("*.json")):
		for fila in json.loads(archivo.read_text(encoding="utf-8")):
			_sincronizar_fila(fila)


def _sincronizar_fila(fila: dict):
	nombre = clave_fecha(fila)
	if frappe.db.exists("Fecha Tributaria", nombre):
		doc = frappe.get_doc("Fecha Tributaria", nombre)
		if doc.corregida_a_mano:
			return
		doc.update({c: fila[c] for c in CAMPOS})
	else:
		doc = frappe.get_doc({"doctype": "Fecha Tributaria", **{c: fila[c] for c in CAMPOS}})
	doc.flags.desde_sincronizacion = True
	doc.save(ignore_permissions=True)
