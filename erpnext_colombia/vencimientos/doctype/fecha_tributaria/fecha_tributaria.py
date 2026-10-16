import frappe
from frappe import _
from frappe.model.document import Document

from erpnext_colombia.vencimientos.fechas import clave_fecha


class FechaTributaria(Document):
	def autoname(self):
		self.name = clave_fecha(self)

	def validate(self):
		maximo = 9 if str(self.cifras) == "1" else 99
		for campo in ("digito_desde", "digito_hasta"):
			if not 0 <= (self.get(campo) or 0) <= maximo:
				frappe.throw(
					_("El dígito debe estar entre 0 y {0} cuando la regla mira {1} cifra(s).").format(
						maximo, self.cifras
					)
				)
		if self.digito_desde > self.digito_hasta:
			frappe.throw(
				_("El dígito inicial ({0}) es mayor que el final ({1}).").format(
					self.digito_desde, self.digito_hasta
				)
			)
		if not self.is_new() and not self.flags.desde_sincronizacion and self.has_value_changed("fecha"):
			self.corregida_a_mano = 1

	def on_update(self):
		antes = self.get_doc_before_save()
		if antes and str(antes.fecha) != str(self.fecha):
			from erpnext_colombia.vencimientos.generacion import propagar_fecha

			propagar_fecha(self, antes.fecha)
