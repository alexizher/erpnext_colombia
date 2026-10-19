import frappe
from frappe import _
from frappe.utils import getdate, today

from erpnext_colombia.vencimientos.reglas import ABIERTOS, digitos, responsable, segmento


def generar(cliente: str | None = None, anio: int | None = None) -> list[str]:
	"""Concilia los vencimientos de un cliente o de todos. Devuelve los problemas de datos encontrados."""
	anio_actual = getdate(today()).year
	anios = [anio] if anio else [anio_actual, anio_actual + 1]
	clientes = [cliente] if cliente else _clientes_a_revisar()
	problemas = []
	for c in clientes:
		frappe.db.savepoint("vencimientos_cliente")
		try:
			problemas += generar_cliente(c, anios)
		except Exception:
			# Un cliente que falla a mitad de camino no deja escrituras a medias.
			frappe.db.rollback(save_point="vencimientos_cliente")
			frappe.log_error(title=f"Vencimientos: no se pudo generar {c}")
			nombre = frappe.db.get_value("Customer", c, "customer_name") or c
			problemas.append(_("{0}: error al generar sus vencimientos (ver Error Log).").format(nombre))
	return list(dict.fromkeys(problemas))


def _clientes_a_revisar() -> list[str]:
	"""Clientes con obligaciones y clientes que aún tienen vencimientos abiertos (para cerrarlos si ya no aplican)."""
	con_obligaciones = frappe.get_all(
		"Obligacion del Cliente", filters={"parenttype": "Customer"}, pluck="parent"
	)
	con_abiertos = frappe.get_all("Vencimiento", filters={"estado": ("in", ABIERTOS)}, pluck="cliente")
	return sorted(set(con_obligaciones) | set(con_abiertos))


def generar_cliente(cliente: str, anios: list[int]) -> list[str]:
	c = frappe.get_doc("Customer", cliente)
	problemas = []
	aplican = {}
	if not c.disabled:
		aplican, problemas, bloqueado = _fechas_que_aplican(c, anios)
		if bloqueado:
			# Sin NIT utilizable no se sabe qué aplica: cerrar sus vencimientos sería perder avisos.
			return problemas
	_conciliar(c.name, anios, aplican)
	return problemas


def _fechas_que_aplican(c, anios):
	"""Devuelve {(obligacion, anio, periodo): fila de Fecha Tributaria}, los problemas de datos del cliente y si
	alguno impide saber qué le aplica."""
	problemas = []
	aplican = {}
	if not c.get("co_obligaciones"):
		return aplican, problemas, False
	t = (
		frappe.db.get_value("Tercero", c.co_tercero, ["numero_documento", "naturaleza"], as_dict=True)
		if c.co_tercero
		else None
	)
	if not t:
		return aplican, [_("{0}: no tiene tercero.").format(c.customer_name)], True
	seg = segmento(c.co_gran_contribuyente, t.naturaleza)
	for fila in c.co_obligaciones:
		for anio in anios:
			fechas = frappe.get_all(
				"Fecha Tributaria",
				filters={"obligacion": fila.obligacion, "anio": anio, "segmento": ("in", [seg, "Todos"])},
				fields=[
					"name",
					"obligacion",
					"anio",
					"periodo",
					"cifras",
					"digito_desde",
					"digito_hasta",
					"fecha",
				],
				order_by="fecha",
			)
			if not fechas:
				if anio == anios[0]:
					problemas.append(
						_("{0}: no hay fechas de {1} para {2} ({3}).").format(
							c.customer_name, fila.obligacion, anio, seg
						)
					)
				continue
			for f in fechas:
				d = digitos(t.numero_documento, int(f.cifras))
				if d is None:
					problemas.append(
						_("{0}: el documento {1} no tiene dígitos para calcular sus fechas.").format(
							c.customer_name, t.numero_documento
						)
					)
					return aplican, problemas, True
				if not f.digito_desde <= d <= f.digito_hasta:
					continue
				if getdate(f.fecha) < getdate(fila.desde):
					continue
				if fila.hasta and getdate(f.fecha) > getdate(fila.hasta):
					continue
				aplican.setdefault((f.obligacion, f.anio, f.periodo), f)
	return aplican, problemas, False


def _conciliar(cliente: str, anios: list[int], aplican: dict):
	existentes = {
		(v.obligacion, v.anio, v.periodo): v
		for v in frappe.get_all(
			"Vencimiento",
			filters={"cliente": cliente, "anio": ("in", anios)},
			fields=[
				"name",
				"obligacion",
				"anio",
				"periodo",
				"estado",
				"cerrado_por_sistema",
				"fecha_tributaria",
			],
		)
	}
	for clave, f in aplican.items():
		v = existentes.get(clave)
		if not v:
			_crear(cliente, f)
			continue
		if v.estado == "No aplica" and v.cerrado_por_sistema:
			_cambiar_estado(v.name, "Pendiente", 0, _("Vuelve a aplicar a este cliente."))
			v.estado = "Pendiente"
		if v.estado in ABIERTOS and v.fecha_tributaria != f.name:
			_mover(v.name, f, _("Cambió la regla que le aplica: ahora vence el {0}.").format(f.fecha))
	for clave, v in existentes.items():
		if clave not in aplican and v.estado in ABIERTOS:
			_cambiar_estado(v.name, "No aplica", 1, _("Ya no aplica a este cliente según su ficha."))


def _crear(cliente: str, f):
	clave = {"cliente": cliente, "obligacion": f.obligacion, "anio": f.anio, "periodo": f.periodo}
	if frappe.db.exists("Vencimiento", clave):
		return
	try:
		_insertar(cliente, f)
	except (frappe.UniqueValidationError, frappe.DuplicateEntryError):
		# Otro proceso (la tarea nocturna o un guardado) lo creó entre la lectura y esta escritura.
		pass


def _insertar(cliente: str, f):
	frappe.get_doc(
		{
			"doctype": "Vencimiento",
			"cliente": cliente,
			"obligacion": f.obligacion,
			"anio": f.anio,
			"periodo": f.periodo,
			"fecha_tributaria": f.name,
			"fecha_vencimiento": f.fecha,
			"estado": "Pendiente",
			"asignado_a": responsable(),
		}
	).insert(ignore_permissions=True)


def _cambiar_estado(nombre: str, estado: str, por_sistema: int, motivo: str):
	doc = frappe.get_doc("Vencimiento", nombre)
	doc.estado = estado
	doc.cerrado_por_sistema = por_sistema
	doc.flags.por_sistema = True
	doc.save(ignore_permissions=True)
	doc.add_comment("Comment", motivo)


def _mover(nombre: str, f, motivo: str):
	doc = frappe.get_doc("Vencimiento", nombre)
	doc.fecha_tributaria = f.name
	doc.fecha_vencimiento = f.fecha
	doc.save(ignore_permissions=True)
	doc.add_comment("Comment", motivo)


def propagar_fecha(fecha_doc, anterior):
	for nombre in frappe.get_all(
		"Vencimiento", filters={"fecha_tributaria": fecha_doc.name, "estado": ("in", ABIERTOS)}, pluck="name"
	):
		_mover(nombre, fecha_doc, _("La fecha cambió del {0} al {1}.").format(anterior, fecha_doc.fecha))


def al_guardar_cliente(doc, method=None):
	if problemas := generar(cliente=doc.name):
		frappe.msgprint("<br>".join(problemas), title=_("Vencimientos"), indicator="orange")
