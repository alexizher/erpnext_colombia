import datetime

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import flt

from erpnext_colombia.honorarios.periodicidad import Honorario, Periodo
from erpnext_colombia.tests.utils import cliente, empresa_prueba

d = datetime.date
INICIO = d(2026, 1, 15)


def honorario(periodicidad="Mensual", desde=INICIO, hasta=None):
	return Honorario(
		concepto="Contabilidad", valor=500_000, periodicidad=periodicidad, desde=desde, hasta=hasta
	)


class TestPeriodicidad(IntegrationTestCase):
	def test_periodo_se_escribe_anio_mes(self):
		self.assertEqual(str(Periodo(2026, 3)), "2026-03")
		self.assertEqual(Periodo.de(d(2026, 12, 9)), Periodo(2026, 12))
		self.assertEqual(Periodo(2026, 12).siguiente(), Periodo(2027, 1))
		self.assertEqual(Periodo(2026, 10).nombre, "octubre de 2026")

	def test_mensual_desde_el_mes_de_inicio(self):
		h = honorario()
		self.assertFalse(h.toca_en(Periodo(2025, 12)))
		for mes in range(1, 13):
			self.assertTrue(h.toca_en(Periodo(2026, mes)), mes)

	def test_no_toca_despues_de_hasta(self):
		h = honorario(hasta=d(2026, 6, 30))
		self.assertTrue(h.toca_en(Periodo(2026, 6)))
		self.assertFalse(h.toca_en(Periodo(2026, 7)))

	def test_trimestral_cada_tres_meses_desde_el_inicio(self):
		h = honorario("Trimestral")
		meses = [m for m in range(1, 13) if h.toca_en(Periodo(2026, m))]
		self.assertEqual(meses, [1, 4, 7, 10])

	def test_bimestral_semestral_y_anual(self):
		self.assertEqual(
			[m for m in range(1, 13) if honorario("Bimestral").toca_en(Periodo(2026, m))], [1, 3, 5, 7, 9, 11]
		)
		self.assertEqual(
			[m for m in range(1, 13) if honorario("Semestral").toca_en(Periodo(2026, m))], [1, 7]
		)
		anual = honorario("Anual", desde=d(2026, 3, 1))
		self.assertTrue(anual.toca_en(Periodo(2027, 3)))
		self.assertFalse(anual.toca_en(Periodo(2027, 4)))

	def test_una_vez_solo_en_su_mes(self):
		h = honorario("Una vez", desde=d(2026, 4, 20))
		self.assertEqual([m for m in range(1, 13) if h.toca_en(Periodo(2026, m))], [4])
		self.assertFalse(h.toca_en(Periodo(2027, 4)))


NUMERO_A = "901888001"
NUMERO_B = "901888002"
NUMERO_SIN = "901888003"


def configurar_honorarios(dia=5):
	from erpnext_colombia.honorarios.instalacion import configurar

	configurar()
	conf = frappe.get_single("Configuracion de Honorarios")
	conf.empresa = empresa_prueba()
	conf.dia_de_facturacion = dia
	conf.save()
	return conf


def con_honorarios(numero, razon, filas):
	nombre = cliente(numero, razon)
	c = frappe.get_doc("Customer", nombre)
	c.disabled = 0
	c.set("co_honorarios", filas)
	c.save()
	return nombre


def facturas_de(nombre, periodo):
	return frappe.get_all(
		"Sales Invoice",
		filters={"customer": nombre, "co_periodo_honorarios": periodo},
		fields=["name", "docstatus", "posting_date", "tercero"],
	)


