import frappe


def preparar_sitio():
	"""Hook before_tests: datos base del asistente (grupos, territorios, unidades) si el sitio no los tiene."""
	if frappe.db.exists("Customer Group", "All Customer Groups"):
		return
	from erpnext.setup.setup_wizard.operations.install_fixtures import install

	install(country="Colombia")
	frappe.db.commit()
