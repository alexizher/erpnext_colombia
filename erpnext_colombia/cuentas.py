import frappe

from erpnext_colombia.pais import PAIS

PLANTILLAS_PUC = ("Colombia PUC", "Colombia PUC Simple")
DIMENSION = "Tercero"
PREFIJOS_CORRIENTES = ("11", "12", "13", "14", "21", "22", "23", "24", "25", "26", "28")
PREFIJOS_NO_CORRIENTES = ("15", "16", "17", "18", "19", "27")
PREFIJOS_CON_TERCERO = ("13", "22", "23", "24", "25")
RAICES_DE_BALANCE = ("Asset", "Liability")
# Lo que ERPNext deja mal al crear una empresa con la plantilla "Colombia PUC" (por cobrar en 139980, etc.).
CUENTAS_POR_DEFECTO = {
	"default_receivable_account": "130505",
	"default_payable_account": "2205",
	# ERPNext deja la primera de ingresos del PUC, 410505 Cultivo de cereales. Consultoría sirve a
	# una oficina de servicios; una empresa de otra actividad la cambia en su ficha.
	"default_income_account": "415550",
	"default_expense_account": "519595",
	"default_cash_account": "110505",
	"default_bank_account": "111005",
	"round_off_account": "429581",
	"exchange_gain_loss_account": "421020",
	"stock_received_but_not_billed": "233595",
}


def clasificacion_por_defecto(numero, root_type):
	if root_type not in RAICES_DE_BALANCE:
		return None
	numero = numero or ""
	if numero.startswith(PREFIJOS_NO_CORRIENTES):
		return "No corriente"
	return "Corriente"


def exige_tercero(numero) -> bool:
	return bool(numero) and numero.startswith(PREFIJOS_CON_TERCERO)


def empresas_con_puc() -> list[str]:
	"""Empresas colombianas con el PUC: por la plantilla elegida o, si se crearon a partir de otra
	empresa (chart_of_accounts vacío), porque tienen la cuenta 1105 (Caja) numerada."""
	colombianas = frappe.get_all("Company", filters={"country": PAIS}, pluck="name")
	if not colombianas:
		return []
	por_plantilla = frappe.get_all(
		"Company",
		filters={"name": ("in", colombianas), "chart_of_accounts": ("in", PLANTILLAS_PUC)},
		pluck="name",
	)
	por_cuenta = frappe.get_all(
		"Account",
		filters={"company": ("in", colombianas), "account_number": "1105"},
		pluck="company",
		distinct=True,
	)
	return sorted(set(por_plantilla) | set(por_cuenta))


def aplicar_a_empresa(empresa: str) -> None:
	if empresa not in empresas_con_puc():
		frappe.logger("erpnext_colombia").info(f"{empresa} no es colombiana o no usa el PUC; se salta")
		return
	cuentas = frappe.get_all(
		"Account",
		filters={"company": empresa, "is_group": 0},
		fields=["name", "account_number", "root_type", "co_clasificacion_niif"],
	)
	for c in cuentas:
		if not c.co_clasificacion_niif:
			valor = clasificacion_por_defecto(c.account_number, c.root_type)
			if valor:
				frappe.db.set_value("Account", c.name, "co_clasificacion_niif", valor, update_modified=False)
	# El filtro se arma completo solo la primera vez. Después lo mantiene al_crear_cuenta, y las
	# cuentas que Daniela quite no vuelven a entrar en cada migración.
	if not frappe.db.exists("Accounting Dimension Filter", {"company": empresa, "accounting_dimension": DIMENSION}):
		_asegurar_filtro(empresa, [c.name for c in cuentas if exige_tercero(c.account_number)])


def _asegurar_filtro(empresa: str, cuentas: list[str]) -> None:
	nombre = frappe.db.get_value("Accounting Dimension Filter", {"company": empresa, "accounting_dimension": DIMENSION})
	if nombre:
		filtro = frappe.get_doc("Accounting Dimension Filter", nombre)
	else:
		filtro = frappe.new_doc("Accounting Dimension Filter")
		filtro.update({"company": empresa, "accounting_dimension": DIMENSION, "apply_restriction_on_values": 0})
	ya = {f.applicable_on_account for f in filtro.accounts}
	nuevas = [c for c in cuentas if c not in ya]
	if not nuevas and nombre:
		return
	for c in nuevas:
		filtro.append("accounts", {"applicable_on_account": c, "is_mandatory": 1})
	filtro.flags.ignore_permissions = True
	filtro.save()


def al_crear_cuenta(doc, method=None):
	if doc.company not in empresas_con_puc():
		return
	if not doc.co_clasificacion_niif:
		valor = clasificacion_por_defecto(doc.account_number, doc.root_type)
		if valor:
			doc.db_set("co_clasificacion_niif", valor, update_modified=False)
	if not doc.is_group and exige_tercero(doc.account_number):
		_asegurar_filtro(doc.company, [doc.name])


def al_crear_empresa(doc, method=None):
	# after_insert corre antes de que ERPNext cree el plan de cuentas (en on_update): aquí solo se marca.
	doc.flags.co_empresa_nueva = True


def al_guardar_empresa(doc, method=None):
	if doc.flags.co_empresa_nueva and doc.name in empresas_con_puc():
		corregir_cuentas_por_defecto(doc.name)


def corregir_cuentas_por_defecto(empresa: str) -> None:
	"""Solo al crear la empresa: después las cuentas por defecto son decisión de quien la lleva."""
	valores = {}
	for campo, numero in CUENTAS_POR_DEFECTO.items():
		nombre = frappe.db.get_value("Account", {"company": empresa, "account_number": numero, "is_group": 0})
		if nombre:
			valores[campo] = nombre
	valores["round_off_cost_center"] = frappe.db.get_value("Company", empresa, "cost_center")
	# Contabilidad externa: el inventario se registra con asientos, no con movimientos de stock.
	valores["enable_perpetual_inventory"] = 0
	frappe.db.set_value("Company", empresa, valores)
	frappe.clear_document_cache("Company", empresa)
