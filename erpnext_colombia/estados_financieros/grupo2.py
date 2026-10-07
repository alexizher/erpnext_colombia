from erpnext_colombia.estados_financieros.filas import (
	APERTURA,
	MOVIMIENTO,
	blanco,
	cuentas,
	formula,
	prefijos,
	titulo,
)

C, NC = "Corriente", "No corriente"
RESULTADO = prefijos(raiz=("Income", "Expense"))
DEPRECIACIONES = ("5160", "5165", "5260", "5265")
ACUMULADAS = ("1592", "1597", "1598", "1599", "1698", "1699")

SITUACION_FINANCIERA = {
	"name": "CO Grupo 2 - Situación financiera",
	"report_type": "Balance Sheet",
	"rows": [
		titulo("ACTIVO"),
		titulo("Activo corriente"),
		cuentas("AC11", "Efectivo y equivalentes al efectivo", prefijos("11", clasificacion=C)),
		cuentas("AC12", "Inversiones", prefijos("12", clasificacion=C)),
		cuentas("AC13", "Deudores comerciales y otras cuentas por cobrar", prefijos("13", clasificacion=C)),
		cuentas("AC14", "Inventarios", prefijos("14", clasificacion=C)),
		cuentas("AC99", "Otros activos corrientes", prefijos(excluir=("11", "12", "13", "14"), clasificacion=C, raiz="Asset")),
		formula("ACT", "Total activo corriente", "AC11 + AC12 + AC13 + AC14 + AC99", negrita=True),
		titulo("Activo no corriente"),
		cuentas("ANC12", "Inversiones de largo plazo", prefijos("12", clasificacion=NC)),
		cuentas("ANC13", "Deudores de largo plazo", prefijos("13", clasificacion=NC)),
		cuentas("ANC15", "Propiedad, planta y equipo", prefijos("15", clasificacion=NC)),
		cuentas("ANC16", "Activos intangibles", prefijos("16", clasificacion=NC)),
		cuentas("ANC99", "Otros activos no corrientes", prefijos(excluir=("12", "13", "15", "16"), clasificacion=NC, raiz="Asset")),
		formula("ANCT", "Total activo no corriente", "ANC12 + ANC13 + ANC15 + ANC16 + ANC99", negrita=True),
		formula("ATOT", "Total activo", "ACT + ANCT", negrita=True),
		blanco(),
		titulo("PASIVO"),
		titulo("Pasivo corriente"),
		cuentas("PC21", "Obligaciones financieras", prefijos("21", clasificacion=C), invertir=True),
		cuentas("PC22", "Proveedores", prefijos("22", clasificacion=C), invertir=True),
		cuentas("PC23", "Cuentas por pagar", prefijos("23", clasificacion=C), invertir=True),
		cuentas("PC24", "Impuestos, gravámenes y tasas", prefijos("24", clasificacion=C), invertir=True),
		cuentas("PC25", "Beneficios a empleados", prefijos("25", clasificacion=C), invertir=True),
		cuentas(
			"PC99",
			"Otros pasivos corrientes",
			prefijos(excluir=("21", "22", "23", "24", "25"), clasificacion=C, raiz="Liability"),
			invertir=True,
		),
		formula("PCT", "Total pasivo corriente", "PC21 + PC22 + PC23 + PC24 + PC25 + PC99", negrita=True),
		titulo("Pasivo no corriente"),
		cuentas("PNC21", "Obligaciones financieras de largo plazo", prefijos("21", clasificacion=NC), invertir=True),
		cuentas(
			"PNC99",
			"Otros pasivos no corrientes",
			prefijos(excluir=("21",), clasificacion=NC, raiz="Liability"),
			invertir=True,
		),
		formula("PNCT", "Total pasivo no corriente", "PNC21 + PNC99", negrita=True),
		formula("PTOT", "Total pasivo", "PCT + PNCT", negrita=True),
		blanco(),
		titulo("PATRIMONIO"),
		cuentas("K31", "Capital social", prefijos("31"), invertir=True),
		cuentas("K32", "Superávit de capital", prefijos("32"), invertir=True),
		cuentas("K33", "Reservas", prefijos("33"), invertir=True),
		cuentas("K34", "Revalorización del patrimonio", prefijos("34"), invertir=True),
		cuentas("K36", "Resultados de ejercicios anteriores", prefijos("36", "37"), invertir=True),
		cuentas("KRE", "Resultado del ejercicio", RESULTADO, invertir=True),
		cuentas("K38", "Superávit por valorizaciones", prefijos("38"), invertir=True),
		cuentas(
			"K99",
			"Otras partidas del patrimonio",
			prefijos(excluir=("31", "32", "33", "34", "36", "37", "38"), raiz="Equity"),
			invertir=True,
		),
		formula("KTOT", "Total patrimonio", "K31 + K32 + K33 + K34 + K36 + KRE + K38 + K99", negrita=True),
		blanco(),
		formula("PKTOT", "Total pasivo y patrimonio", "PTOT + KTOT", negrita=True),
	],
}

