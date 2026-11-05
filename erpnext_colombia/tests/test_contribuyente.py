import frappe
from frappe.tests import IntegrationTestCase

from erpnext_colombia.contribuyente import tipos_de
from erpnext_colombia.tests.utils import GRUPO_CLIENTE, TERRITORIO

NUMEROS = [
	"901000700",
	"901000711",
	"901000722",
	"901000733",
	"901000744",
	"901000755",
	"1030567700",
	"EXT700",
]


def tercero(**campos):
	datos = {
		"doctype": "Tercero",
		"tipo_documento": "31 - NIT",
		"numero_documento": "901000700",
		"razon_social": "Setecientos S.A.S.",
	}
	datos.update(campos)
	return frappe.get_doc(datos)


def persona(numero="1030567700", **campos):
	return tercero(
		tipo_documento="13 - Cédula de ciudadanía",
		numero_documento=numero,
		razon_social=None,
		primer_apellido="Molina",
		primer_nombre="Daniela",
		**campos,
	)


def marcadas(t):
	campos = (
		"rf_gran_contribuyente",
		"rf_autorretenedor",
		"rf_agente_retencion_iva",
		"rf_regimen_simple",
		"rf_no_aplica",
	)
	return [c for c in campos if t.get(c)]


class TestListaDeTipos(IntegrationTestCase):
	def test_cada_naturaleza_ve_solo_sus_tipos(self):
		pj, pn = tipos_de("Persona jurídica"), tipos_de("Persona natural")
		self.assertIn("Grande Contribuyente Autorretenedor", pj)
		self.assertNotIn("Grande Contribuyente Autorretenedor", pn)
		self.assertIn("Persona Natural No Responsable del IVA", pn)
		self.assertNotIn("Persona Natural No Responsable del IVA", pj)
		for comun in ("Persona Natural o Jurídica Ley 1429", "Tercero del Exterior"):
			self.assertIn(comun, pj)
			self.assertIn(comun, pn)
		self.assertEqual(len(set(pj) | set(pn)), 15)


class ConTercerosLimpios(IntegrationTestCase):
	def setUp(self):
		for numero in NUMEROS:
			for doctype in ("Customer", "Supplier"):
				for nombre in frappe.get_all(doctype, filters={"co_tercero": numero}, pluck="name"):
					frappe.delete_doc(doctype, nombre, force=True, ignore_permissions=True)
			if frappe.db.exists("Tercero", numero):
				frappe.delete_doc("Tercero", numero, force=True, ignore_permissions=True)


class TestTipoDeContribuyente(ConTercerosLimpios):
	def test_por_defecto_nit_es_persona_juridica_y_no_aplica(self):
		t = tercero().insert()
		self.assertEqual(t.tipo_contribuyente, "Persona Jurídica")
		self.assertEqual(marcadas(t), ["rf_no_aplica"])

	def test_por_defecto_cedula_es_responsable_del_iva(self):
		t = persona().insert()
		self.assertEqual(t.tipo_contribuyente, "Persona Natural Responsable del IVA")

	def test_por_defecto_documento_del_exterior_es_tercero_del_exterior(self):
		t = tercero(
			tipo_documento="42 - Documento de identificación extranjero",
			numero_documento="EXT700",
			naturaleza="Persona jurídica",
			pais="Spain",
		).insert()
		self.assertEqual(t.tipo_contribuyente, "Tercero del Exterior")

	def test_tipo_de_otra_naturaleza_se_rechaza(self):
		with self.assertRaisesRegex(frappe.ValidationError, "no aplica a una persona natural"):
			persona(tipo_contribuyente="Grande Contribuyente Autorretenedor").insert()

	def test_el_tipo_propone_las_responsabilidades(self):
		t = tercero(
			numero_documento="901000711", tipo_contribuyente="Grande Contribuyente Autorretenedor"
		).insert()
		self.assertEqual(marcadas(t), ["rf_gran_contribuyente", "rf_autorretenedor"])

	def test_cambio_manual_se_respeta_si_el_tipo_no_cambia(self):
		t = tercero(numero_documento="901000722").insert()
		t.rf_agente_retencion_iva = 1
		t.save()
		self.assertIn("rf_agente_retencion_iva", marcadas(t))

	def test_cambiar_el_tipo_vuelve_a_proponer(self):
		t = tercero(numero_documento="901000733").insert()
		t.tipo_contribuyente = "Régimen Simple de Tributación Persona Jurídica"
		t.save()
		self.assertEqual(marcadas(t), ["rf_regimen_simple"])


class TestPropiedadesActivas(ConTercerosLimpios):
	def test_marcar_cliente_crea_el_cliente(self):
		t = tercero(numero_documento="901000744", es_cliente=1).insert()
		cliente = frappe.db.get_value(
			"Customer", {"co_tercero": t.name}, ["customer_name", "tax_id"], as_dict=True
		)
		self.assertEqual(cliente.customer_name, "Setecientos S.A.S.")
		self.assertEqual(cliente.tax_id, t.nit_completo)

	def test_marcar_proveedor_crea_el_proveedor_una_sola_vez(self):
		t = tercero(numero_documento="901000755", es_proveedor=1).insert()
		t.save()
		self.assertEqual(frappe.db.count("Supplier", {"co_tercero": t.name}), 1)

	def test_desmarcar_no_borra_el_cliente(self):
		t = tercero(numero_documento="901000744", es_cliente=1).insert()
		t.es_cliente = 0
		t.save()
		self.assertTrue(frappe.db.exists("Customer", {"co_tercero": t.name}))

	def test_crear_el_cliente_por_su_lado_marca_la_propiedad(self):
		t = tercero(numero_documento="901000744").insert()
		frappe.get_doc(
			{
				"doctype": "Customer",
				"co_tercero": t.name,
				"customer_group": GRUPO_CLIENTE,
				"territory": TERRITORIO,
			}
		).insert()
		self.assertEqual(frappe.db.get_value("Tercero", t.name, "es_cliente"), 1)


class TestParche(ConTercerosLimpios):
	def test_tercero_viejo_queda_con_tipo_y_su_propiedad_de_cliente(self):
		from erpnext_colombia.patches.v0_6 import tipo_y_propiedades_de_terceros

		t = tercero(numero_documento="901000744", es_cliente=1).insert()
		frappe.db.set_value("Tercero", t.name, {"tipo_contribuyente": "", "es_cliente": 0, "rf_no_aplica": 0})
		tipo_y_propiedades_de_terceros.execute()
		viejo = frappe.get_doc("Tercero", t.name)
		self.assertEqual(viejo.tipo_contribuyente, "Persona Jurídica")
		self.assertEqual(viejo.es_cliente, 1)
		self.assertEqual(marcadas(viejo), ["rf_no_aplica"])


class TestNombreDesdeElTercero(IntegrationTestCase):
	def test_el_formulario_trae_el_nombre_del_tercero(self):
		for doctype, campo in (("Customer", "customer_name"), ("Supplier", "supplier_name")):
			df = frappe.get_meta(doctype).get_field(campo)
			self.assertEqual(df.fetch_from, "co_tercero.nombre_completo", doctype)
			self.assertEqual(df.fetch_if_empty, 1, doctype)
