import frappe
from frappe.tests import IntegrationTestCase

from erpnext_colombia.tests.utils import asiento, cliente, cuenta, empresa_prueba, gl, nuevo_tercero, proveedor


class TestMovimientos(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.empresa = empresa_prueba()
		cls.cc = frappe.get_cached_value("Company", cls.empresa, "cost_center")
		if not frappe.db.exists("Item", "SERV-CO"):
			frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": "SERV-CO",
					"item_group": "Services",
					"is_stock_item": 0,
					"stock_uom": "Nos",
				}
			).insert()

	def test_factura_de_venta_lleva_el_tercero_del_cliente(self):
		c = cliente("890903938", "Bancolombia S.A.")
		si = frappe.get_doc(
			{
				"doctype": "Sales Invoice",
				"company": self.empresa,
				"customer": c,
				"posting_date": "2026-03-10",
				"set_posting_time": 1,
				"currency": "COP",
				"debit_to": cuenta("130505"),
				"items": [
					{"item_code": "SERV-CO", "qty": 1, "rate": 100000, "income_account": cuenta("413595"), "cost_center": self.cc}
				],
			}
		).insert()
		si.submit()
		self.assertEqual(si.tercero, "890903938")
		self.assertTrue(all(g.tercero == "890903938" for g in gl(si.name)))

	def test_factura_de_compra_lleva_el_tercero_del_proveedor(self):
		s = proveedor("860034313", "Banco Davivienda S.A.")
		pi = frappe.get_doc(
			{
				"doctype": "Purchase Invoice",
				"company": self.empresa,
				"supplier": s,
				"posting_date": "2026-03-11",
				"set_posting_time": 1,
				"currency": "COP",
				"credit_to": cuenta("2205"),
				"items": [
					{"item_code": "SERV-CO", "qty": 1, "rate": 50000, "expense_account": cuenta("519595"), "cost_center": self.cc}
				],
			}
		).insert()
		pi.submit()
		self.assertTrue(all(g.tercero == "860034313" for g in gl(pi.name)))

	def test_pago_lleva_el_tercero_del_cliente(self):
		c = cliente("899999068", "Ecopetrol S.A.")
		pe = frappe.get_doc(
			{
				"doctype": "Payment Entry",
				"company": self.empresa,
				"payment_type": "Receive",
				"party_type": "Customer",
				"party": c,
				"posting_date": "2026-03-12",
				"paid_from": cuenta("130505"),
				"paid_to": cuenta("111005"),
				"paid_amount": 30000,
				"received_amount": 30000,
				"reference_no": "T-1",
				"reference_date": "2026-03-12",
			}
		).insert()
		pe.submit()
		self.assertTrue(all(g.tercero == "899999068" for g in gl(pe.name)))

	def test_tercero_del_encabezado_llena_solo_las_lineas_vacias(self):
		a = nuevo_tercero("800197268", "DIAN")
		b = nuevo_tercero("860034313", "Banco Davivienda S.A.")
		je = asiento(
			self.empresa,
			"2026-03-13",
			[
				{"cuenta": "519595", "debe": 10000},
				{"cuenta": "110505", "haber": 10000, "tercero": b},
			],
			tercero=a,
		)
		por_cuenta = {g.account: g.tercero for g in gl(je.name)}
		self.assertEqual(por_cuenta[cuenta("519595")], a)
		self.assertEqual(por_cuenta[cuenta("110505")], b)

	def test_linea_con_party_completa_el_tercero(self):
		s = proveedor("860034313", "Banco Davivienda S.A.")
		je = asiento(
			self.empresa,
			"2026-03-14",
			[
				{"cuenta": "519595", "debe": 20000, "tercero": "860034313"},
				{"cuenta": "2205", "haber": 20000, "party_type": "Supplier", "party": s},
			],
		)
		self.assertTrue(all(g.tercero == "860034313" for g in gl(je.name)))

	def test_la_anulacion_conserva_el_tercero(self):
		t = nuevo_tercero("800197268", "DIAN")
		je = asiento(self.empresa, "2026-03-15", [{"cuenta": "519595", "debe": 5000}, {"cuenta": "110505", "haber": 5000}], tercero=t)
		je.cancel()
		lineas = gl(je.name)
		self.assertEqual(len(lineas), 4)
		self.assertTrue(all(g.tercero == t for g in lineas))

	def test_renombrar_tercero_actualiza_movimientos(self):
		t = nuevo_tercero("900123450", "Error de digitación S.A.S.")
		je = asiento(self.empresa, "2026-03-16", [{"cuenta": "519595", "debe": 7000}, {"cuenta": "110505", "haber": 7000}], tercero=t)
		frappe.rename_doc("Tercero", t, "900123451", force=True)
		self.assertTrue(all(g.tercero == "900123451" for g in gl(je.name)))
		self.assertEqual(frappe.db.get_value("Tercero", "900123451", "numero_documento"), "900123451")

	def test_cambiar_el_cliente_en_un_borrador_cambia_el_tercero(self):
		c1 = cliente("890903938", "Bancolombia S.A.")
		c2 = cliente("899999068", "Ecopetrol S.A.")
		si = frappe.get_doc(
			{
				"doctype": "Sales Invoice",
				"company": self.empresa,
				"customer": c1,
				"posting_date": "2026-03-17",
				"set_posting_time": 1,
				"currency": "COP",
				"debit_to": cuenta("130505"),
				"items": [
					{"item_code": "SERV-CO", "qty": 1, "rate": 1000, "income_account": cuenta("413595"), "cost_center": self.cc}
				],
			}
		).insert()
		si.customer = c2
		si.save()
		self.assertEqual(si.tercero, "899999068")

	def test_cambiar_la_parte_de_una_linea_del_asiento_cambia_su_tercero(self):
		s1 = proveedor("860034313", "Banco Davivienda S.A.")
		s2 = proveedor("890903938", "Bancolombia S.A.")
		je = asiento(
			self.empresa,
			"2026-03-18",
			[
				{"cuenta": "519595", "debe": 3000, "tercero": "860034313"},
				{"cuenta": "2205", "haber": 3000, "party_type": "Supplier", "party": s1},
			],
			enviar=False,
		)
		je.accounts[1].party = s2
		je.save()
		self.assertEqual(je.accounts[1].tercero, "890903938")
