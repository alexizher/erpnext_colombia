# Cómo contribuir

ERPNext Colombia es una localización de ERPNext para la normativa colombiana. El código, la documentación y el historial de git hablan de la funcionalidad y de la norma, no de quién usa la app.

## Nombres de personas

No se nombran personas reales en commits, PR, issues, README, comentarios, docstrings ni pruebas.

- Para hablar de quien usa la app se dice el rol: el contador, el usuario, el cliente, la oficina.
- Las pruebas usan datos ficticios: nombres como "Ana Pérez Gómez", NIT inventados y correos de `example.com`.
- Tampoco van nombres de empresas reales ni dominios propios en ejemplos o pruebas. La DIAN y otras entidades públicas sí se nombran cuando la norma lo pide.

## Commits

Formato [Conventional Commits](https://www.conventionalcommits.org/es/):

```
<tipo>: <qué cambia en la app>

<por qué, en términos de la funcionalidad o la norma>
```

Tipos: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`.

El mensaje describe el comportamiento y, si aplica, la norma que lo exige (resolución DIAN, decreto, artículo del Estatuto Tributario). No cuenta para quién se hizo ni quién lo pidió.

| Evitar | Mejor |
|---|---|
| `feat: lista de tipos como la del programa que usaba la clienta` | `feat: tipo de contribuyente con la clasificación usual en Colombia` |
| `fix: lo que reportaron en la factura` | `fix: la factura en borrador toma el periodo del mes facturado` |

## Pruebas

Cada cambio de comportamiento llega con su prueba en `erpnext_colombia/tests/`. Se corren dentro del bench:

```
bench --site <sitio> run-tests --app erpnext_colombia
```
