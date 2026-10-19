import hashlib
import json

import frappe
import requests
from bs4 import BeautifulSoup
from frappe import _
from frappe.utils import now_datetime

from erpnext_colombia.vencimientos.reglas import CONFIGURACION
from erpnext_colombia.vencimientos.resumen import correos_de_alerta, destinatarios

# Contenido principal de las páginas SharePoint de la DIAN (estable entre visitas; el contador de visitas queda fuera).
SELECTOR_PRINCIPAL = '[id$="RichHtmlField"]'
AGENTE = "Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0"


def huella(html: str) -> tuple[str, list[str]]:
	"""Huella de una página: solo los PDF que enlaza su contenido principal.

	El texto no cuenta: la DIAN agrega cada mes un enlace a "los vencimientos de <mes>" sin cambiar fechas.
	Lo que indica un cambio es un PDF nuevo, quitado o reemplazado.
	"""
	soup = BeautifulSoup(html, "html.parser")
	principal = soup.select_one(SELECTOR_PRINCIPAL) or soup.body or soup
	enlaces = sorted(
		{
			a["href"]
			for a in principal.find_all("a", href=True)
			if a["href"].lower().split("?")[0].endswith(".pdf")
		}
	)
	return hashlib.sha256("\n".join(enlaces).encode()).hexdigest(), enlaces


def _leer(url: str) -> tuple[str, list[str]]:
	r = requests.get(url, headers={"User-Agent": AGENTE}, timeout=30)
	r.raise_for_status()
	# La DIAN a veces sirve el PDF como application/octet-stream: se reconoce también por su firma.
	if r.content.startswith(b"%PDF") or "pdf" in (r.headers.get("Content-Type") or "").lower():
		return hashlib.sha256(r.content).hexdigest(), []
	return huella(r.text)


def revisar():
	conf = frappe.get_single(CONFIGURACION)
	for fila in conf.urls_vigiladas:
		fila.ultima_revision = now_datetime()
		try:
			nueva, enlaces = _leer(fila.url)
		except Exception as e:
			fila.ultimo_error = str(e)[:280]
			_avisar(conf, _("No se pudo revisar la DIAN"), url=fila.url, error=fila.ultimo_error)
			continue
		fila.ultimo_error = None
		if fila.ultima_huella and fila.ultima_huella != nueva:
			previos = set(json.loads(fila.ultimos_enlaces or "[]"))
			_avisar(
				conf,
				_("Cambió una página de calendario de la DIAN"),
				url=fila.url,
				nuevos=sorted(set(enlaces) - previos),
				quitados=sorted(previos - set(enlaces)),
			)
		fila.ultima_huella = nueva
		fila.ultimos_enlaces = json.dumps(enlaces)
	conf.save(ignore_permissions=True)


def _avisar(conf, asunto, **args):
	correos = correos_de_alerta() or destinatarios()
	if not correos:
		return
	frappe.sendmail(
		recipients=correos, subject=asunto, template="alerta_dian", args={"asunto": asunto, **args}
	)
