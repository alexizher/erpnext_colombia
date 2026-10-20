import frappe
from frappe import _
from frappe.model.document import Document


class ConfiguraciondeHonorarios(Document):
	def validate(self):
		if not 1 <= (self.dia_de_facturacion or 0) <= 28:
			frappe.throw(_("El día de facturación va de 1 a 28, para que exista en todos los meses."))


@frappe.whitelist()
def generar_ahora() -> list[str]:
	"""Crea ya los borradores del mes, sin esperar el día de facturación."""
	from erpnext_colombia.honorarios.facturacion import Facturador
	from erpnext_colombia.honorarios.periodicidad import Periodo

	frappe.only_for(("System Manager", "Accounts Manager"))
	facturador = Facturador.desde_configuracion()
	if not facturador.empresa:
		frappe.throw(_("Primero escoja la empresa que factura."))
	return facturador.facturar(Periodo.de(facturador.hoy))
