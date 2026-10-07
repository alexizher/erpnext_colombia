import frappe

EMPRESA = "Empresa Prueba CO"
ABREVIATURA = "EPC"
GRUPO_CLIENTE = "Commercial"
TERRITORIO = "Colombia"
GRUPO_PROVEEDOR = "Local"


def preparar_sitio():
	"""Hook before_tests: datos base del asistente (grupos, territorios, unidades) si el sitio no los tiene."""
	if not frappe.db.exists("Customer Group", "All Customer Groups"):
		from erpnext.setup.setup_wizard.operations.install_fixtures import install

		install(country="Colombia")
	for nombre, compra, venta in (("Standard Selling", 0, 1), ("Standard Buying", 1, 0)):
		if not frappe.db.exists("Price List", nombre):
			frappe.get_doc(
				{"doctype": "Price List", "price_list_name": nombre, "currency": "COP", "buying": compra, "selling": venta}
			).insert()
	frappe.db.set_single_value("Selling Settings", "selling_price_list", "Standard Selling")
	frappe.db.set_single_value("Buying Settings", "buying_price_list", "Standard Buying")
	frappe.db.commit()


def empresa_prueba() -> str:
	if not frappe.db.exists("Company", EMPRESA):
		frappe.get_doc(
			{
				"doctype": "Company",
				"company_name": EMPRESA,
				"abbr": ABREVIATURA,
				"default_currency": "COP",
				"country": "Colombia",
				"chart_of_accounts": "Colombia PUC",
				"create_chart_of_accounts_based_on": "Standard Template",
			}
		).insert()
	if not frappe.db.get_value("Company", EMPRESA, "stock_received_but_not_billed"):
		# El asistente no la llena con el PUC; ERPNext la pide en toda factura de compra.
		srbnb = frappe.db.get_value(
			"Account", {"company": EMPRESA, "account_number": ("like", "2335%"), "is_group": 0}, order_by="account_number"
		)
		frappe.db.set_value("Company", EMPRESA, "stock_received_but_not_billed", srbnb)
	for anio in ("2025", "2026"):
		if not frappe.db.exists("Fiscal Year", anio):
			frappe.get_doc(
				{
					"doctype": "Fiscal Year",
					"year": anio,
					"year_start_date": f"{anio}-01-01",
					"year_end_date": f"{anio}-12-31",
				}
			).insert()
	return EMPRESA


def cuenta(numero: str, empresa: str = EMPRESA) -> str:
	nombre = frappe.db.get_value("Account", {"company": empresa, "account_number": numero})
	assert nombre, f"No existe la cuenta {numero} en {empresa}"
	return nombre


def nuevo_tercero(numero: str, razon: str) -> str:
	if not frappe.db.exists("Tercero", numero):
		frappe.get_doc(
			{"doctype": "Tercero", "tipo_documento": "31 - NIT", "numero_documento": numero, "razon_social": razon}
		).insert()
	return numero


def cliente(numero: str, razon: str) -> str:
	t = nuevo_tercero(numero, razon)
	existente = frappe.db.get_value("Customer", {"co_tercero": t})
	if existente:
		return existente
	return (
		frappe.get_doc(
			{"doctype": "Customer", "co_tercero": t, "customer_group": GRUPO_CLIENTE, "territory": TERRITORIO}
		)
		.insert()
		.name
	)


def proveedor(numero: str, razon: str) -> str:
	t = nuevo_tercero(numero, razon)
	existente = frappe.db.get_value("Supplier", {"co_tercero": t})
	if existente:
		return existente
	return frappe.get_doc({"doctype": "Supplier", "co_tercero": t, "supplier_group": GRUPO_PROVEEDOR}).insert().name


def asiento(empresa, fecha, lineas, tercero=None, enviar=True):
	"""lineas: [{"cuenta": "110505", "debe": 100, "haber": 0, "tercero": ..., "party_type": ..., "party": ...}]"""
	je = frappe.get_doc(
		{
			"doctype": "Journal Entry",
			"company": empresa,
			"posting_date": fecha,
			"voucher_type": "Journal Entry",
			"tercero": tercero,
			"accounts": [
				{
					"account": cuenta(linea["cuenta"], empresa),
					"debit_in_account_currency": linea.get("debe", 0),
					"credit_in_account_currency": linea.get("haber", 0),
					"tercero": linea.get("tercero"),
					"party_type": linea.get("party_type"),
					"party": linea.get("party"),
					"cost_center": frappe.get_cached_value("Company", empresa, "cost_center"),
				}
				for linea in lineas
			],
		}
	)
	je.insert()
	if enviar:
		je.submit()
	return je


def gl(voucher_no: str) -> list[dict]:
	return frappe.get_all(
		"GL Entry",
		filters={"voucher_no": voucher_no},
		fields=["account", "debit", "credit", "tercero", "is_cancelled"],
		order_by="creation",
	)
