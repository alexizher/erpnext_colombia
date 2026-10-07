import re

PESOS_DIAN = (3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71)
TIPOS_ALFANUMERICOS = ("41", "42")


def codigo_tipo(tipo: str) -> str:
	return (tipo or "")[:2]


def limpiar_numero(numero: str, tipo: str) -> str:
	numero = (numero or "").strip()
	if codigo_tipo(tipo) in TIPOS_ALFANUMERICOS:
		return re.sub(r"[\s.\-]", "", numero).upper()
	return re.sub(r"\D", "", numero)


def digito_verificacion(numero: str) -> int:
	"""Dígito de verificación del NIT con el algoritmo de la DIAN (módulo 11)."""
	suma = sum(int(c) * PESOS_DIAN[i] for i, c in enumerate(reversed(numero)))
	residuo = suma % 11
	return residuo if residuo in (0, 1) else 11 - residuo
