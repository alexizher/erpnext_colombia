from erpnext_colombia.vencimientos import catalogo, fechas


def configurar():
	catalogo.sincronizar_obligaciones()
	fechas.sincronizar_fechas()
