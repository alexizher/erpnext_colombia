import re

import frappe
from frappe import _
from frappe.model.document import Document

from erpnext_colombia.nit import codigo_tipo, digito_verificacion, limpiar_numero

# "900.123.456-7": el último dígito después de un guion es el de verificación.
DV_CON_GUION = re.compile(r"^\s*(.*\d)\s*-\s*(\d)\s*$")
DOCTYPES_CON_TERCERO = ("Customer", "Supplier", "Company")


class Tercero(Document):
	def autoname(self):
		self._preparar_numero()
		self.name = self.numero_documento

	def validate(self):
		self._preparar_numero()
		es_nit = codigo_tipo(self.tipo_documento) == "31"
		if not self.naturaleza:
			self.naturaleza = "Persona jurídica" if es_nit else "Persona natural"
		if es_nit:
			self._validar_digito()
		else:
			self.digito_verificacion = None
		self._validar_nombres()
		self.nombre_completo = self._armar_nombre()
		self.nit_completo = self._nit_completo()

	def on_update(self):
		self._propagar_nit()

	def before_rename(self, old, new, merge=False):
		numero = new
		if codigo_tipo(self.tipo_documento) == "31" and (m := DV_CON_GUION.match(new or "")):
			numero = m.group(1)
		numero = limpiar_numero(numero, self.tipo_documento)
		if not numero:
			frappe.throw(_("Falta el número de documento."))
		return numero

	def after_rename(self, old, new, merge=False):
		self.numero_documento = new
		if codigo_tipo(self.tipo_documento) == "31":
			self.digito_verificacion = str(digito_verificacion(new))
		self.nit_completo = self._nit_completo()
		self.db_set(
			{
				"numero_documento": new,
				"digito_verificacion": self.digito_verificacion,
				"nit_completo": self.nit_completo,
			}
		)
		self._propagar_nit()

	def _preparar_numero(self):
		if codigo_tipo(self.tipo_documento) == "31" and (m := DV_CON_GUION.match(self.numero_documento or "")):
			numero, dv = m.groups()
			if self.digito_verificacion in (None, ""):
				self.digito_verificacion = dv
			elif str(self.digito_verificacion) != dv:
				frappe.throw(
					_("El número trae el dígito {0} después del guion y el campo dígito de verificación dice {1}.").format(
						dv, self.digito_verificacion
					)
				)
			self.numero_documento = numero
		self.numero_documento = limpiar_numero(self.numero_documento, self.tipo_documento)
		if not self.numero_documento:
			frappe.throw(_("Falta el número de documento."))

	def _nit_completo(self):
		if codigo_tipo(self.tipo_documento) == "31":
			return f"{self.numero_documento}-{self.digito_verificacion}"
		return self.numero_documento

	def _propagar_nit(self):
		"""Clientes, proveedores y empresas enlazados muestran el NIT del tercero en tax_id."""
		from erpnext_colombia.membrete import generar_membrete

		for doctype in DOCTYPES_CON_TERCERO:
			for nombre in frappe.get_all(doctype, filters={"co_tercero": self.name}, pluck="name"):
				frappe.db.set_value(doctype, nombre, "tax_id", self.nit_completo, update_modified=False)
				if doctype == "Company":
					generar_membrete(nombre)

	def _validar_digito(self):
		numero = self.numero_documento
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
