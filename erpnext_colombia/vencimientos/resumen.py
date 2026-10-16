import frappe
from frappe import _
from frappe.utils import add_days, formatdate, getdate, today

from erpnext_colombia.vencimientos.generacion import generar
from erpnext_colombia.vencimientos.reglas import ABIERTOS, CONFIGURACION, dias_anticipacion

CAMPOS = ["name", "cliente", "cliente_nombre", "obligacion", "periodo", "fecha_vencimiento", "estado"]


def datos(hoy=None) -> dict:
	hoy = getdate(hoy or today())
	dias = dias_anticipacion()
	problemas = generar()
	vencidos = frappe.get_all(
		"Vencimiento",
		filters={"estado": ("in", ABIERTOS), "fecha_vencimiento": ("<", hoy)},
		fields=CAMPOS,
		order_by="fecha_vencimiento, cliente_nombre",
	)
	proximos = frappe.get_all(
		"Vencimiento",
		filters={"estado": ("in", ABIERTOS), "fecha_vencimiento": ("between", [hoy, add_days(hoy, dias)])},
		fields=CAMPOS,
		order_by="fecha_vencimiento, cliente_nombre",
	)
	vigilancia = frappe.get_all(
		"URL Vigilada DIAN",
		filters={"parent": CONFIGURACION},
		fields=["url", "ultima_revision", "ultimo_error"],
	)
	return {
		"hoy": hoy,
		"dias": dias,
		"vencidos": vencidos,
		"proximos": proximos,
		"problemas": problemas,
		"vigilancia": vigilancia,
	}


def destinatario() -> str:
	usuario = frappe.db.get_single_value(CONFIGURACION, "responsable")
	correo = frappe.db.get_value("User", usuario, "email") if usuario else None
	if not correo:
		frappe.log_error(
			title="Vencimientos: sin responsable",
			message=_(
				"La configuración de vencimientos no tiene responsable con correo; el resumen va al Administrator."
			),
		)
		correo = frappe.db.get_value("User", "Administrator", "email")
	return correo


def enviar(hoy=None) -> str:
	d = datos(hoy)
	correo = destinatario()
	frappe.sendmail(
		recipients=[correo],
		subject=_("Vencimientos: semana del {0}").format(formatdate(d["hoy"])),
		template="resumen_vencimientos",
		args=d,
	)
	return correo
