frappe.query_reports["Vencimientos por Cliente"] = {
	filters: [
		{ fieldname: "anio", label: __("Año"), fieldtype: "Int", default: new Date().getFullYear() },
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
