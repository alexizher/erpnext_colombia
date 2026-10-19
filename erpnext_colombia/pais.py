import frappe

PAIS = "Colombia"


def es_colombiana(empresa: str | None) -> bool:
	"""Las reglas de la localización aplican a una empresa por su país, no por su plan de cuentas."""
	return bool(empresa) and frappe.get_cached_value("Company", empresa, "country") == PAIS
