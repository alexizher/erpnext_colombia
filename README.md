### ERPNext Colombia

Localización colombiana para ERPNext: PUC, terceros, impuestos, DIAN y exógena

### Dónde está cada cosa

- **Oficina**, en la barra de íconos de ERPNext: el tablero de vencimientos, los vencimientos, los clientes, el reporte por cliente y, en Configuración, las fechas tributarias y las obligaciones.
- **Contabilidad → Terceros y NIIF**, al final del menú: los terceros y los estados financieros de los grupos 2 y 3, cada uno abierto con su plantilla.

Las reglas contables (tercero obligatorio en las cuentas 13 y 22 a 25, clasificación NIIF, tercero en facturas, pagos y asientos) aplican solo a las empresas con país Colombia que usan el PUC. Los campos de tercero y certificación de la Ley 222 solo aparecen en la ficha de una empresa colombiana.

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
