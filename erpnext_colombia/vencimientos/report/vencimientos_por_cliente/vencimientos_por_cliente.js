frappe.query_reports["Vencimientos por Cliente"] = {
	filters: [
		{
			fieldname: "anio",
			label: __("Año de vencimiento"),
			fieldtype: "Int",
			default: new Date().getFullYear(),
			// El periodo de diciembre vence en enero: "Diciembre de 2030" aparece en 2031.
			description: __("Diciembre vence en enero del año siguiente."),
		},
		{ fieldname: "cliente", label: __("Cliente"), fieldtype: "Link", options: "Customer" },
		{ fieldname: "obligacion", label: __("Obligación"), fieldtype: "Link", options: "Obligacion Tributaria" },
		{
			fieldname: "estado",
			label: __("Estado"),
			fieldtype: "Select",
			options: ["", "Pendiente", "En preparación", "Presentada", "Pagada", "No aplica"],
		},
	],
};
