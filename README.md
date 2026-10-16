### ERPNext Colombia

Localización colombiana para ERPNext: PUC, terceros, impuestos, DIAN y exógena

### Vencimientos

El módulo Vencimientos lleva el calendario DIAN de cada cliente. En la ficha del cliente (sección "Obligaciones tributarias") se marcan sus obligaciones: renta, IVA bimestral o cuatrimestral, retención en la fuente, exógena y Régimen Simple. Con el NIT del tercero, la app crea un vencimiento por obligación y periodo, con su estado y el radicado.

Cada noche se concilian los vencimientos y se abre un ToDo cuando falta poco. Los lunes a las 7:00 sale un resumen por correo, y una revisión semanal avisa si cambia el calendario publicado por la DIAN.

Se configura en "Configuración de vencimientos": responsable, días de anticipación (15 por defecto), correos que reciben la alerta de la DIAN y páginas vigiladas.

Las fechas vienen en `erpnext_colombia/vencimientos/fechas/<año>.json`, transcritas del calendario tributario de la DIAN. Las de cada año nuevo llegan con una versión nueva de la app. Una fecha corregida a mano en "Fecha Tributaria" no se sobrescribe al actualizar.

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch main
bench install-app erpnext_colombia
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/erpnext_colombia
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### License

gpl-3.0
