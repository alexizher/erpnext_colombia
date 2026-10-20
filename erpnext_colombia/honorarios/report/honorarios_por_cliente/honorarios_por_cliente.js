frappe.query_reports["Honorarios por Cliente"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Empresa"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("Desde"),
			fieldtype: "Date",
			default: frappe.datetime.year_start(),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("Hasta"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{ fieldname: "customer", label: __("Cliente"), fieldtype: "Link", options: "Customer" },
	],
	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		// Saldo pendiente en rojo para verlo de un vistazo
		if (column.fieldname === "saldo" && data && data.saldo > 0) {
			value = `<span class="text-danger">${value}</span>`;
		}
		return value;
	},
};
