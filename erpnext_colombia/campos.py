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
	"Customer": [_tercero("customer_name")],
	"Supplier": [_tercero("supplier_name")],
	"Company": [{**_tercero("tax_id"), "reqd": 0}],
}
