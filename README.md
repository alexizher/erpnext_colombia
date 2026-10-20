### ERPNext Colombia

Localización colombiana para ERPNext: PUC, terceros, impuestos, DIAN y exógena

### Dónde está cada cosa

- **Oficina**, en la barra de íconos de ERPNext: el tablero de vencimientos, los vencimientos, los clientes, el reporte por cliente, los honorarios (facturas y reporte por cliente), los prospectos y, en Configuración, las fechas tributarias, las obligaciones y la configuración de vencimientos y de honorarios.
- **Contabilidad → Terceros y NIIF**, al final del menú: los terceros, los estados financieros de los grupos 2 y 3 (cada uno abierto con su plantilla), el balance de prueba por tercero y el auxiliar por tercero.

Las reglas contables (tercero obligatorio en las cuentas 13 y 22 a 25, clasificación NIIF, tercero en facturas, pagos y asientos) aplican solo a las empresas con país Colombia que usan el PUC. Los campos de tercero y certificación de la Ley 222 solo aparecen en la ficha de una empresa colombiana.

Al crear una empresa colombiana con la plantilla "Colombia PUC", la app corrige las cuentas por defecto que ERPNext deja mal (por cobrar 130505, por pagar 2205, recibido no facturado 233595, redondeo 429581, entre otras) y apaga el inventario perpetuo. Solo pasa al crearla: los cambios que se hagan después en la empresa se respetan.

### Terceros

Todo cliente y proveedor tiene un tercero, también los del exterior: la dimensión contable y la exógena lo necesitan. Un extranjero se registra con el documento 42 (identificación extranjera) o 43 (sin identificación del exterior) y su país. La DIAN (800197268-4) queda creada como tercero y proveedor para las retenciones y los pagos de impuestos.

El **balance de prueba por tercero** da por cuenta y tercero el saldo inicial, los débitos, los créditos y el saldo final. El **auxiliar por tercero** lista los movimientos con su saldo corrido. Los dos aceptan una cuenta de grupo y traen sus subcuentas. Como en ERPNext, lo marcado como apertura cuenta como saldo inicial.

### Honorarios

En la ficha del cliente, sección "Honorarios", se anota lo que se le cobra: concepto, valor, periodicidad (mensual, bimestral, trimestral, semestral, anual o una vez) y desde cuándo. Desde el día de facturación de cada mes, la app crea una factura de venta en borrador por cliente con lo que toca ese mes. Daniela la revisa y la envía. Un mes ya facturado no se vuelve a generar, aunque su factura se cancele.

Se configura en "Configuración de honorarios": empresa que factura, artículo (la app crea "HONORARIOS"), plantilla de impuestos, día de facturación y días para pagar. El botón "Generar las facturas de este mes" no espera al día de facturación. El reporte "Honorarios por cliente" muestra lo facturado, lo pagado, el saldo y desde cuándo debe cada uno.

En un prospecto (Lead) se anotan los servicios que le interesan y el honorario propuesto. Al crear el cliente desde el prospecto, ese valor pasa a sus honorarios como cobro mensual desde el mes siguiente.

### Traducción

`erpnext_colombia/translations/es.csv` completa en español lo que Frappe y ERPNext v16 todavía no traducen: la pantalla de entrada, el saludo y los pasos de bienvenida del inicio, y los mensajes de las gráficas sin datos. Se aplica sobre la traducción oficial porque la app se instala después de ERPNext. Las pruebas de `test_traducciones.py` fallan si una versión nueva de ERPNext trae pasos de bienvenida o gráficas sin traducir.

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
