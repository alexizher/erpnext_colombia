import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from erpnext_colombia.campos import CAMPOS


def after_install():
	configurar()


def after_migrate():
	configurar()


def configurar():
	create_custom_fields(CAMPOS, update=True)
	frappe.clear_cache()
