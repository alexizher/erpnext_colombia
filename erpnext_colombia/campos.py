def _tercero(insert_after):
	return {
		"fieldname": "co_tercero",
		"label": "Tercero",
		"fieldtype": "Link",
		"options": "Tercero",
		"insert_after": insert_after,
		"reqd": 1,
		"in_standard_filter": 1,
	}


CAMPOS = {
	"Customer": [
		_tercero("customer_name"),
		{
			"fieldname": "co_seccion_obligaciones",
			"label": "Obligaciones tributarias",
			"fieldtype": "Section Break",
			"insert_after": "co_tercero",
			"collapsible": 1,
		},
		{
			"fieldname": "co_gran_contribuyente",
			"label": "Gran contribuyente",
			"fieldtype": "Check",
			"insert_after": "co_seccion_obligaciones",
		},
		{
			"fieldname": "co_empresa_contable",
			"label": "Empresa en este sistema",
			"fieldtype": "Link",
			"options": "Company",
			"insert_after": "co_gran_contribuyente",
			"description": "Solo si se le lleva la contabilidad aquí.",
		},
		{
			"fieldname": "co_obligaciones",
			"label": "Obligaciones",
			"fieldtype": "Table",
			"options": "Obligacion del Cliente",
			"insert_after": "co_empresa_contable",
		},
	],
	"Supplier": [_tercero("supplier_name")],
	"Company": [
		{**_tercero("tax_id"), "reqd": 0},
		{
			"fieldname": "co_seccion_certificacion",
			"label": "Certificación de estados financieros",
			"fieldtype": "Section Break",
			"insert_after": "co_tercero",
			"collapsible": 1,
		},
		{
			"fieldname": "co_representante_legal",
			"label": "Representante legal",
			"fieldtype": "Data",
			"insert_after": "co_seccion_certificacion",
		},
		{
			"fieldname": "co_representante_legal_documento",
			"label": "Documento del representante legal",
			"fieldtype": "Data",
			"insert_after": "co_representante_legal",
		},
		{
			"fieldname": "co_contador",
			"label": "Contador",
			"fieldtype": "Data",
			"insert_after": "co_representante_legal_documento",
		},
		{
			"fieldname": "co_contador_tarjeta_profesional",
			"label": "Tarjeta profesional del contador",
			"fieldtype": "Data",
			"insert_after": "co_contador",
		},
		{
			"fieldname": "co_columna_revisor",
			"fieldtype": "Column Break",
			"insert_after": "co_contador_tarjeta_profesional",
		},
		{
			"fieldname": "co_revisor_fiscal",
			"label": "Revisor fiscal",
			"fieldtype": "Data",
			"insert_after": "co_columna_revisor",
			"description": "Solo si la empresa está obligada a tenerlo.",
		},
		{
			"fieldname": "co_revisor_fiscal_tarjeta_profesional",
			"label": "Tarjeta profesional del revisor fiscal",
			"fieldtype": "Data",
			"insert_after": "co_revisor_fiscal",
		},
	],
	"Account": [
		{
			"fieldname": "co_clasificacion_niif",
			"label": "Clasificación NIIF",
			"fieldtype": "Select",
			"options": "\nCorriente\nNo corriente",
			"insert_after": "account_type",
			"description": "Corriente o no corriente en el estado de situación financiera.",
		}
	],
}
