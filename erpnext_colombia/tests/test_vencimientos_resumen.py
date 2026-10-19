import frappe
from frappe.tests import IntegrationTestCase

from erpnext_colombia.tests.utils import (
	cliente_con,
	cuenta_correo_prueba,
	fecha_prueba,
	obligacion_prueba,
	vencimientos_de,
)
from erpnext_colombia.vencimientos import resumen
from erpnext_colombia.vencimientos.generacion import generar


class TestResumen(IntegrationTestCase):
	def setUp(self):
		fecha_prueba("Septiembre de 2030", "2030-10-10", desde=0, hasta=9)
		fecha_prueba("Octubre de 2030", "2030-11-12", desde=0, hasta=9)
		fecha_prueba("Noviembre de 2030", "2030-12-10", desde=0, hasta=9)
		frappe.db.set_single_value(
			"Configuracion de Vencimientos", {"responsable": "Administrator", "dias_anticipacion": 15}
		)
		frappe.db.set_value("User", "Administrator", "email", "admin@example.com")
		cuenta_correo_prueba()
		# Un cliente por prueba: los datos de una prueba quedan para las siguientes de la clase.
		numero = (
			f"9005006{sorted(n for n in dir(self) if n.startswith('test_')).index(self._testMethodName):02d}"
		)
		self.c = cliente_con(
			numero, f"Res {numero} S.A.S.", [{"obligacion": obligacion_prueba(), "desde": "2030-09-01"}]
		)
		generar(cliente=self.c, anio=2030)

	def _mios(self, filas):
		return [f.periodo for f in filas if f.cliente == self.c]

	def test_bloques(self):
		d = resumen.datos(hoy="2030-11-01")
		self.assertEqual(self._mios(d["vencidos"]), ["Septiembre de 2030"])
		self.assertEqual(self._mios(d["proximos"]), ["Octubre de 2030"])

	def test_presentado_no_aparece(self):
		v = frappe.get_doc("Vencimiento", vencimientos_de(self.c, periodo="Septiembre de 2030")[0].name)
		v.estado = "Presentada"
		v.save()
		self.assertEqual(self._mios(resumen.datos(hoy="2030-11-01")["vencidos"]), [])

	def test_se_envia_aunque_no_haya_nada(self):
		frappe.db.delete("Email Queue")
		resumen.enviar(hoy="2035-01-07")
		self.assertEqual(frappe.db.count("Email Queue"), 1)

	def test_resumen_sin_responsable_va_a_los_correos_de_alerta(self):
		frappe.db.set_single_value(
			"Configuracion de Vencimientos",
			{"responsable": None, "correos_alerta_dian": "alerta1@repolite.link\nalerta2@repolite.link"},
		)
		self.assertEqual(resumen.destinatarios(), ["alerta1@repolite.link", "alerta2@repolite.link"])

	def test_resumen_sin_a_quien_no_sale_a_un_correo_de_ejemplo(self):
		frappe.db.set_single_value(
			"Configuracion de Vencimientos", {"responsable": None, "correos_alerta_dian": None}
		)
		frappe.db.delete("Email Queue")
		self.assertEqual(resumen.enviar(hoy="2030-11-01"), [])
		self.assertEqual(frappe.db.count("Email Queue"), 0)
		self.assertTrue(
			frappe.db.exists("Error Log", {"method": ("like", "%Vencimientos: sin responsable%")})
		)

	def test_cero_dias_de_anticipacion_se_respeta(self):
		from erpnext_colombia.vencimientos.reglas import dias_anticipacion

		frappe.db.set_single_value("Configuracion de Vencimientos", "dias_anticipacion", 0)
		self.assertEqual(dias_anticipacion(), 0)
