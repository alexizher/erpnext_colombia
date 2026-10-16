from frappe import _


def cliente(data):
	data.setdefault("non_standard_fieldnames", {})["Vencimiento"] = "cliente"
	data.setdefault("transactions", []).append({"label": _("Vencimientos"), "items": ["Vencimiento"]})
	return data
