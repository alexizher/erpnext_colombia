import json
from unittest.mock import MagicMock, patch

import frappe
import requests
from frappe.tests import IntegrationTestCase

from erpnext_colombia.tests.utils import cuenta_correo_prueba
from erpnext_colombia.vencimientos import vigilancia

PAGINA = """<html><body><div id="ctl00_PlaceHolderMain_ctl01__ControlWrapper_RichHtmlField">
<p>Calendario 2026</p>{texto}<a href="/Calendarios/Calendario_Tributario_2026.pdf">PDF</a>{extra}</div>
<div id="counter">{contador}</div><script>var t={contador};</script></body></html>"""


def respuesta(cuerpo, status=200, tipo="text/html; charset=utf-8"):
	r = MagicMock()
	r.status_code = status
	r.headers = {"Content-Type": tipo}
	if isinstance(cuerpo, bytes):
		r.content = cuerpo
		r.text = cuerpo.decode("latin-1")
	else:
		r.text = cuerpo
		r.content = cuerpo.encode()
	r.raise_for_status.side_effect = (
		None if status == 200 else requests.HTTPError(f"{status} Client Error: Forbidden")
	)
	return r


def pagina(contador="1", texto="", extra=""):
	return PAGINA.format(contador=contador, texto=texto, extra=extra)


class TestVigilancia(IntegrationTestCase):
	def setUp(self):
		cuenta_correo_prueba()
		conf = frappe.get_single("Configuracion de Vencimientos")
		conf.set("urls_vigiladas", [{"url": "https://www.dian.gov.co/prueba"}])
		conf.correos_alerta_dian = "alexizher@gmail.com"
		conf.save()
		frappe.db.delete("Email Queue")

	def _fila(self):
		return frappe.get_single("Configuracion de Vencimientos").urls_vigiladas[0]

	def _correos(self):
		return frappe.get_all("Email Queue", pluck="message")

	def test_huella_ignora_contador_y_scripts(self):
		self.assertEqual(vigilancia.huella(pagina("8022710"))[0], vigilancia.huella(pagina("8022711"))[0])

	def test_huella_ignora_texto_sin_pdf_nuevo(self):
		# La DIAN agrega cada mes "Conozca aquí los vencimientos de ..."; eso no es un cambio de fechas.
		otra = pagina(texto="<p>Conozca aquí los vencimientos de noviembre de 2026</p>")
		self.assertEqual(vigilancia.huella(pagina())[0], vigilancia.huella(otra)[0])

	def test_primera_lectura_guarda_sin_avisar(self):
		with patch("requests.get", return_value=respuesta(pagina())):
			vigilancia.revisar()
		self.assertTrue(self._fila().ultima_huella)
		self.assertEqual(self._correos(), [])

	def test_sin_cambio_no_avisa(self):
		with patch("requests.get", return_value=respuesta(pagina())):
			vigilancia.revisar()
			vigilancia.revisar()
		self.assertEqual(self._correos(), [])

	def test_pdf_nuevo_avisa_con_el_enlace(self):
		with patch("requests.get", return_value=respuesta(pagina())):
			vigilancia.revisar()
		nuevo = pagina(extra='<a href="/Calendarios/Calendario_Tributario_2027.pdf">2027</a>')
		with patch("requests.get", return_value=respuesta(nuevo)):
			vigilancia.revisar()
		correos = self._correos()
		self.assertEqual(len(correos), 1)
		self.assertIn("Calendario_Tributario_2027.pdf", correos[0])
		self.assertIn("/Calendarios/Calendario_Tributario_2027.pdf", json.loads(self._fila().ultimos_enlaces))

	def test_pdf_modificado_avisa(self):
		with patch("requests.get", return_value=respuesta(b"%PDF-1.7 version 1", tipo="application/pdf")):
			vigilancia.revisar()
		with patch("requests.get", return_value=respuesta(b"%PDF-1.7 version 2", tipo="application/pdf")):
			vigilancia.revisar()
		self.assertEqual(len(self._correos()), 1)

	def test_403_avisa_y_queda_en_la_fila(self):
		with patch("requests.get", return_value=respuesta("", status=403)):
			vigilancia.revisar()
		self.assertIn("403", self._fila().ultimo_error)
		self.assertEqual(len(self._correos()), 1)
		self.assertFalse(self._fila().ultima_huella)
