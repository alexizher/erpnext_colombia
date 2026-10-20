from erpnext_colombia.honorarios.facturacion import Facturador


def diaria():
	Facturador.desde_configuracion().facturar_si_toca()
