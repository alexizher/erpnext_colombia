from erpnext_colombia.estados_financieros.filas import (
	APERTURA,
	MOVIMIENTO,
	api,
	blanco,
	cuentas,
	formula,
	prefijos,
	titulo,
)

C, NC = "Corriente", "No corriente"
RESULTADO = prefijos(raiz=("Income", "Expense"))
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
		# Ver estados_financieros.consultas: con o sin cierre anual, el resultado del ejercicio es el
		# del estado de resultados y lo demás va en ejercicios anteriores.
		cuentas("K36C", "Cuentas 36 y 37", prefijos("36", "37"), invertir=True, oculto=True),
		api("KUSC", "Resultados sin cerrar", "resultado_sin_cerrar", oculto=True),
		api("KRE", "Resultado del ejercicio", "resultado_del_periodo"),
		formula("K36", "Resultados de ejercicios anteriores", "K36C + KUSC - KRE"),
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

OTRAS_CLASES = tuple(f"1{d}" for d in range(1, 10)) + tuple(f"2{d}" for d in range(1, 10)) + ("8", "9")

FLUJOS_DE_EFECTIVO = {
	"name": "CO Grupo 2 - Flujos de efectivo",
	"report_type": "Cash Flow",
	"rows": [
		titulo("Actividades de operación"),
		cuentas("F01", "Resultado del periodo", RESULTADO, saldo=MOVIMIENTO, invertir=True),
		# Se toman de las contrapartidas acumuladas (1592, 1597...) y no del gasto: así cuadran también
		# las bajas de activos y la amortización de diferidos, que se abona directo a la 17.
		cuentas("F02", "Depreciaciones, amortizaciones y deterioro", prefijos(*ACUMULADAS), saldo=MOVIMIENTO, invertir=True),
		cuentas("F03", "(Aumento) disminución en deudores", prefijos("13"), saldo=MOVIMIENTO, invertir=True),
		cuentas("F04", "(Aumento) disminución en inventarios", prefijos("14"), saldo=MOVIMIENTO, invertir=True),
		cuentas("F05", "(Aumento) disminución en diferidos y pagos anticipados", prefijos("17"), saldo=MOVIMIENTO, invertir=True),
		cuentas(
			"F06",
			"Aumento (disminución) en pasivos de operación",
			prefijos("22", "23", "24", "25", "26", "27", "28"),
			saldo=MOVIMIENTO,
			invertir=True,
		),
		cuentas(
			"F07",
			"Otras partidas de activo y pasivo",
			prefijos(excluir=OTRAS_CLASES, raiz=("Asset", "Liability")),
			saldo=MOVIMIENTO,
			invertir=True,
		),
		formula("FOP", "Efectivo neto de actividades de operación", "F01 + F02 + F03 + F04 + F05 + F06 + F07", negrita=True),
		titulo("Actividades de inversión"),
		cuentas(
			"F11",
			"Inversiones y propiedad, planta y equipo, intangibles y otros activos",
			prefijos("12", "15", "16", "18", "19", excluir=ACUMULADAS),
			saldo=MOVIMIENTO,
			invertir=True,
		),
		formula("FIN", "Efectivo neto de actividades de inversión", "F11", negrita=True),
		titulo("Actividades de financiación"),
		cuentas("F21", "Obligaciones financieras y bonos", prefijos("21", "29"), saldo=MOVIMIENTO, invertir=True),
		cuentas(
			"F22",
			"Aportes, reservas y otros movimientos del patrimonio",
			prefijos(excluir=("36", "37"), raiz="Equity"),
			saldo=MOVIMIENTO,
			invertir=True,
		),
		api("F23", "Movimientos de resultados acumulados", "movimiento_resultados_acumulados_sin_cierre"),
		formula("FFI", "Efectivo neto de actividades de financiación", "F21 + F22 + F23", negrita=True),
		blanco(),
		formula("FNET", "Aumento (disminución) neto del efectivo", "FOP + FIN + FFI", negrita=True),
		# En reportes sin valores acumulados el motor devuelve como "Closing Balance" el movimiento del
		# año; el saldo final se arma con la apertura más el movimiento real de la caja.
		cuentas("F31", "Efectivo al inicio del periodo", prefijos("11"), saldo=APERTURA),
		cuentas("F3M", "Movimiento de la caja", prefijos("11"), saldo=MOVIMIENTO, oculto=True),
		formula("F32", "Efectivo al final del periodo", "F31 + F3M", negrita=True),
		formula("F33", "Diferencia por conciliar", "F3M - FNET"),
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
	("C38", "Superávit por valorizaciones", prefijos("38")),
	("C99", "Otras partidas del patrimonio", prefijos(excluir=("31", "32", "33", "34", "36", "37", "38"), raiz="Equity")),
]

RESULTADOS_ACUMULADOS = prefijos("36", "37")

# Resultados: cuentas 36 y 37 más lo que aún no pasó a patrimonio con un cierre anual.
COMPONENTE_RESULTADOS = [
	cuentas("CR_IA", "Cuentas 36 y 37 al inicio", RESULTADOS_ACUMULADOS, saldo=APERTURA, invertir=True, oculto=True),
	api("CR_IU", "Resultados sin cerrar al inicio", "resultado_sin_cerrar_al_inicio", oculto=True),
	formula("CR_I", "Resultados acumulados - saldo inicial", "CR_IA + CR_IU"),
	api("CR_E", "Resultado del ejercicio", "resultado_del_periodo", nivel=2),
	cuentas("CR_MA", "Movimiento de las cuentas 36 y 37", RESULTADOS_ACUMULADOS, saldo=MOVIMIENTO, invertir=True, oculto=True),
	{**formula("CR_FA", "Cuentas 36 y 37 al final", "CR_IA + CR_MA"), "hidden_calculation": 1},
	api("CR_FU", "Resultados sin cerrar al final", "resultado_sin_cerrar", oculto=True),
	formula("CR_F", "Resultados acumulados - saldo final", "CR_FA + CR_FU", negrita=True),
	formula("CR_M", "Resultados acumulados - movimiento del periodo", "CR_F - CR_I"),
	blanco(),
]

CAMBIOS_EN_EL_PATRIMONIO = {
	"name": "CO Grupo 2 - Cambios en el patrimonio",
	"report_type": "Custom Financial Statement",
	"rows": [fila for codigo, texto, filtro in COMPONENTES for fila in _componente(codigo, texto, filtro)]
	+ COMPONENTE_RESULTADOS
	+ [
		formula(
			"CTOT",
			"Total patrimonio al final",
			" + ".join([f"{c}_F" for c, _t, _f in COMPONENTES] + ["CR_F"]),
			negrita=True,
		)
	],
}

PLANTILLAS = [SITUACION_FINANCIERA, RESULTADO_INTEGRAL, FLUJOS_DE_EFECTIVO, CAMBIOS_EN_EL_PATRIMONIO]
