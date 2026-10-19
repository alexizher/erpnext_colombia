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


def correos_de_alerta() -> list[str]:
	texto = frappe.db.get_single_value(CONFIGURACION, "correos_alerta_dian") or ""
	return [c.strip() for c in texto.splitlines() if c.strip()]


def destinatarios() -> list[str]:
	"""El responsable; si no tiene correo, los correos de alerta de la DIAN. Sin ninguno, nadie: el
	correo del Administrator suele ser el de ejemplo y el resumen se perdería sin que nadie lo note."""
	usuario = frappe.db.get_single_value(CONFIGURACION, "responsable")
	correo = frappe.db.get_value("User", usuario, "email") if usuario else None
	if correo:
		return [correo]
	if alerta := correos_de_alerta():
		return alerta
	frappe.log_error(
		title="Vencimientos: sin responsable",
		message=_(
			"La configuración de vencimientos no tiene responsable con correo ni correos de alerta; no se envió."
		),
	)
	return []


def enviar(hoy=None) -> list[str]:
	d = datos(hoy)
	correos = destinatarios()
	if correos:
		frappe.sendmail(
			recipients=correos,
			subject=_("Vencimientos: semana del {0}").format(formatdate(d["hoy"])),
			template="resumen_vencimientos",
			args=d,
		)
	return correos
