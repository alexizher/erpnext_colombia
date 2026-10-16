import json
from collections import defaultdict

from frappe.tests import IntegrationTestCase

from erpnext_colombia.vencimientos import catalogo
from erpnext_colombia.vencimientos.fechas import CAMPOS, CARPETA

PERIODOS_ESPERADOS = {"Retención en la fuente": 12, "IVA bimestral": 6, "IVA cuatrimestral": 3}


class TestFechas2026(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.filas = json.loads((CARPETA / "2026.json").read_text(encoding="utf-8"))

	def test_campos_completos(self):
		for f in self.filas:
			self.assertEqual(set(f), set(CAMPOS), f)
			self.assertTrue(f["fuente"], f)

	def test_obligaciones_del_catalogo(self):
		nombres = {o["nombre"] for o in catalogo.OBLIGACIONES}
		for f in self.filas:
			self.assertIn(f["obligacion"], nombres)

	def test_anio_es_el_de_la_fecha(self):
		# El calendario 2026 de la DIAN cubre los periodos de 2026: los de diciembre vencen en enero de 2027.
		for f in self.filas:
			self.assertEqual(f["anio"], int(f["fecha"][:4]), f)
			self.assertTrue("2026-01-01" <= f["fecha"] <= "2027-01-31", f)

	def test_ninguna_cae_en_fin_de_semana(self):
		import datetime

		for f in self.filas:
			self.assertLess(datetime.date.fromisoformat(f["fecha"]).weekday(), 5, f)

	def test_digitos_sin_huecos_ni_cruces(self):
		grupos = defaultdict(list)
		for f in self.filas:
			grupos[(f["obligacion"], f["periodo"], f["segmento"])].append(f)
		for clave, filas in grupos.items():
			cifras = {f["cifras"] for f in filas}
			self.assertEqual(len(cifras), 1, clave)
			maximo = 9 if cifras == {"1"} else 99
			siguiente = 0
			for f in sorted(filas, key=lambda x: x["digito_desde"]):
				self.assertEqual(
					f["digito_desde"], siguiente, f"hueco o cruce en {clave} antes de {f['digito_desde']}"
				)
				self.assertGreaterEqual(f["digito_hasta"], f["digito_desde"], clave)
				siguiente = f["digito_hasta"] + 1
			self.assertEqual(siguiente, maximo + 1, f"faltan dígitos al final en {clave}")

	def test_periodos_completos(self):
		periodos = defaultdict(set)
		for f in self.filas:
			periodos[f["obligacion"]].add(f["periodo"])
		for obligacion, n in PERIODOS_ESPERADOS.items():
			self.assertEqual(len(periodos[obligacion]), n, obligacion)
		# La exógena no está en el calendario: la DIAN la fija por resolución aparte.
		for o in catalogo.OBLIGACIONES:
			if o["nombre"] != "Exógena":
				self.assertTrue(periodos[o["nombre"]], f"sin fechas: {o['nombre']}")

	def test_ajuste_del_dia_civico(self):
		self.assertFalse(
			[f for f in self.filas if f["fecha"] == "2026-04-17"], "quedó una fecha el 17 de abril"
		)