RESULTADO_INTEGRAL = {
	"name": "CO Grupo 2 - Resultado integral",
	"report_type": "Profit and Loss Statement",
	"rows": [
		cuentas("ING", "Ingresos de actividades ordinarias", prefijos("41"), saldo=MOVIMIENTO, invertir=True),
		cuentas("COS", "Costo de ventas", prefijos("6", "7"), saldo=MOVIMIENTO),
		formula("UB", "Utilidad bruta", "ING - COS", negrita=True),
		cuentas("GAD", "Gastos de administración", prefijos("51"), saldo=MOVIMIENTO),
		cuentas("GVE", "Gastos de ventas", prefijos("52"), saldo=MOVIMIENTO),
		cuentas("OIN", "Otros ingresos", prefijos("42", excluir=("4210",)), saldo=MOVIMIENTO, invertir=True),
		cuentas("OGA", "Otros gastos", prefijos("53", excluir=("5305",)), saldo=MOVIMIENTO),
		formula("UOP", "Resultado de actividades de operación", "UB - GAD - GVE + OIN - OGA", negrita=True),
		cuentas("IFI", "Ingresos financieros", prefijos("4210"), saldo=MOVIMIENTO, invertir=True),
		cuentas("GFI", "Costos financieros", prefijos("5305"), saldo=MOVIMIENTO),
		formula("UAI", "Resultado antes de impuestos", "UOP + IFI - GFI", negrita=True),
		cuentas("IMP", "Impuesto de renta", prefijos("54"), saldo=MOVIMIENTO),
		cuentas(
			"OTR",
			"Otras partidas de resultados",
			prefijos(excluir=("41", "42", "51", "52", "53", "54", "6", "7"), raiz=("Income", "Expense")),
			saldo=MOVIMIENTO,
			invertir=True,
		),
		formula("RES", "Resultado del periodo", "UAI - IMP + OTR", negrita=True),
	],
}

FLUJOS_DE_EFECTIVO = {
	"name": "CO Grupo 2 - Flujos de efectivo",
	"report_type": "Cash Flow",
	"rows": [
		titulo("Actividades de operación"),
		cuentas("F01", "Resultado del periodo", RESULTADO, saldo=MOVIMIENTO, invertir=True),
		cuentas("F02", "Depreciaciones y amortizaciones", prefijos(*DEPRECIACIONES), saldo=MOVIMIENTO),
		cuentas("F03", "(Aumento) disminución en deudores", prefijos("13"), saldo=MOVIMIENTO, invertir=True),
		cuentas("F04", "(Aumento) disminución en inventarios", prefijos("14"), saldo=MOVIMIENTO, invertir=True),
		cuentas("F05", "(Aumento) disminución en gastos pagados por anticipado", prefijos("17"), saldo=MOVIMIENTO, invertir=True),
		cuentas(
			"F06",
			"Aumento (disminución) en pasivos de operación",
			prefijos("22", "23", "24", "25", "26", "27", "28"),
			saldo=MOVIMIENTO,
			invertir=True,
		),
		formula("FOP", "Efectivo neto de actividades de operación", "F01 + F02 + F03 + F04 + F05 + F06", negrita=True),
		titulo("Actividades de inversión"),
		cuentas(
			"F11",
			"Inversiones y adquisición de propiedad, planta y equipo e intangibles",
			prefijos("12", "15", "16", "18", excluir=ACUMULADAS),
			saldo=MOVIMIENTO,
			invertir=True,
		),
		formula("FIN", "Efectivo neto de actividades de inversión", "F11", negrita=True),
		titulo("Actividades de financiación"),
		cuentas("F21", "Obligaciones financieras", prefijos("21"), saldo=MOVIMIENTO, invertir=True),
		cuentas(
			"F22",
			"Aportes de capital y otros movimientos del patrimonio",
			prefijos("31", "32", "33", "35"),
			saldo=MOVIMIENTO,
			invertir=True,
		),
		formula("FFI", "Efectivo neto de actividades de financiación", "F21 + F22", negrita=True),
		blanco(),
		formula("FNET", "Aumento (disminución) neto del efectivo", "FOP + FIN + FFI", negrita=True),
		cuentas("F31", "Efectivo al inicio del periodo", prefijos("11"), saldo=APERTURA),
		formula("F32", "Efectivo al final del periodo", "F31 + FNET", negrita=True),
	],
}


def _componente(codigo, texto, filtro):
	return [
		cuentas(f"{codigo}_I", f"{texto} - saldo inicial", filtro, saldo=APERTURA, invertir=True),
		cuentas(f"{codigo}_M", f"{texto} - movimiento del periodo", filtro, saldo=MOVIMIENTO, invertir=True),
		formula(f"{codigo}_F", f"{texto} - saldo final", f"{codigo}_I + {codigo}_M", negrita=True),
		blanco(),
	]


COMPONENTES = [
	("C31", "Capital", prefijos("31")),
	("C32", "Superávit de capital", prefijos("32")),
	("C33", "Reservas", prefijos("33")),
	("C34", "Revalorización del patrimonio", prefijos("34")),
	("C36", "Resultados de ejercicios anteriores", prefijos("36", "37")),
	("CRE", "Resultado del ejercicio", RESULTADO),
	("C38", "Superávit por valorizaciones", prefijos("38")),
	("C99", "Otras partidas del patrimonio", prefijos(excluir=("31", "32", "33", "34", "36", "37", "38"), raiz="Equity")),
]

CAMBIOS_EN_EL_PATRIMONIO = {
	"name": "CO Grupo 2 - Cambios en el patrimonio",
	"report_type": "Custom Financial Statement",
	"rows": [fila for codigo, texto, filtro in COMPONENTES for fila in _componente(codigo, texto, filtro)]
	+ [formula("CTOT", "Total patrimonio al final", " + ".join(f"{c}_F" for c, _t, _f in COMPONENTES), negrita=True)],
}

PLANTILLAS = [SITUACION_FINANCIERA, RESULTADO_INTEGRAL, FLUJOS_DE_EFECTIVO, CAMBIOS_EN_EL_PATRIMONIO]
