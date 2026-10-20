frappe.ui.form.on("Configuracion de Honorarios", {
	refresh(frm) {
		frm.add_custom_button(__("Generar las facturas de este mes"), () => {
			frappe.call({
				method: "erpnext_colombia.honorarios.doctype.configuracion_de_honorarios.configuracion_de_honorarios.generar_ahora",
				freeze: true,
				callback: ({ message }) => {
					const n = (message || []).length;
					frappe.msgprint(
						n
							? __("Se crearon {0} borradores. Están en Facturas de honorarios.", [
									n,
							  ])
							: __("No había facturas nuevas para este mes.")
					);
				},
			});
		});
	},
});
