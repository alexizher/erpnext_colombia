from erpnext_colombia.vencimientos import avisos, generacion, resumen


def diaria():
	generacion.generar()
	avisos.abrir_todos()


def resumen_semanal():
	resumen.enviar()
