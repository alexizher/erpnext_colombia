import json

CIERRE = "Closing Balance"
APERTURA = "Opening Balance"
MOVIMIENTO = "Period Movement (Debits - Credits)"


def titulo(texto):
	return {"data_source": "Blank Line", "display_name": texto, "bold_text": 1, "indentation_level": 0}


def blanco():
	return {"data_source": "Blank Line"}


def cuentas(codigo, texto, filtro, saldo=CIERRE, invertir=False, nivel=1):
	return {
		"reference_code": codigo,
		"display_name": texto,
		"data_source": "Account Data",
		"balance_type": saldo,
		"calculation_formula": filtro,
		"reverse_sign": 1 if invertir else 0,
		"indentation_level": nivel,
		"hide_when_empty": 0,
	}


def formula(codigo, texto, expresion, nivel=1, negrita=False):
	return {
		"reference_code": codigo,
		"display_name": texto,
		"data_source": "Calculated Amount",
		"calculation_formula": expresion,
		"indentation_level": nivel,
		"bold_text": 1 if negrita else 0,
	}


def prefijos(*incluir, excluir=(), clasificacion=None, raiz=None):
	"""Filtro de cuentas por prefijo de número. Sin prefijos a incluir, filtra solo por raíz."""
	condiciones = []
	if incluir:
		opciones = [["account_number", "like", f"{p}%"] for p in incluir]
		condiciones.append(opciones[0] if len(opciones) == 1 else {"or": opciones})
	# En SQL, NULL NOT LIKE '11%' no es verdadero: una cuenta sin número quedaría fuera de los "Otros".
	condiciones += [
		{"or": [["account_number", "not like", f"{p}%"], ["account_number", "is", "not set"]]} for p in excluir
	]
	if clasificacion:
		condiciones.append(["co_clasificacion_niif", "=", clasificacion])
	if raiz:
		condiciones.append(["root_type", "in", list(raiz)] if isinstance(raiz, tuple) else ["root_type", "=", raiz])
	filtro = condiciones[0] if len(condiciones) == 1 else {"and": condiciones}
	return json.dumps(filtro, ensure_ascii=False)
