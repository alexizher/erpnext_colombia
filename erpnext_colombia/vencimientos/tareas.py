from erpnext_colombia.vencimientos import avisos, generacion, resumen, vigilancia


def diaria():
	generacion.generar()
	avisos.abrir_todos()


def resumen_semanal():
	resumen.enviar()


def vigilancia_semanal():
	vigilancia.revisar()
