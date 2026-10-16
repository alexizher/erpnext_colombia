from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today

from erpnext_colombia.tests.utils import cliente_con, fecha_prueba, obligacion_prueba, vencimientos_de
from erpnext_colombia.vencimientos.avisos import abrir_todos
from erpnext_colombia.vencimientos.generacion import generar


def todos_abiertos(vencimiento):
	return frappe.get_all(
		"ToDo",
		filters={"reference_type": "Vencimiento", "reference_name": vencimiento, "status": "Open"},
		pluck="allocated_to",
	)


class TestAvisos(IntegrationTestCase):
	def setUp(self):
		fecha_prueba("Julio de 2030", "2030-08-12", desde=0, hasta=9)
		fecha_prueba("Agosto de 2030", "2030-09-10", desde=0, hasta=9)
		frappe.db.set_single_value(
			"Configuracion de Vencimientos", {"responsable": "Administrator", "dias_anticipacion": 15}
		)
		# Un cliente por prueba: los datos de una prueba quedan para las siguientes de la clase.
		numero = (
			f"9004005{sorted(n for n in dir(self) if n.startswith('test_')).index(self._testMethodName):02d}"
		)
		self.c = cliente_con(
			numero, f"Avi {numero} S.A.S.", [{"obligacion": obligacion_prueba(), "desde": "2030-07-01"}]
		)
		generar(cliente=self.c, anio=2030)
		self.julio = vencimientos_de(self.c, periodo="Julio de 2030")[0].name
		self.agosto = vencimientos_de(self.c, periodo="Agosto de 2030")[0].name

	def test_abre_todo_dentro_de_la_ventana(self):
		abrir_todos(hoy="2030-08-01")
		self.assertEqual(todos_abiertos(self.julio), ["Administrator"])
		self.assertEqual(todos_abiertos(self.agosto), [])

	def test_no_duplica(self):
		abrir_todos(hoy="2030-08-01")
		abrir_todos(hoy="2030-08-02")
		self.assertEqual(len(todos_abiertos(self.julio)), 1)

	def test_incluye_los_vencidos(self):
		abrir_todos(hoy="2030-08-20")
		self.assertEqual(todos_abiertos(self.julio), ["Administrator"])

	def test_se_cierra_al_presentar(self):
		abrir_todos(hoy="2030-08-01")
		v = frappe.get_doc("Vencimiento", self.julio)
		v.estado = "Presentada"
		v.save()
		self.assertEqual(todos_abiertos(self.julio), [])
		self.assertEqual(str(v.fecha_presentacion), today())

	def test_no_abre_para_presentados(self):
		v = frappe.get_doc("Vencimiento", self.julio)
		v.estado = "Presentada"
		v.save()
		abrir_todos(hoy="2030-08-01")
		self.assertEqual(todos_abiertos(self.julio), [])

	def test_un_todo_que_falla_no_detiene_a_los_demas(self):
		from frappe.desk.form import assign_to

		original = assign_to._add
		llamadas = []

		def falla_la_primera(args, **kw):
			llamadas.append(args["name"])
			if len(llamadas) == 1:
				raise frappe.PermissionError("sin permiso")
			return original(args, **kw)

		with patch("frappe.desk.form.assign_to._add", side_effect=falla_la_primera):
			abrir_todos(hoy="2030-09-01")
		abiertos = todos_abiertos(self.julio) + todos_abiertos(self.agosto)
		self.assertGreaterEqual(len(llamadas), 2)
		self.assertEqual(len(abiertos), 1)
