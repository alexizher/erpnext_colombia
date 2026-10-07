from erpnext_colombia.estados_financieros.filas import MOVIMIENTO, api, blanco, cuentas, formula, prefijos, titulo

SITUACION_FINANCIERA = {
	"name": "CO Grupo 3 - Situación financiera",
	"report_type": "Balance Sheet",
	"rows": [
		titulo("ACTIVO"),
		cuentas("A11", "Efectivo y equivalentes al efectivo", prefijos("11")),
		cuentas("A13", "Deudores comerciales y otras cuentas por cobrar", prefijos("13")),
		cuentas("A14", "Inventarios", prefijos("14")),
		cuentas("A15", "Propiedad, planta y equipo", prefijos("15")),
		cuentas("A99", "Otros activos", prefijos(excluir=("11", "13", "14", "15"), raiz="Asset")),
		formula("ATOT", "Total activo", "A11 + A13 + A14 + A15 + A99", negrita=True),
		blanco(),
		titulo("PASIVO"),
		cuentas("P21", "Obligaciones financieras", prefijos("21"), invertir=True),
		cuentas("P22", "Proveedores y cuentas por pagar", prefijos("22", "23"), invertir=True),
		cuentas("P24", "Impuestos por pagar", prefijos("24"), invertir=True),
		cuentas("P25", "Obligaciones laborales", prefijos("25"), invertir=True),
		cuentas("P99", "Otros pasivos", prefijos(excluir=("21", "22", "23", "24", "25"), raiz="Liability"), invertir=True),
		formula("PTOT", "Total pasivo", "P21 + P22 + P24 + P25 + P99", negrita=True),
		blanco(),
		titulo("PATRIMONIO"),
		cuentas("K31", "Capital", prefijos("31"), invertir=True),
		# Ver estados_financieros.consultas: con o sin cierre anual, el resultado del ejercicio es el
		# del estado de resultados y lo demás va en resultados acumulados.
		cuentas("K36C", "Cuentas 36 y 37", prefijos("36", "37"), invertir=True, oculto=True),
		api("KUSC", "Resultados sin cerrar", "resultado_sin_cerrar", oculto=True),
		api("KRE", "Resultado del ejercicio", "resultado_del_periodo"),
		formula("K36", "Resultados acumulados", "K36C + KUSC - KRE"),
		cuentas("K99", "Otras partidas del patrimonio", prefijos(excluir=("31", "36", "37"), raiz="Equity"), invertir=True),
		formula("KTOT", "Total patrimonio", "K31 + K36 + KRE + K99", negrita=True),
		blanco(),
		formula("PKTOT", "Total pasivo y patrimonio", "PTOT + KTOT", negrita=True),
	],
}

RESULTADOS = {
	"name": "CO Grupo 3 - Resultados",
	"report_type": "Profit and Loss Statement",
	"rows": [
		cuentas("I4", "Ingresos", prefijos("4"), saldo=MOVIMIENTO, invertir=True),
		cuentas("C6", "Costos", prefijos("6", "7"), saldo=MOVIMIENTO),
		cuentas("G5", "Gastos", prefijos("5"), saldo=MOVIMIENTO),
		cuentas(
			"O9",
			"Otros ingresos y gastos",
			prefijos(excluir=("4", "5", "6", "7"), raiz=("Income", "Expense")),
			saldo=MOVIMIENTO,
			invertir=True,
		),
		blanco(),
		formula("UTIL", "Utilidad (pérdida) del periodo", "I4 - C6 - G5 + O9", negrita=True),
	],
}

PLANTILLAS = [SITUACION_FINANCIERA, RESULTADOS]
