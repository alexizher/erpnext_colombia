import frappe
from frappe import _
from frappe.model.document import Document

from erpnext_colombia.nit import codigo_tipo, digito_verificacion, limpiar_numero


class Tercero(Document):
	def autoname(self):
		self.numero_documento = limpiar_numero(self.numero_documento, self.tipo_documento)
		if not self.numero_documento:
			frappe.throw(_("Falta el número de documento."))
		self.name = self.numero_documento

	def validate(self):
		self.numero_documento = limpiar_numero(self.numero_documento, self.tipo_documento)
		if not self.numero_documento:
			frappe.throw(_("Falta el número de documento."))
		es_nit = codigo_tipo(self.tipo_documento) == "31"
		if not self.naturaleza:
			self.naturaleza = "Persona jurídica" if es_nit else "Persona natural"
		if es_nit:
			self._validar_digito()
		else:
			self.digito_verificacion = None
		self._validar_nombres()
		self.nombre_completo = self._armar_nombre()
		self.nit_completo = (
			f"{self.numero_documento}-{self.digito_verificacion}" if es_nit else self.numero_documento
		)

	def after_rename(self, old, new, merge=False):
		self.db_set("numero_documento", new)
		if codigo_tipo(self.tipo_documento) == "31":
			dv = digito_verificacion(new)
			self.db_set("digito_verificacion", str(dv))
			self.db_set("nit_completo", f"{new}-{dv}")
		else:
			self.db_set("nit_completo", new)

	def _validar_digito(self):
		numero = self.numero_documento
		if len(numero) == 10 and int(numero[-1]) == digito_verificacion(numero[:-1]):
			frappe.throw(
				_(
					"El número {0} parece traer el dígito de verificación al final. "
					"Escriba {1} en el número; el dígito de verificación va en su propio campo."
				).format(numero, numero[:-1])
			)
		calculado = str(digito_verificacion(numero))
		if self.digito_verificacion not in (None, "") and str(self.digito_verificacion) != calculado:
			frappe.throw(
				_("El dígito de verificación de {0} es {1}, no {2}.").format(
					numero, calculado, self.digito_verificacion
				)
			)
		self.digito_verificacion = calculado

	def _validar_nombres(self):
		if self.naturaleza == "Persona natural":
			if not (self.primer_apellido and self.primer_nombre):
				frappe.throw(_("Para una persona natural escriba el primer apellido y el primer nombre."))
		elif not self.razon_social:
			frappe.throw(_("Para una persona jurídica escriba la razón social."))

	def _armar_nombre(self):
		if self.naturaleza == "Persona natural":
			partes = [self.primer_nombre, self.otros_nombres, self.primer_apellido, self.segundo_apellido]
			return " ".join(p.strip() for p in partes if p and p.strip())
		return self.razon_social.strip()
