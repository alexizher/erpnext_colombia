import frappe

from erpnext_colombia.vencimientos import catalogo, fechas

URLS_INICIALES = [
	"https://www.dian.gov.co/Paginas/CalendarioTributario.aspx",
	"https://www.dian.gov.co/Calendarios/Calendario_Tributario_2026.pdf",
]


def configurar():
	catalogo.sincronizar_obligaciones()
	fechas.sincronizar_fechas()
	configurar_urls()


def configurar_urls():
	conf = frappe.get_single("Configuracion de Vencimientos")
	if conf.urls_vigiladas:
		return
	for url in URLS_INICIALES:
		conf.append("urls_vigiladas", {"url": url})
	conf.save(ignore_permissions=True)
