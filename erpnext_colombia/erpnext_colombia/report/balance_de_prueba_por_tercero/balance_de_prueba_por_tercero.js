frappe.query_reports["Balance de Prueba por Tercero"] = {
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
		{
			fieldname: "account",
			label: __("Cuenta"),
			fieldtype: "Link",
			options: "Account",
			description: __("Una cuenta de grupo trae todas sus subcuentas."),
			get_query: () => ({
				filters: { company: frappe.query_report.get_filter_value("company") },
			}),
		},
		{ fieldname: "tercero", label: __("Tercero"), fieldtype: "Link", options: "Tercero" },
	],
};
