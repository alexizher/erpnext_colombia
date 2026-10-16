frappe.views.calendar["Vencimiento"] = {
	field_map: {
		start: "fecha_vencimiento",
		end: "fecha_vencimiento",
		id: "name",
		title: "titulo",
		allDay: "allDay",
		color: "color",
	},
	filters: [
		{ fieldtype: "Link", fieldname: "cliente", options: "Customer", label: __("Cliente") },
		{ fieldtype: "Link", fieldname: "obligacion", options: "Obligacion Tributaria", label: __("Obligación") },
	],
	get_events_method: "frappe.desk.calendar.get_events",
};
