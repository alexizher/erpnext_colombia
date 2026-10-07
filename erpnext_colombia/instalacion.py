import frappe
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
	make_dimension_in_accounting_doctypes,
)
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from erpnext_colombia.campos import CAMPOS


def after_install():
	configurar()


def after_migrate():
	configurar()


def configurar():
	create_custom_fields(CAMPOS, update=True)
	crear_dimension()
	from erpnext_colombia.cuentas import aplicar_a_empresa, empresas_con_puc

	for empresa in empresas_con_puc():
		aplicar_a_empresa(empresa)
	from erpnext_colombia.estados_financieros import sincronizar_plantillas

	sincronizar_plantillas()
	frappe.clear_cache()


def crear_dimension():
	nombre = frappe.db.get_value("Accounting Dimension", {"document_type": "Tercero"})
	if nombre:
		dimension = frappe.get_doc("Accounting Dimension", nombre)
	else:
		dimension = frappe.get_doc({"doctype": "Accounting Dimension", "document_type": "Tercero"})
		dimension.insert(ignore_permissions=True)
	# Fuera de pruebas ERPNext crea los campos en segundo plano; aquí se crean ya, y el trabajo en
	# segundo plano los encuentra hechos y no hace nada.
	make_dimension_in_accounting_doctypes(dimension)
