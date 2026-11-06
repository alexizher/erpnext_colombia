"""Tipo de contribuyente y responsabilidades fiscales del tercero.

La lista de tipos sigue la clasificación usual de los programas contables en Colombia. Las
responsabilidades son las que pide la factura electrónica de la DIAN; el tipo las propone y el
contador las puede cambiar a mano.
"""

import frappe

PJ = "Persona jurídica"
PN = "Persona natural"
AMBAS = frozenset({PJ, PN})

TERCERO_DEL_EXTERIOR = "Tercero del Exterior"

# (tipo, naturalezas en las que se ofrece, responsabilidades que propone)
TIPOS = (
	("Entidades Sin Ánimo de Lucro", {PJ}, ()),
	("Grande Contribuyente Autorretenedor", {PJ}, ("O-13", "O-15")),
	("Grande Contribuyente No Autorretenedor", {PJ}, ("O-13",)),
	("Instituciones del Estado Públicos y Otros", {PJ}, ()),
	("Persona Jurídica", {PJ}, ()),
	("Persona Jurídica Autorretenedor", {PJ}, ("O-15",)),
	("Persona Natural Autorretenedor", {PN}, ("O-15",)),
	("Persona Natural No Responsable del IVA", {PN}, ()),
	("Persona Natural o Jurídica Ley 1429", AMBAS, ()),
	("Persona Natural Responsable del IVA", {PN}, ()),
	("Persona Natural Responsable del IVA Agente Retenedor", {PN}, ("O-23",)),
	("Proveedor Sociedades de Comercio Internacional", {PJ}, ()),
	("Régimen Simple de Tributación Persona Jurídica", {PJ}, ("O-47",)),
	("Régimen Simple de Tributación Persona Natural", {PN}, ("O-47",)),
	(TERCERO_DEL_EXTERIOR, AMBAS, ()),
)

NATURALEZAS = {tipo: naturalezas for tipo, naturalezas, _ in TIPOS}
RESPONSABILIDADES_DEL_TIPO = {tipo: responsabilidades for tipo, _, responsabilidades in TIPOS}

# Código DIAN -> campo Check del Tercero.
RESPONSABILIDADES = {
	"O-13": "rf_gran_contribuyente",
	"O-15": "rf_autorretenedor",
	"O-23": "rf_agente_retencion_iva",
	"O-47": "rf_regimen_simple",
	"R-99-PN": "rf_no_aplica",
}
NO_APLICA = "R-99-PN"


def tipos_de(naturaleza: str) -> list[str]:
	return [tipo for tipo, naturalezas, _ in TIPOS if naturaleza in naturalezas]


def tipo_por_defecto(naturaleza: str, del_exterior: bool) -> str:
	if del_exterior:
		return TERCERO_DEL_EXTERIOR
	return "Persona Jurídica" if naturaleza == PJ else "Persona Natural Responsable del IVA"


def aplica_a(tipo: str, naturaleza: str) -> bool:
	return naturaleza in NATURALEZAS.get(tipo, ())


def responsabilidades_de(tipo: str) -> dict[str, int]:
	"""Valor de cada casilla de responsabilidad que propone el tipo. Sin ninguna, R-99-PN."""
	codigos = set(RESPONSABILIDADES_DEL_TIPO.get(tipo, ())) or {NO_APLICA}
	return {campo: int(codigo in codigos) for codigo, campo in RESPONSABILIDADES.items()}


@frappe.whitelist()
def opciones(naturaleza: str, tipo: str | None = None) -> dict:
	"""Para el formulario: los tipos de la naturaleza y las responsabilidades que propone el tipo."""
	return {"tipos": tipos_de(naturaleza), "responsabilidades": responsabilidades_de(tipo) if tipo else {}}
