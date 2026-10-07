import frappe

PUC = "Colombia PUC"
DIMENSION = "Tercero"
PREFIJOS_CORRIENTES = ("11", "12", "13", "14", "21", "22", "23", "24", "25", "26", "28")
PREFIJOS_NO_CORRIENTES = ("15", "16", "17", "18", "19", "27")
PREFIJOS_CON_TERCERO = ("13", "22", "23", "24", "25")
RAICES_DE_BALANCE = ("Asset", "Liability")


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
	return frappe.get_all("Company", filters={"chart_of_accounts": PUC}, pluck="name")


def aplicar_a_empresa(empresa: str) -> None:
	if empresa not in empresas_con_puc():
		frappe.logger("erpnext_colombia").info(f"{empresa} no usa {PUC}; se salta")
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