class TestFacturacionDeHonorarios(IntegrationTestCase):
	def setUp(self):
		configurar_honorarios()
		self.a = con_honorarios(
			NUMERO_A,
			"Honorarios A S.A.S.",
			[
				{
					"concepto": "Contabilidad mensual",
					"valor": 800_000,
					"periodicidad": "Mensual",
					"desde": "2026-01-01",
				},
				{
					"concepto": "Declaración de renta",
					"valor": 1_200_000,
					"periodicidad": "Una vez",
					"desde": "2026-08-01",
				},
			],
		)
		self.b = con_honorarios(
			NUMERO_B,
			"Honorarios B S.A.S.",
			[{"concepto": "Nómina", "valor": 300_000, "periodicidad": "Trimestral", "desde": "2026-01-01"}],
		)
		self.sin = con_honorarios(NUMERO_SIN, "Sin Honorarios S.A.S.", [])
		for nombre in (self.a, self.b, self.sin):
			for f in frappe.get_all(
				"Sales Invoice", filters={"customer": nombre}, fields=["name", "docstatus"]
			):
				if f.docstatus == 1:
					frappe.get_doc("Sales Invoice", f.name).cancel()
				frappe.delete_doc("Sales Invoice", f.name, force=True)

	def facturar(self, periodo, hoy):
		from erpnext_colombia.honorarios.facturacion import Facturador

		return Facturador.desde_configuracion(hoy=hoy).facturar(periodo)

	def test_un_borrador_por_cliente_con_lo_que_toca_en_el_mes(self):
		self.facturar(Periodo(2026, 8), hoy=d(2026, 8, 5))
		[fa] = facturas_de(self.a, "2026-08")
		self.assertEqual(fa.docstatus, 0)
		self.assertEqual(fa.tercero, NUMERO_A)
		items = frappe.get_all(
			"Sales Invoice Item", filters={"parent": fa.name}, fields=["description", "rate"], order_by="idx"
		)
		self.assertEqual(
			[(i.description, flt(i.rate)) for i in items],
			[
				("Contabilidad mensual - agosto de 2026", 800_000),
				("Declaración de renta - agosto de 2026", 1_200_000),
			],
		)
		self.assertEqual(facturas_de(self.b, "2026-08"), [])
		self.assertEqual(frappe.get_all("Sales Invoice", filters={"customer": self.sin}), [])

	def test_trimestral_factura_en_su_mes(self):
		self.facturar(Periodo(2026, 10), hoy=d(2026, 10, 5))
		self.assertEqual(len(facturas_de(self.b, "2026-10")), 1)

	def test_no_duplica_el_mes(self):
		self.facturar(Periodo(2026, 9), hoy=d(2026, 9, 5))
		self.facturar(Periodo(2026, 9), hoy=d(2026, 9, 6))
		self.assertEqual(len(facturas_de(self.a, "2026-09")), 1)

	def test_cancelada_no_se_vuelve_a_crear(self):
		# Si Daniela cancela la de un mes, es porque ese mes no se cobra.
		self.facturar(Periodo(2026, 9), hoy=d(2026, 9, 5))
		[fa] = facturas_de(self.a, "2026-09")
		doc = frappe.get_doc("Sales Invoice", fa.name)
		doc.submit()
		doc.cancel()
		self.facturar(Periodo(2026, 9), hoy=d(2026, 9, 6))
		self.assertEqual(len(facturas_de(self.a, "2026-09")), 1)

	def test_cliente_deshabilitado_no_se_factura(self):
		frappe.db.set_value("Customer", self.a, "disabled", 1)
		self.facturar(Periodo(2026, 9), hoy=d(2026, 9, 5))
		self.assertEqual(facturas_de(self.a, "2026-09"), [])

	def test_la_tarea_diaria_espera_el_dia_de_facturacion(self):
		from erpnext_colombia.honorarios.facturacion import Facturador

		Facturador.desde_configuracion(hoy=d(2026, 11, 4)).facturar_si_toca()
		self.assertEqual(facturas_de(self.a, "2026-11"), [])
		Facturador.desde_configuracion(hoy=d(2026, 11, 20)).facturar_si_toca()
		self.assertEqual(len(facturas_de(self.a, "2026-11")), 1)

	def test_sin_empresa_configurada_no_hace_nada(self):
		from erpnext_colombia.honorarios.facturacion import Facturador

		frappe.db.set_single_value("Configuracion de Honorarios", "empresa", None)
		self.assertEqual(Facturador.desde_configuracion(hoy=d(2026, 12, 20)).facturar_si_toca(), [])
		self.assertEqual(facturas_de(self.a, "2026-12"), [])

	def test_con_plantilla_de_impuestos_lleva_iva(self):
		from erpnext_colombia.tests.utils import ABREVIATURA, cuenta

		plantilla = f"IVA Honorarios - {ABREVIATURA}"
		if not frappe.db.exists("Sales Taxes and Charges Template", plantilla):
			frappe.get_doc(
				{
					"doctype": "Sales Taxes and Charges Template",
					"title": "IVA Honorarios",
					"company": empresa_prueba(),
					"taxes": [
						{
							"charge_type": "On Net Total",
							"account_head": cuenta("2408"),
							"rate": 19,
							"description": "IVA 19 %",
						}
					],
				}
			).insert()
		frappe.db.set_single_value("Configuracion de Honorarios", "plantilla_impuestos", plantilla)
		try:
			self.facturar(Periodo(2026, 10), hoy=d(2026, 10, 5))
		finally:
			frappe.db.set_single_value("Configuracion de Honorarios", "plantilla_impuestos", None)
		[fb] = facturas_de(self.b, "2026-10")
		factura = frappe.get_doc("Sales Invoice", fb.name)
		self.assertEqual(flt(factura.total_taxes_and_charges), 57_000)
		self.assertEqual(flt(factura.grand_total), 357_000)

	def test_valor_cero_se_rechaza(self):
		c = frappe.get_doc("Customer", self.a)
		c.append(
			"co_honorarios",
			{"concepto": "Gratis", "valor": 0, "periodicidad": "Mensual", "desde": "2026-01-01"},
		)
		with self.assertRaisesRegex(frappe.ValidationError, "valor"):
			c.save()


