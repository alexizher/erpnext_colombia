import frappe
from erpnext.accounts.doctype.financial_report_template.financial_report_engine import FinancialReportEngine
from frappe.utils import flt

from erpnext_colombia.tests.utils import asiento, cliente, nuevo_tercero, proveedor

MARCA = "datos-estados"


def ejecutar(plantilla, empresa, desde="2025", hasta="2026"):
	# El reporte Balance Sheet de ERPNext trae "valores acumulados" marcado; sin eso cada columna
	# muestra la variación del año y no el saldo.
	acumulado = 1 if frappe.db.get_value("Financial Report Template", plantilla, "report_type") == "Balance Sheet" else 0
	filtros = frappe._dict(
		{
			"company": empresa,
			"report_template": plantilla,
			"from_fiscal_year": desde,
			"to_fiscal_year": hasta,
			"period_start_date": f"{desde}-01-01",
			"period_end_date": f"{hasta}-12-31",
			"filter_based_on": "Fiscal Year",
			"periodicity": "Yearly",
			"accumulated_values": acumulado,
		}
	)
	_columnas, filas, _msg, _grafico = FinancialReportEngine().execute(filtros)
	return filas


def valores(filas, texto):
	"""Valores por periodo de la fila cuyo texto visible es `texto`."""
	fila = next((f for f in filas if f.get("account_name") == texto), None)
	assert fila is not None, f"No está la fila {texto!r}"
	claves = fila.get("_segment_info", {}).get("period_keys", [])
	return [flt(fila.get(k)) for k in claves]


def cargar_movimientos(empresa):
	"""Movimientos conocidos en 2025 y 2026. Se cargan una sola vez por empresa."""
	if frappe.db.exists("Journal Entry", {"company": empresa, "user_remark": MARCA, "docstatus": 1}):
		return
	t = nuevo_tercero("800197268", "DIAN")
	socio = nuevo_tercero("1030567890", "Socio")  # NIT de 10 dígitos que no termina en su DV
	# 130505 y 2205 son Receivable y Payable en el PUC: ERPNext exige cliente y proveedor en esas líneas.
	partes = {
		"130505": ("Customer", cliente("890903938", "Bancolombia S.A.")),
		"2205": ("Supplier", proveedor("860034313", "Banco Davivienda S.A.")),
	}
	movimientos = [
		# 2025: aporte de capital, préstamo, venta, costo, compra de mercancía, gasto, activo fijo, depreciación
		("2025-01-02", [("111005", 10_000_000, 0), ("310505", 0, 10_000_000)], socio),
		("2025-02-01", [("111005", 5_000_000, 0), ("210505", 0, 5_000_000)], t),
		("2025-03-01", [("130505", 3_000_000, 0), ("413595", 0, 3_000_000)], t),
		("2025-03-01", [("613595", 1_200_000, 0), ("143599", 0, 1_200_000)], t),
		("2025-04-01", [("143599", 2_000_000, 0), ("2205", 0, 2_000_000)], t),
		("2025-05-01", [("519595", 400_000, 0), ("111005", 0, 400_000)], t),
		("2025-06-01", [("151605", 6_000_000, 0), ("111005", 0, 6_000_000)], t),
		("2025-12-31", [("516015", 300_000, 0), ("159205", 0, 300_000)], t),
		# 2026: cobro, pago a proveedor, otra venta, gasto bancario
		("2026-02-01", [("111005", 3_000_000, 0), ("130505", 0, 3_000_000)], t),
		("2026-03-01", [("2205", 1_000_000, 0), ("111005", 0, 1_000_000)], t),
		("2026-04-01", [("130505", 2_500_000, 0), ("413595", 0, 2_500_000)], t),
		("2026-05-01", [("530505", 50_000, 0), ("111005", 0, 50_000)], t),
	]
	for fecha, lineas, tercero in movimientos:
		filas = []
		for c, d, h in lineas:
			fila = {"cuenta": c, "debe": d, "haber": h}
			if c in partes:
				fila["party_type"], fila["party"] = partes[c]
			filas.append(fila)
		je = asiento(empresa, fecha, filas, tercero=tercero, enviar=False)
		je.user_remark = MARCA
		je.save()
		je.submit()
