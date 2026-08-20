from pathlib import Path

path = Path('frontend/src/views/ArticulosView.vue')
text = path.read_text(encoding='utf-8')

anchor = "// Detectar redimensionamiento\nonMounted(() => {"
helpers = '''// === CARGA RÁPIDA DESDE TARJETAS ===
const quickQuantities = ref({})

const getCartItem = (articulo) => cart.items.find(item => item.articulo.clave === articulo.clave)
const isInCart = (articulo) => Boolean(getCartItem(articulo))

const getQuickStep = (articulo) => {
  const campoa1 = (articulo.campoa1 || '').toLowerCase()
  const mts2 = parseFloat(articulo.mts2) || 0
  return campoa1 === 'a' && mts2 > 0 ? mts2 : 1
}

const getQuickQuantity = (articulo) => {
  const stored = quickQuantities.value[articulo.clave]
  if (stored !== undefined && stored !== null && stored !== '') return Number(stored)
  const existing = getCartItem(articulo)
  if (existing) return Number(existing.cantidad)
  return getQuickStep(articulo)
}

const setQuickQuantity = (articulo, value) => {
  const step = getQuickStep(articulo)
  const parsed = Number(value)
  let next = Number.isFinite(parsed) && parsed > 0 ? parsed : step
  if ((articulo.campoa1 || '').toLowerCase() === 'a' && step > 0) {
    next = Math.max(step, Math.ceil(next / step) * step)
  } else {
    next = Math.max(1, next)
  }
  quickQuantities.value = { ...quickQuantities.value, [articulo.clave]: Number(next.toFixed(3)) }
}

const incrementQuickQuantity = (articulo) => setQuickQuantity(articulo, getQuickQuantity(articulo) + getQuickStep(articulo))
const decrementQuickQuantity = (articulo) => setQuickQuantity(articulo, Math.max(getQuickStep(articulo), getQuickQuantity(articulo) - getQuickStep(articulo)))

const quickQuantityHelper = (articulo) => {
  const campoa1 = (articulo.campoa1 || '').toLowerCase()
  const mts2 = parseFloat(articulo.mts2) || 0
  if (campoa1 === 'a' && mts2 > 0) {
    const cajas = Math.round(getQuickQuantity(articulo) / mts2)
    return `${cajas} caja${cajas === 1 ? '' : 's'} · ${mts2} m²/caja`
  }
  return isInCart(articulo) ? `En pedido: ${getCartItem(articulo).cantidad}` : ''
}

const quickAddToCart = (articulo) => {
  const cantidad = getQuickQuantity(articulo)
  const existing = getCartItem(articulo)
  if (existing) {
    cart.updateQuantity(articulo.clave, cantidad)
  } else {
    cart.add(articulo, cantidad)
  }
  quickQuantities.value = { ...quickQuantities.value, [articulo.clave]: cantidad }
  showNotification(`${articulo.nombre}: ${cantidad} agregado${existing ? ' / actualizado' : ''} en el pedido`, 'success')
}

'''
if helpers not in text:
    text = text.replace(anchor, helpers + anchor, 1)

# Grid: permitir wrap y agregar controles inline antes del CTA.
text = text.replace('class="mt-4 pt-4 border-t border-gray-200 flex items-center justify-between"',
                    'class="mt-4 flex flex-wrap items-end gap-2 border-t border-gray-200 pt-3"', 1)

grid_marker = '''                <!-- Botón de agregar al carrito (solo si hay precio disponible) -->
                <button 
                  v-if="art.mostrar_precio && art.precio_lista"
                  @click="abrirModalCarrito(art)" 
                  class="ui-button ui-button-primary px-5 py-3 text-sm shadow-sm"
                >'''
grid_replacement = '''                <div v-if="art.mostrar_precio && art.precio_lista" class="ml-auto min-w-[150px]">
                  <div class="grid grid-cols-[36px_minmax(56px,1fr)_36px] overflow-hidden rounded-lg border border-gray-300 bg-white">
                    <button type="button" class="h-10 font-black text-gray-700 hover:bg-gray-100" @click="decrementQuickQuantity(art)" :aria-label="`Restar ${art.nombre}`">−</button>
                    <input type="number" :min="getQuickStep(art)" :step="getQuickStep(art)" :value="getQuickQuantity(art)" class="h-10 w-full border-x border-gray-200 text-center text-sm font-black text-gray-950 focus:outline-none" @change="setQuickQuantity(art, $event.target.value)" />
                    <button type="button" class="h-10 font-black text-gray-700 hover:bg-gray-100" @click="incrementQuickQuantity(art)" :aria-label="`Sumar ${art.nombre}`">+</button>
                  </div>
                  <p class="mt-1 min-h-4 text-[11px] font-semibold text-gray-500">{{ quickQuantityHelper(art) }}</p>
                </div>

                <!-- Botón de agregar/actualizar carrito -->
                <button 
                  v-if="art.mostrar_precio && art.precio_lista"
                  @click="quickAddToCart(art)" 
                  class="ui-button ui-button-primary px-4 py-2.5 text-sm shadow-sm"
                >'''
if grid_marker not in text:
    raise SystemExit('No se encontró CTA grid')
text = text.replace(grid_marker, grid_replacement, 1)
text = text.replace('<span>Agregar</span>', '<span>{{ isInCart(art) ? \'Actualizar\' : \'Agregar\' }}</span>', 1)

# Detalle: controles inline dentro del bloque de precio y CTA directo.
detail_marker = '''                  <button
                    v-if="art.mostrar_precio && art.precio_lista"
                    @click="abrirModalCarrito(art)"
                    class="ui-button ui-button-primary mt-4 w-full px-4 py-3 text-sm shadow-sm"
                  >'''
detail_replacement = '''                  <div v-if="art.mostrar_precio && art.precio_lista" class="mt-3">
                    <div class="grid grid-cols-[40px_minmax(64px,1fr)_40px] overflow-hidden rounded-lg border border-gray-300 bg-white">
                      <button type="button" class="h-10 font-black text-gray-700 hover:bg-gray-100" @click="decrementQuickQuantity(art)">−</button>
                      <input type="number" :min="getQuickStep(art)" :step="getQuickStep(art)" :value="getQuickQuantity(art)" class="h-10 w-full border-x border-gray-200 text-center text-sm font-black focus:outline-none" @change="setQuickQuantity(art, $event.target.value)" />
                      <button type="button" class="h-10 font-black text-gray-700 hover:bg-gray-100" @click="incrementQuickQuantity(art)">+</button>
                    </div>
                    <p class="mt-1 text-[11px] font-semibold text-gray-500">{{ quickQuantityHelper(art) }}</p>
                  </div>

                  <button
                    v-if="art.mostrar_precio && art.precio_lista"
                    @click="quickAddToCart(art)"
                    class="ui-button ui-button-primary mt-3 w-full px-4 py-3 text-sm shadow-sm"
                  >'''
if detail_marker not in text:
    raise SystemExit('No se encontró CTA detalle')
text = text.replace(detail_marker, detail_replacement, 1)
# Solo el CTA de detalle restante con texto plano.
text = text.replace('                    Agregar\n                  </button>', "                    {{ isInCart(art) ? 'Actualizar pedido' : 'Agregar al pedido' }}\n                  </button>", 1)

path.write_text(text, encoding='utf-8')
