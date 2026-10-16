import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today

COLORES = {
	"Pendiente": "orange",
	"En preparación": "blue",
	"Presentada": "green",
	"Pagada": "green",
	"No aplica": "gray",
}


class Vencimiento(Document):
	def validate(self):
		otro = frappe.db.get_value(
			"Vencimiento",
			{
				"cliente": self.cliente,
				"obligacion": self.obligacion,
				"anio": self.anio,
				"periodo": self.periodo,
				"name": ("!=", self.name),
			},
		)
		if otro:
			frappe.throw(_("Ya existe {0} para este cliente, obligación y periodo.").format(otro))
		if self.estado == "Presentada" and not self.fecha_presentacion:
			self.fecha_presentacion = today()
		self.titulo = f"{self.cliente_nombre or self.cliente} · {self.obligacion} {self.periodo}"
		self.color = COLORES[self.estado]

	def on_update(self):
		from erpnext_colombia.vencimientos.avisos import cerrar_si_termino

		cerrar_si_termino(self)
