from erpnext_colombia.vencimientos import avisos, generacion


def diaria():
	generacion.generar()
	avisos.abrir_todos()