class TestHonorariosPorCliente(IntegrationTestCase):
	def test_facturado_pagado_y_saldo(self):
		from erpnext_colombia.honorarios.facturacion import Facturador
		from erpnext_colombia.honorarios.report.honorarios_por_cliente.honorarios_por_cliente import execute

		configurar_honorarios()
		nombre = con_honorarios(
			"901888004",
			"Reporte Honorarios S.A.S.",
			[
				{
					"concepto": "Contabilidad mensual",
					"valor": 400_000,
					"periodicidad": "Mensual",
					"desde": "2026-01-01",
				}
			],
		)
		for f in frappe.get_all("Sales Invoice", filters={"customer": nombre}, fields=["name", "docstatus"]):
			if f.docstatus == 1:
				frappe.get_doc("Sales Invoice", f.name).cancel()
			frappe.delete_doc("Sales Invoice", f.name, force=True)
		for mes in (3, 4):
			Facturador.desde_configuracion(hoy=d(2026, mes, 5)).facturar(Periodo(2026, mes))
			[f] = facturas_de(nombre, f"2026-{mes:02d}")
			frappe.get_doc("Sales Invoice", f.name).submit()

		_columnas, filas = execute(
			frappe._dict(
				{
					"company": empresa_prueba(),
					"from_date": "2026-01-01",
					"to_date": "2026-12-31",
					"customer": nombre,
				}
			)
		)
		[fila] = filas
		self.assertEqual(flt(fila["facturado"]), 800_000)
		self.assertEqual(flt(fila["saldo"]), 800_000)
		self.assertEqual(flt(fila["pagado"]), 0)
		self.assertEqual(fila["facturas"], 2)
		self.assertEqual(str(fila["pendiente_desde"]), "2026-03-05")


class TestProspectoAClientes(IntegrationTestCase):
	def test_honorario_propuesto_pasa_al_cliente(self):
		from erpnext.crm.doctype.lead.lead import make_customer

		from erpnext_colombia.tests.utils import nuevo_tercero

		configurar_honorarios()
		lead = frappe.get_doc(
			{
				"doctype": "Lead",
				"first_name": "Prospecto",
				"company_name": "Prospecto Honorarios S.A.S.",
				"co_servicios": "Contabilidad y nómina",
				"co_honorario_propuesto": 650_000,
			}
		).insert()
		c = make_customer(lead.name)
		c.co_tercero = nuevo_tercero("901888005", "Prospecto Honorarios S.A.S.")
		c.customer_group = "Commercial"
		c.territory = "Colombia"
		c.insert()
		[fila] = c.co_honorarios
		self.assertEqual(
			(fila.concepto, flt(fila.valor), fila.periodicidad), ("Honorarios contables", 650_000, "Mensual")
		)
		self.assertEqual(getattr(fila.desde, "day", None) or int(str(fila.desde)[-2:]), 1)
