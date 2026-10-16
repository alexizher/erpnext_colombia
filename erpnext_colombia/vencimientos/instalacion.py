import frappe

from erpnext_colombia.vencimientos import catalogo, fechas
from erpnext_colombia.vencimientos.reglas import ESTADOS

URLS_INICIALES = [
	"https://www.dian.gov.co/Paginas/CalendarioTributario.aspx",
	"https://www.dian.gov.co/Calendarios/Calendario_Tributario_2026.pdf",
]


def configurar():
	catalogo.sincronizar_obligaciones()
	fechas.sincronizar_fechas()
	configurar_urls()
	crear_kanban()


def configurar_urls():
	conf = frappe.get_single("Configuracion de Vencimientos")
	if conf.urls_vigiladas:
		return
	for url in URLS_INICIALES:
		conf.append("urls_vigiladas", {"url": url})
	conf.save(ignore_permissions=True)


def crear_kanban():
	if frappe.db.exists("Kanban Board", "Vencimientos"):
		return
	frappe.get_doc(
		{
			"doctype": "Kanban Board",
			"kanban_board_name": "Vencimientos",
			"reference_doctype": "Vencimiento",
			"field_name": "estado",
			"columns": [{"column_name": e, "status": "Active"} for e in ESTADOS],
		}
	).insert(ignore_permissions=True)
