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
				{
					"doctype": "Price List",
					"price_list_name": nombre,
					"currency": "COP",
					"buying": compra,
					"selling": venta,
				}
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
			"Account",
			{"company": EMPRESA, "account_number": ("like", "2335%"), "is_group": 0},
			order_by="account_number",
		)
		frappe.db.set_value("Company", EMPRESA, "stock_received_but_not_billed", srbnb)
	if frappe.db.get_value("Company", EMPRESA, "enable_perpetual_inventory"):
		# Contabilidad externa: el inventario se registra con asientos, no con movimientos de stock.
		frappe.db.set_value("Company", EMPRESA, "enable_perpetual_inventory", 0)
	# ERPNext guarda el valor en memoria por proceso (erpnext.is_perpetual_inventory_enabled); en la suite
	# completa otro módulo pudo leerlo antes del cambio.
	frappe.clear_document_cache("Company", EMPRESA)
	getattr(frappe.local, "enable_perpetual_inventory", {}).pop(EMPRESA, None)
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
			{
				"doctype": "Tercero",
				"tipo_documento": "31 - NIT",
				"numero_documento": numero,
				"razon_social": razon,
			}
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
	return (
		frappe.get_doc({"doctype": "Supplier", "co_tercero": t, "supplier_group": GRUPO_PROVEEDOR})
		.insert()
		.name
	)


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


OBLIGACION_PRUEBA = "Prueba mensual"


def obligacion_prueba() -> str:
	"""Obligación solo para pruebas: así las fechas reales de 2026 no se cruzan con las de las pruebas."""
	if not frappe.db.exists("Obligacion Tributaria", OBLIGACION_PRUEBA):
		frappe.get_doc(
			{"doctype": "Obligacion Tributaria", "nombre": OBLIGACION_PRUEBA, "formulario": "000"}
		).insert()
	return OBLIGACION_PRUEBA


def fecha_prueba(periodo, fecha, anio=2030, segmento="Todos", cifras="1", desde=0, hasta=9, obligacion=None):
	from erpnext_colombia.vencimientos.fechas import clave_fecha

	datos = {
		"doctype": "Fecha Tributaria",
		"obligacion": obligacion or obligacion_prueba(),
		"anio": anio,
		"periodo": periodo,
		"segmento": segmento,
		"cifras": cifras,
		"digito_desde": desde,
		"digito_hasta": hasta,
		"fecha": fecha,
		"fuente": "prueba",
	}
	nombre = clave_fecha(datos)
	if frappe.db.exists("Fecha Tributaria", nombre):
		return frappe.get_doc("Fecha Tributaria", nombre)
	return frappe.get_doc(datos).insert()


def cliente_con(numero, razon, obligaciones, gran_contribuyente=0, tipo="31 - NIT"):
	"""obligaciones: [{"obligacion": ..., "desde": ..., "hasta": ...}]"""
	if not frappe.db.exists("Tercero", numero):
		datos = {"doctype": "Tercero", "tipo_documento": tipo, "numero_documento": numero}
		if tipo.startswith("31"):
			datos["razon_social"] = razon
		else:
			datos.update({"primer_apellido": razon, "primer_nombre": "Prueba"})
		frappe.get_doc(datos).insert()
	nombre = frappe.db.get_value("Customer", {"co_tercero": numero})
	if nombre:
		c = frappe.get_doc("Customer", nombre)
	else:
		c = frappe.get_doc(
			{
				"doctype": "Customer",
				"co_tercero": numero,
				"customer_group": GRUPO_CLIENTE,
				"territory": TERRITORIO,
			}
		)
	c.co_gran_contribuyente = gran_contribuyente
	c.set("co_obligaciones", obligaciones)
	if nombre:
		c.save()
	else:
		c.insert()
	return c.name


def vencimientos_de(cliente, anio=2030, **filtros) -> list[dict]:
	return frappe.get_all(
		"Vencimiento",
		filters={"cliente": cliente, "anio": anio, **filtros},
		fields=["name", "periodo", "fecha_vencimiento", "estado", "cerrado_por_sistema"],
		order_by="fecha_vencimiento",
	)


def cuenta_correo_prueba():
	"""Cuenta saliente por defecto para que frappe.sendmail encole; en pruebas la cola no se envía."""
	if frappe.db.exists("Email Account", {"default_outgoing": 1}):
		return
	frappe.get_doc(
		{
			"doctype": "Email Account",
			"email_account_name": "Prueba Vencimientos",
			"email_id": "pruebas@example.com",
			"smtp_server": "localhost",
			"enable_outgoing": 1,
			"default_outgoing": 1,
			"password": "x",
		}
	).insert(ignore_permissions=True)
