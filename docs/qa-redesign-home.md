# QA — Rediseño de home de Revendedores

Validación final del epic #19 y de los issues #20–#24.

## Viewports mínimos

- 360 × 800
- 390 × 844
- 768 × 1024
- 1024 × 768
- 1366 × 768
- 1440 × 900
- desktop ancho

En todos los casos verificar que no exista scroll horizontal accidental.

## Flujo principal

1. Iniciar sesión con un revendedor de prueba.
2. Abrir Productos.
3. Confirmar que búsqueda y condiciones comerciales aparecen antes del catálogo sin bloques redundantes.
4. Cambiar condición de pago, Retira/Reparto y Con/Sin impuestos; confirmar actualización de precios.
5. Agregar un artículo normal desde su card usando `- / cantidad / +`.
6. Si existe un artículo por m²/caja, ingresar una cantidad no múltiplo y confirmar el ajuste al siguiente múltiplo válido.
7. Confirmar que volver a agregar el mismo artículo actualiza la línea y no crea otra línea visual.
8. En desktop abrir/cerrar el sidebar de pedido y verificar que el catálogo recupera ancho.
9. Desde el sidebar editar cantidad, eliminar una línea y comprobar total/peso.
10. En mobile/tablet abrir el drawer desde `Ver pedido`, editar cantidades y cerrarlo con `Escape`.
11. Abrir `Carga rápida` y realizar solo con teclado: código → Enter → cantidad → Enter → siguiente código.
12. Probar código inexistente; debe informar error y devolver foco al código.
13. Probar un código ya presente; la carga rápida debe acumular cantidad.
14. Navegar a `Revisar pedido`, validar condiciones y observaciones.
15. Enviar el pedido una sola vez y confirmar pantalla `Pedido enviado`.
16. Verificar `Ver mis pedidos` y `Armar otro pedido`.

## Accesibilidad

- Todos los steppers críticos deben poder utilizarse con teclado.
- Foco visible en botones, inputs y enlaces.
- Drawer móvil y carga rápida cierran con `Escape`.
- Carga rápida mantiene el foco dentro del diálogo con Tab/Shift+Tab y devuelve foco al control que la abrió.
- Al abrir modal/drawer se bloquea el scroll del body y se restaura al cerrar.
- Mensajes de error de carga rápida usan `role=alert`.
- Botones touch principales deben tener alrededor de 44 px de alto.

## Regresión funcional

Verificar que siguen funcionando:

- búsqueda y autocompletado;
- Ofertas y Discontinuados;
- favoritos;
- vista Grilla/Detalle;
- paginación;
- condición de pago;
- Retira/Reparto;
- Con/Sin impuestos;
- cantidades enteras y decimales/m²;
- persistencia del carrito;
- checkout idempotente;
- precio autoritativo de backend;
- snapshot comercial y observaciones;
- estados de emails y reintentos;
- pantalla final y emails sin lenguaje de pago online.

## Criterio de cierre

- Backend tests verdes.
- Django `check` verde.
- Frontend build verde.
- 0 errores JavaScript durante el flujo.
- 0 respuestas HTTP 500.
- Sin duplicación de pedidos ni líneas por doble click.
- El armado de un pedido de varios artículos requiere menos navegación que antes del rediseño.
