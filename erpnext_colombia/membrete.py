import frappe
from frappe.utils import escape_html

CERTIFICACION = (
	"Los suscritos representante legal y contador certificamos que hemos verificado previamente "
	"las afirmaciones contenidas en estos estados financieros, conforme al artículo 37 de la "
	"Ley 222 de 1995, y que las mismas se han tomado fielmente de los libros."
)


def nombre_membrete(empresa: str) -> str:
	return f"Estados financieros - {empresa}"


def _firma(nombre, cargo, detalle):
	if not nombre:
		return ""
	return (
		'<td style="width:33%;text-align:center;padding-top:40px;vertical-align:top">'
		'<div style="border-top:1px solid #000;margin:0 12px;padding-top:4px">'
		f"<strong>{escape_html(nombre)}</strong><br>{cargo}<br>{escape_html(detalle or '')}"
		"</div></td>"
	)


def _tarjeta(numero):
	return f"T.P. {numero}" if numero else ""


def generar_membrete(empresa: str) -> str:
	c = frappe.get_doc("Company", empresa)
	logo = f'<img src="{escape_html(c.company_logo)}" style="max-height:60px"><br>' if c.company_logo else ""
	encabezado = (
		f'<div style="text-align:center">{logo}<strong>{escape_html(c.company_name)}</strong>'
		f"<br>NIT {escape_html(c.tax_id or '')}</div>"
	)
	firmas = "".join(
		[
			_firma(c.co_representante_legal, "Representante legal", c.co_representante_legal_documento),
			_firma(c.co_contador, "Contador", _tarjeta(c.co_contador_tarjeta_profesional)),
			_firma(c.co_revisor_fiscal, "Revisor fiscal", _tarjeta(c.co_revisor_fiscal_tarjeta_profesional)),
		]
	)
	pie = f'<p style="font-size:9px">{CERTIFICACION}</p><table style="width:100%"><tr>{firmas}</tr></table>'

	nombre = nombre_membrete(empresa)
	lh = frappe.get_doc("Letter Head", nombre) if frappe.db.exists("Letter Head", nombre) else frappe.new_doc("Letter Head")
	lh.update(
		{
			"letter_head_name": nombre,
			"source": "HTML",
			"content": encabezado,
			"footer_source": "HTML",
			"footer": pie,
			"is_default": 0,
		}
	)
	lh.flags.ignore_permissions = True
	lh.save()
	return lh.name


def al_guardar_empresa(doc, method=None):
	if doc.get("co_tercero") or doc.get("co_contador"):
		generar_membrete(doc.name)
