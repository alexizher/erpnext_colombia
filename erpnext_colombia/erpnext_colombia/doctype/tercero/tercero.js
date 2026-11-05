// El tipo de contribuyente muestra solo los de la naturaleza escogida y propone las responsabilidades.
const METODO = "erpnext_colombia.contribuyente.opciones";

function filtrar_tipos(frm) {
	if (!frm.doc.naturaleza) return;
	frappe.call(METODO, { naturaleza: frm.doc.naturaleza }).then(({ message }) => {
		frm.set_df_property("tipo_contribuyente", "options", ["", ...message.tipos]);
		if (frm.doc.tipo_contribuyente && !message.tipos.includes(frm.doc.tipo_contribuyente)) {
			frm.set_value("tipo_contribuyente", "");
		}
	});
}

frappe.ui.form.on("Tercero", {
	refresh: filtrar_tipos,
	naturaleza: filtrar_tipos,
	tipo_contribuyente(frm) {
		if (!frm.doc.tipo_contribuyente) return;
		frappe
			.call(METODO, { naturaleza: frm.doc.naturaleza, tipo: frm.doc.tipo_contribuyente })
			.then(({ message }) => frm.set_value(message.responsabilidades));
	},
});
