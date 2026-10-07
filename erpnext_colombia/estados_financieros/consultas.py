"""Valores que las plantillas de v16 no pueden armar solo con filtros de cuentas.

El motor de plantillas saca los asientos del cierre anual (Period Closing Voucher) de las cuentas
de resultado pero los deja en la cuenta de cierre (3605). Por eso el resultado del ejercicio y los
resultados acumulados se calculan aquí, directo del libro mayor. Cada función recibe lo que pasa
una fila "Custom API" y devuelve un valor por periodo, en positivo cuando es utilidad.
"""

import frappe
from frappe import _
from frappe.query_builder.functions import Coalesce, Sum
from frappe.utils import flt

CIERRE = "Period Closing Voucher"
RESULTADOS = ("Income", "Expense")


def _suma(empresa, desde=None, hasta=None, antes_de=None, raices=None, prefijos=None, sin_cierre=False) -> float:
	"""Créditos menos débitos del libro mayor de la empresa en las cuentas y fechas pedidas."""
	gl = frappe.qb.DocType("GL Entry")
	cuenta = frappe.qb.DocType("Account")
	consulta = (
		frappe.qb.from_(gl)
		.join(cuenta)
		.on(gl.account == cuenta.name)
		.select(Coalesce(Sum(gl.credit - gl.debit), 0))
		.where((gl.company == empresa) & (gl.is_cancelled == 0))
	)
	if raices:
		consulta = consulta.where(cuenta.root_type.isin(list(raices)))
	if prefijos:
		condicion = None
		for p in prefijos:
			c = cuenta.account_number.like(f"{p}%")
			condicion = c if condicion is None else condicion | c
		consulta = consulta.where(condicion)
	if desde:
		consulta = consulta.where(gl.posting_date >= desde)
	if hasta:
		consulta = consulta.where(gl.posting_date <= hasta)
	if antes_de:
		consulta = consulta.where(gl.posting_date < antes_de)
	if sin_cierre:
		consulta = consulta.where(gl.voucher_type != CIERRE)
	return flt(consulta.run()[0][0])


def _empresa(filters) -> str:
	"""Las funciones son llamables por API: solo responden sobre empresas que el usuario puede ver."""
	empresa = (filters or {}).get("company")
	if not empresa:
		frappe.throw(_("Falta la empresa."))
	frappe.has_permission("Company", "read", doc=empresa, throw=True)
	frappe.has_permission("GL Entry", "read", throw=True)
	if empresa not in frappe.get_list("Company", pluck="name"):
		frappe.throw(_("No tiene permiso para ver esta empresa."), frappe.PermissionError)
	return empresa


@frappe.whitelist(methods=["GET"])
def resultado_del_periodo(filters, periods, row=None):
	"""Utilidad del periodo sin los asientos de cierre: la misma del estado de resultados."""
	empresa = _empresa(filters)
	return [
		_suma(empresa, desde=p["from_date"], hasta=p["to_date"], raices=RESULTADOS, sin_cierre=True) for p in periods
	]


@frappe.whitelist(methods=["GET"])
def resultado_sin_cerrar(filters, periods, row=None):
	"""Resultados acumulados hasta el fin del periodo que aún no pasaron a patrimonio con un cierre."""
	empresa = _empresa(filters)
	return [_suma(empresa, hasta=p["to_date"], raices=RESULTADOS) for p in periods]


@frappe.whitelist(methods=["GET"])
def resultado_sin_cerrar_al_inicio(filters, periods, row=None):
	"""Lo mismo que resultado_sin_cerrar, al comienzo del periodo."""
	empresa = _empresa(filters)
	return [_suma(empresa, antes_de=p["from_date"], raices=RESULTADOS) for p in periods]


@frappe.whitelist(methods=["GET"])
def movimiento_resultados_acumulados_sin_cierre(filters, periods, row=None):
	"""Movimiento de las cuentas 36 y 37 sin los asientos de cierre (para el flujo de efectivo)."""
	empresa = _empresa(filters)
	return [
		_suma(empresa, desde=p["from_date"], hasta=p["to_date"], prefijos=("36", "37"), sin_cierre=True)
		for p in periods
	]
