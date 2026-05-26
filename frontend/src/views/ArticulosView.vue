<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/services/api'
import * as XLSX from 'xlsx'

import { cart } from '@/services/cart';
import FloatingCartButton from '@/components/FloatingCartButton.vue';

// Estado del modal de imagen
const showImageModal = ref(false)
const selectedArticulo = ref(null)

// Estado del modal de filtros (móvil)
const showMobileFilters = ref(false)

// Estado del modal de carrito
const modalCarrito = ref({
  visible: false,
  articulo: null,
  tipo: '', // 'C', 'A', 'M' o vacío
  cantidad: 1,
  peso: 0,
  superficie: 0,
  subtotal: 0
})

// --- Filtros ---
const modalidad = ref('retira')
const conImpuestos = ref(true)
const condicionPago = ref('')

// Estado para formas de pago
const formasPago = ref([])
const loadingFormasPago = ref(false)

// Estado de artículos
const articulos = ref([])
const loading = ref(false)
const error = ref(null)
const searchQuery = ref('')

// Autocompletado
const showSuggestions = ref(false)
const suggestions = ref([])

// Paginación
const currentPage = ref(1)
const totalPages = ref(1)
const totalItems = ref(0)
const pageSize = ref(12)
const pageSizeOptions = [12, 24, 36, 48, 60, 72, 84, 96]
const viewMode = ref('grid')

// Detectar si es escritorio
const isDesktop = ref(window.innerWidth >= 768)

// Leer query de ruta para filtros especiales (ej: ?discontinuados=1)
const route = useRoute()
const showOnlyDiscontinuados = computed(() => {
  const q = route?.query?.discontinuados
  return q === '1' || q === 'true' || q === 'S'
})

const router = useRouter()
// (Se ha eliminado el modal de ofertas: control de sesión y flags ya no son necesarios)

const showOnlyOferta = computed(() => {
  const q = route?.query?.oferta
  return q === '1' || q === 'true' || q === 'S'
})

// Control de debounce
let searchTimeout = null

const normalizePageSize = (value) => {
  const parsed = Number(value)

  if (!Number.isFinite(parsed) || parsed <= 0) {
    return 12
  }

  const matchingOption = pageSizeOptions.find(option => option === parsed)
  if (matchingOption) {
    return matchingOption
  }

  return 12
}

const pageStartItem = computed(() => {
  if (totalItems.value === 0) return 0
  return (currentPage.value - 1) * pageSize.value + 1
})

const pageEndItem = computed(() => {
  if (totalItems.value === 0) return 0
  return Math.min(currentPage.value * pageSize.value, totalItems.value)
})

const paginationItems = computed(() => {
  if (totalPages.value <= 1) {
    return [{ type: 'page', value: 1 }]
  }

  const siblingCount = isDesktop.value ? 1 : 0
  const firstPage = 1
  const lastPage = totalPages.value
  const leftSibling = Math.max(currentPage.value - siblingCount, firstPage)
  const rightSibling = Math.min(currentPage.value + siblingCount, lastPage)
  const items = []

  items.push({ type: 'page', value: firstPage })

  if (leftSibling > firstPage + 1) {
    items.push({ type: 'ellipsis', value: 'left-ellipsis' })
  }

  const middleStart = Math.max(leftSibling, firstPage + 1)
  const middleEnd = Math.min(rightSibling, lastPage - 1)

  for (let page = middleStart; page <= middleEnd; page += 1) {
    items.push({ type: 'page', value: page })
  }

  if (rightSibling < lastPage - 1) {
    items.push({ type: 'ellipsis', value: 'right-ellipsis' })
  }

  if (lastPage > firstPage) {
    items.push({ type: 'page', value: lastPage })
  }

  return items
})

// Función para formatear moneda
const formatCurrency = (value) => {
  const number = parseFloat(value)
  if (isNaN(number)) return value
  return new Intl.NumberFormat('es-ES', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(number)
}

// Formatear cantidad/stock para mostrar en la UI
const formatStock = (value) => {
  const n = parseFloat(value)
  if (isNaN(n)) return value || '0'
  // Mostrar sin decimales si es entero, sino hasta 2 decimales
  const opts = Number.isInteger(n) ? { maximumFractionDigits: 0 } : { minimumFractionDigits: 0, maximumFractionDigits: 2 }
  return n.toLocaleString('es-AR', opts)
}

// Función para formatear fecha en formato dd-mm-aaaa
const formatDate = (dateString) => {
  if (!dateString) return ''
  
  try {
    // Intentar varios formatos de fecha que puede enviar el backend
    let date
    
    // Si viene en formato ISO (YYYY-MM-DD o YYYY-MM-DDTHH:MM:SS)
    if (dateString.includes('-')) {
      date = new Date(dateString)
    }
    // Si viene en formato DD/MM/YYYY
    else if (dateString.includes('/')) {
      const parts = dateString.split('/')
      if (parts.length === 3) {
        // Asumir DD/MM/YYYY
        date = new Date(parts[2], parts[1] - 1, parts[0])
      }
    }
    // Si viene como timestamp
    else if (!isNaN(dateString)) {
      date = new Date(parseInt(dateString))
    }
    else {
      // Intentar parsear directamente
      date = new Date(dateString)
    }
    
    // Verificar si la fecha es válida
    if (isNaN(date.getTime())) {
      return dateString // Devolver original si no se puede formatear
    }
    
    // Formatear a dd-mm-aaaa
    const day = date.getDate().toString().padStart(2, '0')
    const month = (date.getMonth() + 1).toString().padStart(2, '0')
    const year = date.getFullYear()
    
    return `${day}-${month}-${year}`
  } catch (error) {
    console.warn('Error formateando fecha:', dateString, error)
    return dateString // Devolver original en caso de error
  }
}

// Buscar campo de vencimiento de oferta en el objeto artículo
const ofertaExpiryFields = ['oferta_vencimiento','fecha_venc_oferta','venc_oferta','oferta_vto','oferta_fin','oferta_fecha','fecha_fin_oferta','vencimiento_oferta']
const getOfferExpiry = (art) => {
  if (!art) return null
  for (const f of ofertaExpiryFields) {
    if (art[f]) return art[f]
  }
  return null
}

// === Cargar filtros guardados del localStorage ===
const loadSavedFilters = () => {
  const savedModalidad = localStorage.getItem('articulos_modalidad')
  if (savedModalidad === 'retira' || savedModalidad === 'reparto') {
    modalidad.value = savedModalidad
  }

  const savedImpuestos = localStorage.getItem('articulos_con_impuestos')
  if (savedImpuestos === 'true') {
    conImpuestos.value = true
  } else if (savedImpuestos === 'false') {
    conImpuestos.value = false
  }

  const savedCondicion = localStorage.getItem('condicion_pago')
  if (savedCondicion && formasPago.value.some(fp => fp.id === savedCondicion)) {
    condicionPago.value = savedCondicion
  }

  const savedPageSize = localStorage.getItem('articulos_page_size')
  pageSize.value = normalizePageSize(savedPageSize)

  const savedViewMode = localStorage.getItem('articulos_view_mode')
  viewMode.value = savedViewMode === 'list' ? 'list' : 'grid'
}

// === Guardar filtros en localStorage ===
const saveFilters = () => {
  localStorage.setItem('articulos_modalidad', modalidad.value)
  localStorage.setItem('articulos_con_impuestos', String(conImpuestos.value))
  localStorage.setItem('condicion_pago', condicionPago.value)
}

const setViewMode = (mode) => {
  viewMode.value = mode === 'list' ? 'list' : 'grid'
  localStorage.setItem('articulos_view_mode', viewMode.value)
}

const updatePageSize = (value) => {
  const nextPageSize = normalizePageSize(value)

  if (nextPageSize === pageSize.value) {
    return
  }

  pageSize.value = nextPageSize
  localStorage.setItem('articulos_page_size', String(nextPageSize))
  currentPage.value = 1
  fetchArticulos()
}

// === TOAST NOTIFICATIONS (cola) ===
const toasts = ref([])

const showNotification = (message, type = 'info') => {
  const id = Date.now() + Math.random()
  const toast = { id, message, type }

  toasts.value.push(toast)

  // Eliminar automáticamente después de 3 segundos
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }, 3000)
}

// Cerrar toast manually
const removeToast = (id) => {
  toasts.value = toasts.value.filter(t => t.id !== id)
}

// === FETCH ARTÍCULOS ===
const fetchArticulos = async () => {
  loading.value = true
  error.value = null
  try {
    // Fetch de favoritos en paralelo
    const favoritesPromise = api.get('/api/favoritos/').then(res => res.data.map(fav => fav.articulo));

    const params = {
      page: currentPage.value,
      page_size: pageSize.value,
      modalidad: modalidad.value,
      con_impuestos: conImpuestos.value,
      condicion_pago: condicionPago.value
    };

    if (searchQuery.value.trim()) {
      params.search = searchQuery.value.trim();
    }

    // Si la vista pide solo discontinuados, solicitarlo al backend
    if (showOnlyDiscontinuados.value) {
      params.discontinuados = 1
    }

    if (showOnlyOferta.value) {
      params.oferta = 1
    }

    const responsePromise = api.get('/api/articulos/', { params });

    // Esperar ambas respuestas
    const [articulosResponse, favoriteArticuloIds] = await Promise.all([responsePromise, favoritesPromise]);

    const fetchedArticulos = articulosResponse.data.results;

    // Marcar favoritos y precios disponibles (comportamiento normal)
    articulos.value = fetchedArticulos.map(art => ({
      ...art,
      is_favorito: favoriteArticuloIds.includes(art.clave),
      mostrar_precio: art.mostrar_precio || false,
      consultandoPrecio: false
    }))

    totalItems.value = articulosResponse.data.count;
    totalPages.value = articulosResponse.data.total_pages;
    currentPage.value = articulosResponse.data.current_page;

    updateSuggestions();

    // Ya no mostramos modal de ofertas desde la UI
  } catch (err) {
    showNotification('No se pudieron cargar los artículos. Intente más tarde.', 'error');
    console.error('Error al cargar artículos:', err);
  } finally {
    loading.value = false;
  }
};

// === GESTIONAR FAVORITOS ===
const toggleFavorite = async (articulo) => {
  const originalIsFavorito = articulo.is_favorito;
  articulo.is_favorito = !articulo.is_favorito; // Optimistic update

  try {
    if (articulo.is_favorito) {
      await api.post('/api/favoritos/', { articulo: articulo.clave });
      showNotification('Agregado a favoritos', 'success');
      
      // Si ahora es favorito, actualizar para mostrar el precio
      articulo.mostrar_precio = true;
      // Recargar artículos para obtener precios actualizados
      fetchArticulos();
    } else {
      // El ID para DELETE es la clave del artículo
      const url = `/api/favoritos/${articulo.clave}/`.trim();
      await api.delete(url);
      showNotification('Eliminado de favoritos', 'info');
      
      // Si ya no es favorito, ocultar el precio
      articulo.mostrar_precio = false;
      articulo.precio_lista = null;
    }
  } catch (err) {
    articulo.is_favorito = originalIsFavorito; // Revert on error
    showNotification('No se pudo actualizar el favorito. Intente de nuevo.', 'error');
    console.error('Error al actualizar favorito:', err);
  }
};

// === CONSULTAR PRECIO ===
const consultarPrecio = async (articulo) => {
  try {
    // Mostrar loading en el botón
    const articuloIndex = articulos.value.findIndex(art => art.clave === articulo.clave);
    if (articuloIndex !== -1) {
      articulos.value[articuloIndex].consultandoPrecio = true;
    }

    const consultaData = {
      articulo_clave: articulo.clave,
      modalidad: modalidad.value,
      con_impuestos: conImpuestos.value,
      condicion_pago: condicionPago.value
    };
    
    console.log('Enviando consulta de precio:', consultaData);
    
    const response = await api.post('/api/consultar-precio/', consultaData);
    
    console.log('Respuesta del servidor:', response.data);
    
    if (response.data.success && response.data.articulo.precio_lista !== null) {
      // Actualizar el artículo con el precio obtenido
      if (articuloIndex !== -1) {
        articulos.value[articuloIndex].precio_lista = response.data.articulo.precio_lista;
        articulos.value[articuloIndex].mostrar_precio = true;
        articulos.value[articuloIndex].consultandoPrecio = false;
      }
      
      showNotification(`Precio: $${formatCurrency(response.data.articulo.precio_lista)}`, 'success');
    } else {
      throw new Error(`Precio no disponible: ${response.data.articulo.precio_lista}`);
    }
  } catch (err) {
    console.error('Error al consultar precio:', err);
    
    // Quitar loading del botón
    const articuloIndex = articulos.value.findIndex(art => art.clave === articulo.clave);
    if (articuloIndex !== -1) {
      articulos.value[articuloIndex].consultandoPrecio = false;
    }
    
    const errorMsg = err.response?.data?.error || err.message || 'No se pudo consultar el precio. Intente de nuevo.';
    showNotification(errorMsg, 'error');
  }
};

// === FETCH FORMAS DE PAGO ===
const fetchFormasPago = async () => {
  loadingFormasPago.value = true
  try {
    const response = await api.get('/api/formas-pago/')
    formasPago.value = response.data
    loadSavedFilters()
  } catch (err) {
    console.error('Error al cargar formas de pago:', err)
    condicionPago.value = ''
    showNotification('No se pudieron cargar las condiciones de pago.', 'error')
  } finally {
    loadingFormasPago.value = false
  }
}

// === DEBOUNCE EN BÚSQUEDA ===
watch(searchQuery, () => {
  if (searchTimeout) clearTimeout(searchTimeout)

  if (!searchQuery.value.trim()) {
    currentPage.value = 1
    fetchArticulos()
    return
  }

  searchTimeout = setTimeout(() => {
    currentPage.value = 1
    fetchArticulos()
  }, 500)
})

// Al cambiar condición de pago
watch(condicionPago, () => {
  saveFilters()
  fetchArticulos()
})

// Al cambiar otros filtros
watch([modalidad, conImpuestos], () => {
  saveFilters()
  currentPage.value = 1
  fetchArticulos()
})

// Si cambia la query `discontinuados`, recargar artículos
watch(() => route.query.discontinuados, () => {
  currentPage.value = 1
  fetchArticulos()
})

// Reaccionar cuando cambia la query `oferta`
watch(() => route.query.oferta, () => {
  currentPage.value = 1
  fetchArticulos()
})

// Registrar vistas de ofertas/discontinuados (una vez por session)
const trackArticuloView = async (tipo) => {
  const key = `view_logged_${tipo}`
  try {
    if (sessionStorage.getItem(key)) return
    await api.post('/api/track-articulos-view/', { tipo })
    sessionStorage.setItem(key, '1')
  } catch (e) {
    // no bloquear UI si falla el tracking
  }
}

watch(() => route.query.discontinuados, (val) => {
  if (val) trackArticuloView('discontinuado')
})

watch(() => route.query.oferta, (val) => {
  if (val) trackArticuloView('oferta')
})

// Actualizar sugerencias
const updateSuggestions = () => {
  const query = searchQuery.value.toLowerCase()
  if (!query) {
    suggestions.value = []
    return
  }

  suggestions.value = articulos.value
    .filter(art =>
      art.clave.toLowerCase().includes(query) ||
      art.nombre.toLowerCase().includes(query)
    )
    .slice(0, 5)
}

// Cambiar página
const changePage = (page) => {
  if (page >= 1 && page <= totalPages.value && page !== currentPage.value) {
    currentPage.value = page
    fetchArticulos()
  }
}

// Limpiar búsqueda
const clearSearch = () => {
  searchQuery.value = ''
  currentPage.value = 1
  fetchArticulos()
}

// Seleccionar sugerencia
const selectSuggestion = (articulo) => {
  searchQuery.value = articulo.nombre
  showSuggestions.value = false
  currentPage.value = 1
  fetchArticulos()
}

// Exportar a Excel (Favoritos únicamente)
const exportToExcel = async () => {
  try {
    // Mostrar loading notification
    showNotification('Preparando exportación de favoritos...', 'info')
    
    // Llamar al endpoint optimizado de backend
    const response = await api.get('/api/exportar-favoritos/', {
      params: {
        modalidad: modalidad.value,
        con_impuestos: conImpuestos.value,
        condicion_pago: condicionPago.value
      }
    })
    
    if (response.data.success) {
      const { data, total_articulos, parametros, message } = response.data
      
      if (data.length === 0) {
        showNotification('No tienes artículos favoritos para exportar.', 'info')
        return
      }
      
      // Crear archivo Excel con los datos optimizados del backend
      const excelData = data.map(art => ({
        'Clave': art.clave,
        'Nombre': art.nombre,
        'Unidad': art.unidad,
        'Peso': art.peso,
        'IVA': `${art.iva}%`,
        'Precio Actual': art.precio_actual,
        'Modalidad': art.modalidad,
        'Con Impuestos': art.con_impuestos ? 'Sí' : 'No',
        'Última Actualización': art.ultima_actualizacion,
      }))

      const worksheet = XLSX.utils.json_to_sheet(excelData)
      const workbook = XLSX.utils.book_new()
      XLSX.utils.book_append_sheet(workbook, worksheet, 'Artículos Favoritos')
      
      // Generar nombre de archivo con parámetros
      const fecha = new Date().toISOString().split('T')[0]
      const fileName = `favoritos_${parametros.modalidad}_${parametros.con_impuestos ? 'con' : 'sin'}_impuestos_${fecha}.xlsx`
      
      XLSX.writeFile(workbook, fileName)
      
      showNotification(`✅ ${total_articulos} artículos favoritos exportados correctamente.`, 'success')
      
    } else {
      showNotification('Error al preparar la exportación.', 'error')
    }
    
  } catch (error) {
    console.error('Error en exportación:', error)
    if (error.response?.data?.error) {
      showNotification(error.response.data.error, 'error')
    } else {
      showNotification('Error al exportar favoritos. Intenta nuevamente.', 'error')
    }
  }
}

// Función para abrir imagen
const openImageModal = (articulo) => {
  if (!articulo || !articulo.imagen) {
    showNotification('Este artículo no tiene imagen disponible.', 'error')
    return
  }
  selectedArticulo.value = articulo
  showImageModal.value = true
}

// Cerrar modal de imagen
const closeImageModal = () => {
  showImageModal.value = false
  selectedArticulo.value = null
}

// Cerrar modal de filtros
const closeFilterModal = () => {
  showMobileFilters.value = false
}

// Aplicar filtros (cierra modal y recarga)
const applyFilters = () => {
  saveFilters()
  currentPage.value = 1
  fetchArticulos()
  closeFilterModal()
}

// === FUNCIONES DEL MODAL DE CARRITO ===
const abrirModalCarrito = (articulo) => {
  console.log('📦 Abriendo modal para artículo:', articulo)
  
  // Si es campoa1='c', inicializar con 1 artículo y su peso correspondiente
  const cantidadInicial = 1
  const pesoInicial = articulo.campoa1 === 'c' ? (articulo.peso || 0) : 0
  
  modalCarrito.value = {
    visible: true,
    articulo: articulo,
    tipo: articulo.campoa1 || '',
    cantidad: cantidadInicial,
    peso: pesoInicial,
    superficie: 0,
    subtotal: articulo.precio_lista || 0
  }
  
  console.log('🔍 Tipo de artículo (campoa1):', articulo.campoa1)
  console.log('🔍 Tipo de stock (campoa1):', articulo.campoa1)
  console.log('📏 Peso unitario por artículo:', articulo.peso, 'kg')
  console.log('📏 Mts2:', articulo.mts2)
}

const cerrarModalCarrito = () => {
  modalCarrito.value = {
    visible: false,
    articulo: null,
    tipo: '',
    cantidad: 1,
    peso: 0,
    superficie: 0,
    subtotal: 0
  }
}

const calcularCantidadPorSuperficie = () => {
  if (modalCarrito.value.tipo === 'A' && modalCarrito.value.articulo?.mts2 > 0 && modalCarrito.value.superficie > 0) {
    // Calcular cantidad de cajas necesarias (siempre redondear hacia arriba)
    const cajas = Math.ceil(modalCarrito.value.superficie / modalCarrito.value.articulo.mts2)
    modalCarrito.value.cantidad = cajas
    
    // Calcular subtotal
    modalCarrito.value.subtotal = cajas * (modalCarrito.value.articulo.precio_lista || 0)
    
    console.log(`📦 Superficie: ${modalCarrito.value.superficie} m²`)
    console.log(`📦 M² por caja: ${modalCarrito.value.articulo.mts2}`)
    console.log(`📦 Cajas calculadas: ${cajas}`)
  }
}

const agregarAlCarrito = () => {
  if (!modalCarrito.value.articulo || modalCarrito.value.cantidad <= 0) {
    showNotification('Debe ingresar una cantidad válida', 'error')
    return
  }
  
  let cantidadAAgregar = modalCarrito.value.cantidad
  let superficieReal = modalCarrito.value.superficie
  
  // Validación especial para tipo A con mts2: asegurar que la superficie sea múltiplo
  if (modalCarrito.value.tipo === 'A' && modalCarrito.value.articulo.mts2 > 0 && modalCarrito.value.superficie > 0) {
    // Recalcular la cantidad de cajas necesarias para cubrir la superficie
    const cajasNecesarias = Math.ceil(modalCarrito.value.superficie / modalCarrito.value.articulo.mts2)
    
    // Calcular la superficie real que se cubrirá (múltiplo exacto)
    superficieReal = cajasNecesarias * modalCarrito.value.articulo.mts2
    
    // La cantidad a agregar es la superficie total en m² (no las cajas)
    cantidadAAgregar = superficieReal
    
    console.log(`🔧 Superficie solicitada: ${modalCarrito.value.superficie} m²`)
    console.log(`� Cajas necesarias: ${cajasNecesarias}`)
    console.log(`📏 Superficie real (múltiplo): ${superficieReal} m²`)
    console.log(`� Cantidad a agregar al carrito: ${cantidadAAgregar} m²`)
  }
  
  console.log('🛒 Agregando al carrito:', {
    clave: modalCarrito.value.articulo.clave,
    nombre: modalCarrito.value.articulo.nombre,
    cantidad: cantidadAAgregar,
    peso: modalCarrito.value.peso,
    superficie: superficieReal
  })
  
  // Agregar al carrito pasando la cantidad como segundo parámetro
  cart.add(modalCarrito.value.articulo, cantidadAAgregar)
  
  // Mostrar notificación personalizada
  let mensaje = `${modalCarrito.value.cantidad} unidad(es) agregada(s) al carrito`
  
  const campoa1Lower = (modalCarrito.value.articulo.campoa1 || '').toLowerCase()
  
  if (modalCarrito.value.tipo === 'A' && modalCarrito.value.superficie > 0) {
    const cajas = Math.ceil(modalCarrito.value.superficie / modalCarrito.value.articulo.mts2)
    mensaje = `${superficieReal.toFixed(2)} m² agregados al carrito (${cajas} caja${cajas > 1 ? 's' : ''})`
  } else if (campoa1Lower === 'c' && modalCarrito.value.peso > 0) {
    // Para campoa1='c': mostrar cantidad de artículos y peso total
    mensaje = `${modalCarrito.value.cantidad} artículo(s) agregado(s) (${modalCarrito.value.peso} kg total)`
  } else if ((modalCarrito.value.tipo === 'C' || modalCarrito.value.tipo === 'M') && modalCarrito.value.peso > 0) {
    mensaje += ` (${modalCarrito.value.peso} kg)`
  }
  
  showNotification(mensaje, 'success')
  
  // Cerrar modal
  cerrarModalCarrito()
}

// Watch para calcular subtotal y peso cuando cambia la cantidad
watch(() => modalCarrito.value.cantidad, (newCantidad, oldCantidad) => {
  if (!modalCarrito.value.articulo || newCantidad <= 0) return

  const campoa1Lower = (modalCarrito.value.articulo.campoa1 || '').toLowerCase()

  // Si es campoa1='c', calcular el peso automáticamente (peso total = cantidad × peso_unitario)
  if (campoa1Lower === 'c') {
    const pesoUnitario = parseFloat(modalCarrito.value.articulo.peso) || 0
    modalCarrito.value.peso = newCantidad * pesoUnitario
    console.log(`⚖️ Calculando peso total: ${newCantidad} artículos × ${pesoUnitario} kg = ${modalCarrito.value.peso} kg`)
  }
  
  // SIEMPRE calcular subtotal por cantidad de artículos (no por peso)
  modalCarrito.value.subtotal = newCantidad * (modalCarrito.value.articulo.precio_lista || 0)
})

// Watch para calcular cantidad cuando cambia el peso (solo para campoa1='c')
watch(() => modalCarrito.value.peso, (newPeso, oldPeso) => {
  console.log('🔔 Watch de peso disparado:', { newPeso, oldPeso, articulo: modalCarrito.value.articulo?.clave, campoa1: modalCarrito.value.articulo?.campoa1 })
  
  if (!modalCarrito.value.articulo) {
    console.log('❌ No hay artículo en el modal')
    return
  }

  // Si es campoa1='c' (mayúscula o minúscula) y se cambió el peso manualmente
  const campoa1Lower = (modalCarrito.value.articulo.campoa1 || '').toLowerCase()
  
  if (campoa1Lower === 'c' && newPeso > 0) {
    const pesoUnitario = parseFloat(modalCarrito.value.articulo.peso) || 1
    const cantidadCalculada = newPeso / pesoUnitario
    
    console.log(`🔢 Datos del cálculo:`)
    console.log(`   Peso ingresado: ${newPeso} kg`)
    console.log(`   Peso unitario: ${pesoUnitario} kg/artículo`)
    console.log(`   Cantidad calculada: ${cantidadCalculada} artículos`)
    
    // Redondear para evitar decimales extraños
    const cantidadRedondeada = Math.round(cantidadCalculada * 100) / 100
    
    // Solo actualizar si es diferente (para evitar loops infinitos)
    if (Math.abs(modalCarrito.value.cantidad - cantidadRedondeada) > 0.01) {
      console.log(`✅ Actualizando cantidad de ${modalCarrito.value.cantidad} a ${cantidadRedondeada}`)
      modalCarrito.value.cantidad = cantidadRedondeada
      
      // El subtotal se calculará automáticamente por el watch de cantidad
    } else {
      console.log(`⏭️ No se actualiza, cantidad ya es ${cantidadRedondeada}`)
    }
  } else {
    console.log(`⏭️ No aplica cálculo. campoa1='${campoa1Lower}', peso=${newPeso}`)
  }
  
  // Para tipos C y M que NO son campoa1='c', calcular subtotal por peso
  if (campoa1Lower !== 'c' && (modalCarrito.value.tipo === 'C' || modalCarrito.value.tipo === 'M') && newPeso > 0) {
    modalCarrito.value.subtotal = newPeso * (modalCarrito.value.articulo.precio_lista || 0)
  }
})

// Detectar redimensionamiento
onMounted(() => {
  window.addEventListener('resize', () => {
    isDesktop.value = window.innerWidth >= 768
  })

  fetchFormasPago()
  fetchArticulos()

  if (route.query.discontinuados) {
    trackArticuloView('discontinuado')
  }
  if (route.query.oferta) {
    trackArticuloView('oferta')
  }
})
</script>

<template>
  <div class="flex h-screen bg-gray-50 overflow-hidden">
    <main class="flex-1 overflow-y-auto p-6 bg-gray-50 main-content">
      <div class="w-full">

        <h1 class="text-2xl font-bold mb-6 text-gray-900">Gestión de Artículos</h1>

        <!-- Barra de búsqueda -->
        <div class="mb-6 relative">
          <div class="flex flex-col sm:flex-row gap-3">
            <div class="flex-grow relative">
              <input
                v-model="searchQuery"
                placeholder="Buscar por clave o nombre..."
                class="w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
              />
              <div class="absolute inset-y-0 left-0 flex items-center pl-3">
                <div v-if="loading && searchQuery" class="animate-spin h-5 w-5 text-gray-400">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                </div>
                <span v-else class="text-gray-400">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </span>
              </div>
            </div>

            <button
              @click="exportToExcel"
              class="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition flex items-center gap-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Exportar
            </button>

            <button
              @click="clearSearch"
              class="px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition"
            >
              Limpiar
            </button>
          </div>

          <!-- Autocompletado -->
          <ul
            v-if="showSuggestions && suggestions.length > 0"
            class="absolute z-50 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto"
          >
            <li
              v-for="sug in suggestions"
              :key="sug.clave"
              @click="selectSuggestion(sug)"
              class="px-4 py-2 hover:bg-red-100 cursor-pointer border-b last:border-b-0 text-sm"
            >
              <strong>{{ sug.clave }}</strong> - {{ sug.nombre }}
            </li>
          </ul>
        </div>

        <!-- Botón Filtros (solo móvil) -->
        <button
          v-if="!isDesktop"
          @click="showMobileFilters = true"
          class="w-full mb-4 flex items-center justify-between bg-white hover:bg-gray-50 border border-gray-300 rounded-lg shadow-sm py-3 px-4 font-medium text-gray-700"
        >
          <span class="flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.207A1 1 0 013 6.5V4z" />
            </svg>
            Filtros
          </span>
          <span
            v-if="modalidad !== 'retira' || !conImpuestos || condicionPago"
            class="w-2 h-2 bg-red-500 rounded-full"
          ></span>
        </button>

        <!-- Filtros en escritorio (versión compacta) -->
        <div v-if="isDesktop" class="bg-white p-3 rounded-lg shadow-sm mb-6 border border-gray-200">
          <h3 class="text-lg font-medium text-gray-900 mb-3">Filtros</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <!-- Condición de Pago -->
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Condición de Pago</label>
              <select
                v-model="condicionPago"
                class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-red-500"
                :disabled="loadingFormasPago"
              >
                <option v-for="fp in formasPago" :key="fp.id" :value="fp.id">
                  {{ fp.nombre }}
                  <template v-if="fp.descuento > 0"> (-{{ fp.descuento }}%)</template>
                  <template v-if="fp.punitorio > 0"> (punitorio +{{ fp.punitorio }}%)</template>
                </option>
              </select>
              <p v-if="loadingFormasPago" class="text-xs text-gray-500 mt-1">Cargando...</p>
            </div>

            <!-- Modalidad -->
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Modalidad</label>
              <select
                v-model="modalidad"
                class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-red-500"
              >
                <option value="retira">Retira</option>
                <option value="reparto">Reparto</option>
              </select>
            </div>

            <!-- Precio -->
            <div>
              <label class="block text-xs font-medium text-gray-700 mb-1">Precio</label>
              <select
                v-model="conImpuestos"
                class="w-full px-2 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-red-500"
              >
                <option :value="true">Con impuestos</option>
                <option :value="false">Sin impuestos</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Mensaje de error -->
        <div v-if="error" class="p-4 mb-6 bg-red-100 text-red-700 border border-red-300 rounded">
          {{ error }}
        </div>

        <div class="mb-6 flex flex-col gap-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p class="text-sm font-medium text-gray-900">Visualización de productos</p>
            <p class="text-sm text-gray-500">
              Mostrando {{ pageStartItem }}-{{ pageEndItem }} de {{ totalItems }} artículos
            </p>
          </div>

          <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
            <label class="flex items-center gap-2 text-sm text-gray-700">
              <span>Productos por página</span>
              <select
                :value="pageSize"
                class="rounded-lg border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-500"
                @change="updatePageSize($event.target.value)"
              >
                <option v-for="size in pageSizeOptions" :key="size" :value="size">
                  {{ size }}
                </option>
              </select>
            </label>

            <div class="inline-flex rounded-lg border border-gray-300 bg-gray-50 p-1">
              <button
                type="button"
                class="rounded-md px-3 py-2 text-sm font-medium transition"
                :class="viewMode === 'grid' ? 'bg-white text-red-600 shadow-sm' : 'text-gray-600 hover:text-gray-900'"
                @click="setViewMode('grid')"
              >
                Grilla
              </button>
              <button
                type="button"
                class="rounded-md px-3 py-2 text-sm font-medium transition"
                :class="viewMode === 'list' ? 'bg-white text-red-600 shadow-sm' : 'text-gray-600 hover:text-gray-900'"
                @click="setViewMode('list')"
              >
                Detalle
              </button>
            </div>
          </div>
        </div>

        <!-- Cargando -->
        <div v-if="loading && articulos.length === 0" class="flex justify-center py-8">
          <p class="text-lg text-gray-600">Cargando artículos...</p>
        </div>

        <!-- Vista grilla -->
        <div
          v-else-if="articulos.length > 0 && viewMode === 'grid'"
          class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4"
        >
          <div
            v-for="art in articulos"
            :key="art.clave"
            :class="[
              'rounded-lg shadow flex flex-col overflow-hidden transition transform hover:scale-102 hover:shadow-xl relative',
              art.discontinuado === 'S' ? 'bg-yellow-50 border border-yellow-300 opacity-95' : '',
              art.oferta === 'S' ? 'bg-green-50 border border-green-300 offer-animate' : '',
              (art.discontinuado !== 'S' && art.oferta !== 'S') ? 'bg-white' : ''
            ]"
          >
            <div v-if="art.discontinuado === 'S'" class="absolute top-3 right-3 bg-yellow-500 text-white text-xs font-semibold px-2 py-1 rounded">Discontinuado</div>
            <div v-if="art.oferta === 'S'" class="absolute top-3 left-3 bg-green-600 text-white text-xs font-semibold px-2 py-1 rounded">Oferta</div>
            <!-- Imagen del artículo -->
            <div class="relative h-40 bg-gray-100 border-b">
              <img
                v-if="art.imagen"
                :src="art.imagen"
                :alt="art.nombre"
                class="w-full h-full object-contain p-3 cursor-pointer"
                @click="openImageModal(art)"
              />
              <div
                v-else
                class="w-full h-full flex items-center justify-center text-gray-400 text-sm"
                @click="showNotification('No hay imagen disponible', 'info')"
              >
                Sin imagen
              </div>
            </div>

            <!-- Contenido de la tarjeta -->
            <div class="p-4 flex-1 flex flex-col">
              <div class="flex justify-between items-start">
                <h3
                  class="text-lg font-bold text-gray-900 line-clamp-2 flex-1"
                  :title="art.nombre"
                >
                  {{ art.nombre }}
                </h3>
                  <!-- Mostrar fecha de vencimiento de oferta si existe -->
                  <div v-if="art.oferta === 'S'" class="ml-3">
                    <p v-if="getOfferExpiry(art)" class="text-sm text-green-800 font-semibold offer-expiry ml-3">Vence: {{ formatDate(getOfferExpiry(art)) }}</p>
                  </div>
                <button
                  @click.stop="toggleFavorite(art)"
                  class="p-1 rounded-full text-gray-400 hover:text-red-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 transition-colors duration-200"
                  :class="{ 'text-red-500': art.is_favorito }"
                  aria-label="Añadir o quitar de favoritos"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" :class="{ 'fill-current': art.is_favorito }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                  </svg>
                </button>
              </div>
              <p class="text-sm text-gray-500 mt-1">Clave: {{ art.clave }}</p>

              <div class="grid grid-cols-2 gap-3 mt-4 text-sm">
                <div>
                  <p class="text-gray-500">Unidad</p>
                  <p class="font-semibold">{{ art.unidad }}</p>
                </div>
                <div>
                  <p class="text-gray-500">Peso</p>
                  <p class="font-semibold">{{ art.peso }}</p>
                </div>
                <!-- Mostrar mts2 por caja si es mayor que 0 -->
                <div v-if="art.mts2 && parseFloat(art.mts2) > 0">
                  <p class="text-gray-500">Mts² por caja</p>
                  <p class="font-semibold text-blue-600">{{ formatCurrency(art.mts2) }} m²</p>
                </div>
                <div v-else>
                  <p class="text-gray-500">IVA</p>
                  <p class="font-semibold">{{ art.iva }}%</p>
                </div>
                <div v-if="!(art.mts2 && parseFloat(art.mts2) > 0)">
                  <p class="text-gray-500">Últ. Act.</p>
                  <p class="font-semibold">{{ formatDate(art.ultact) }}</p>
                </div>
                <!-- Mostrar IVA en la segunda fila si hay mts2 -->
                <div v-if="art.mts2 && parseFloat(art.mts2) > 0">
                  <p class="text-gray-500">IVA</p>
                  <p class="font-semibold">{{ art.iva }}%</p>
                </div>
              </div>

              <!-- Mostrar stock prominente para artículos en oferta: barra a todo ancho -->
              <div v-if="art.oferta === 'S'" class="w-full mt-4">
                <div class="w-full bg-green-700 text-white text-sm font-bold px-3 py-2 rounded-lg text-center">Stock disponible: {{ formatStock(art.stock) }}</div>
              </div>

              <div class="mt-4 pt-4 border-t border-gray-200 flex items-center justify-between">
                <!-- Mostrar precio si está disponible -->
                <div v-if="art.mostrar_precio && art.precio_lista">
                    <p class="text-red-500 text-left">Precio</p>
                    <p class="text-xl font-bold text-red-500 text-left line-clamp-1">$ {{ formatCurrency(art.precio_lista) }}</p>
                </div>
                <!-- Mostrar botón "Ver Precio" si no se muestra el precio -->
                <div v-else class="flex-1">
                    <button 
                      @click="consultarPrecio(art)"
                      :disabled="art.consultandoPrecio"
                      :class="art.consultandoPrecio ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'"
                      class="text-white px-3 py-2 rounded-lg transition text-sm flex items-center gap-2"
                    >
                      <div v-if="art.consultandoPrecio" class="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                      <span v-if="art.consultandoPrecio">Consultando...</span>
                      <span v-else>👁️ Ver Precio</span>
                    </button>
                </div>
                
                <!-- Botón de agregar al carrito (solo si hay precio disponible) -->
                <button 
                  v-if="art.mostrar_precio && art.precio_lista"
                  @click="abrirModalCarrito(art)" 
                  class="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Vista detalle -->
        <div v-else-if="articulos.length > 0" class="space-y-4">
          <article
            v-for="art in articulos"
            :key="art.clave"
            :class="[
              'overflow-hidden rounded-xl border shadow-sm transition hover:shadow-md',
              art.discontinuado === 'S' ? 'border-yellow-300 bg-yellow-50' : '',
              art.oferta === 'S' ? 'border-green-300 bg-green-50' : '',
              (art.discontinuado !== 'S' && art.oferta !== 'S') ? 'border-gray-200 bg-white' : ''
            ]"
          >
            <div class="flex flex-col gap-5 p-5 xl:flex-row xl:items-start">
              <div class="relative h-48 overflow-hidden rounded-lg border border-gray-200 bg-gray-100 xl:h-40 xl:w-40 xl:flex-shrink-0">
                <img
                  v-if="art.imagen"
                  :src="art.imagen"
                  :alt="art.nombre"
                  class="h-full w-full cursor-pointer object-contain p-3"
                  @click="openImageModal(art)"
                />
                <div
                  v-else
                  class="flex h-full w-full items-center justify-center px-4 text-center text-sm text-gray-400"
                  @click="showNotification('No hay imagen disponible', 'info')"
                >
                  Sin imagen
                </div>
              </div>

              <div class="min-w-0 flex-1">
                <div class="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div class="min-w-0">
                    <div class="mb-2 flex flex-wrap gap-2">
                      <span v-if="art.discontinuado === 'S'" class="rounded-full bg-yellow-500 px-3 py-1 text-xs font-semibold text-white">
                        Discontinuado
                      </span>
                      <span v-if="art.oferta === 'S'" class="rounded-full bg-green-600 px-3 py-1 text-xs font-semibold text-white">
                        Oferta
                      </span>
                    </div>

                    <h3 class="text-xl font-bold text-gray-900">{{ art.nombre }}</h3>
                    <p class="mt-1 text-sm text-gray-500">Clave: {{ art.clave }}</p>
                    <p v-if="art.oferta === 'S' && getOfferExpiry(art)" class="mt-2 text-sm font-semibold text-green-800">
                      Vence: {{ formatDate(getOfferExpiry(art)) }}
                    </p>
                  </div>

                  <button
                    @click.stop="toggleFavorite(art)"
                    class="self-start rounded-full p-1 text-gray-400 transition-colors duration-200 hover:text-red-500 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
                    :class="{ 'text-red-500': art.is_favorito }"
                    aria-label="Añadir o quitar de favoritos"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" :class="{ 'fill-current': art.is_favorito }" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                    </svg>
                  </button>
                </div>

                <div class="mt-5 grid grid-cols-2 gap-4 text-sm lg:grid-cols-5">
                  <div>
                    <p class="text-gray-500">Unidad</p>
                    <p class="font-semibold text-gray-900">{{ art.unidad }}</p>
                  </div>
                  <div>
                    <p class="text-gray-500">Peso</p>
                    <p class="font-semibold text-gray-900">{{ art.peso }}</p>
                  </div>
                  <div v-if="art.mts2 && parseFloat(art.mts2) > 0">
                    <p class="text-gray-500">Mts² por caja</p>
                    <p class="font-semibold text-blue-600">{{ formatCurrency(art.mts2) }} m²</p>
                  </div>
                  <div v-else>
                    <p class="text-gray-500">IVA</p>
                    <p class="font-semibold text-gray-900">{{ art.iva }}%</p>
                  </div>
                  <div>
                    <p class="text-gray-500">Últ. Act.</p>
                    <p class="font-semibold text-gray-900">{{ formatDate(art.ultact) }}</p>
                  </div>
                  <div v-if="art.mts2 && parseFloat(art.mts2) > 0">
                    <p class="text-gray-500">IVA</p>
                    <p class="font-semibold text-gray-900">{{ art.iva }}%</p>
                  </div>
                  <div>
                    <p class="text-gray-500">Stock</p>
                    <p :class="art.oferta === 'S' ? 'font-bold text-green-700' : 'font-semibold text-gray-900'">
                      {{ formatStock(art.stock) }}
                    </p>
                  </div>
                </div>
              </div>

              <div class="xl:w-72 xl:flex-shrink-0">
                <div class="rounded-xl border border-gray-200 bg-gray-50 p-4">
                  <div v-if="art.mostrar_precio && art.precio_lista">
                    <p class="text-sm text-gray-500">Precio</p>
                    <p class="mt-1 text-2xl font-bold text-red-500">$ {{ formatCurrency(art.precio_lista) }}</p>
                  </div>
                  <div v-else>
                    <button
                      @click="consultarPrecio(art)"
                      :disabled="art.consultandoPrecio"
                      :class="art.consultandoPrecio ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'"
                      class="flex w-full items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm text-white transition"
                    >
                      <div v-if="art.consultandoPrecio" class="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                      <span v-if="art.consultandoPrecio">Consultando...</span>
                      <span v-else>👁️ Ver Precio</span>
                    </button>
                  </div>

                  <button
                    v-if="art.mostrar_precio && art.precio_lista"
                    @click="abrirModalCarrito(art)"
                    class="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-white transition hover:bg-red-700"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
                    </svg>
                    Agregar al carrito
                  </button>
                </div>
              </div>
            </div>
          </article>
        </div>

        <!-- Sin resultados -->
        <div v-else-if="!loading" class="text-center py-10 text-gray-500">
          <p>No se encontraron artículos.</p>
        </div>

        <!-- Paginación -->
        <div v-if="!loading && totalPages > 1" class="mt-6 flex flex-col gap-4 rounded-lg border border-gray-200 bg-white p-4 shadow-sm lg:flex-row lg:items-center lg:justify-between">
          <div class="text-sm text-gray-700">
            Página {{ currentPage }} de {{ totalPages }}. Mostrando {{ pageStartItem }}-{{ pageEndItem }} de {{ totalItems }} artículos.
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <button
              :disabled="currentPage === 1"
              @click="changePage(1)"
              class="rounded border border-gray-300 px-3 py-2 hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-75"
            >
              Primero
            </button>
            <button
              :disabled="currentPage === 1"
              @click="changePage(currentPage - 1)"
              class="rounded border border-gray-300 px-4 py-2 hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-75"
            >
              Anterior
            </button>
            <template v-for="item in paginationItems" :key="item.value">
              <span
                v-if="item.type === 'ellipsis'"
                class="px-2 py-2 text-sm font-medium text-gray-400"
              >
                ...
              </span>
              <button
                v-else
                @click="changePage(item.value)"
                class="rounded border px-3 py-2 text-sm font-medium transition"
                :class="item.value === currentPage ? 'border-red-600 bg-red-600 text-white' : 'border-gray-300 hover:bg-gray-100'"
              >
                {{ item.value }}
              </button>
            </template>
            <button
              :disabled="currentPage === totalPages"
              @click="changePage(currentPage + 1)"
              class="rounded border border-gray-300 px-4 py-2 hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-75"
            >
              Siguiente
            </button>
            <button
              :disabled="currentPage === totalPages"
              @click="changePage(totalPages)"
              class="rounded border border-gray-300 px-3 py-2 hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-75"
            >
              Última
            </button>
          </div>
        </div>
      </div>

      <!-- Modal de filtros (móvil) -->
      <div
        v-if="showMobileFilters && !isDesktop"
        class="fixed inset-0 z-50 flex flex-col bg-white"
      >
        <div class="flex justify-between items-center p-4 border-b bg-gray-50">
          <h3 class="text-lg font-medium text-gray-900">Filtros</h3>
          <button @click="closeFilterModal" class="text-gray-500 hover:text-gray-700">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="flex-1 overflow-y-auto p-4 space-y-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Condición de Pago</label>
            <select
              v-model="condicionPago"
              class="w-full px-3 py-2 border border-gray-300 rounded text-sm"
              :disabled="loadingFormasPago"
            >
              <option v-for="fp in formasPago" :key="fp.id" :value="fp.id">
                {{ fp.nombre }}
                <span v-if="fp.descuento > 0" class="text-red-600 text-xs">(-{{ fp.descuento }}%)</span>
                <span v-if="fp.punitorio > 0" class="text-red-600 text-xs">(punitorio +{{ fp.punitorio }}%)</span>
              </option>
            </select>
            <p v-if="loadingFormasPago" class="text-xs text-gray-500 mt-1">Cargando...</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Modalidad</label>
            <select v-model="modalidad" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
              <option value="retira">Retira</option>
              <option value="reparto">Reparto</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Precio</label>
            <select v-model="conImpuestos" class="w-full px-3 py-2 border border-gray-300 rounded text-sm">
              <option :value="true">Con impuestos</option>
              <option :value="false">Sin impuestos</option>
            </select>
          </div>
        </div>
        <div class="p-4 border-t bg-gray-50">
          <button
            @click="applyFilters"
            class="w-full py-2 bg-red-600 text-white font-medium rounded hover:bg-red-700 transition"
          >
            Aplicar filtros
          </button>
        </div>
      </div>

      <!-- Modal de imagen -->
      <div
        v-if="showImageModal && selectedArticulo"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/80"
        @click="closeImageModal"
      >
        <div
          class="relative max-w-2xl w-full bg-white rounded-lg shadow-2xl p-6"
          @click.stop
        >
          <button
            @click="closeImageModal"
            class="absolute top-4 right-4 z-10 text-white bg-black/40 hover:bg-black/60 rounded-full p-2 transition"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>

          <div class="flex flex-col items-center text-center">
            <img
              :src="selectedArticulo.imagen"
              :alt="'Imagen de ' + selectedArticulo.nombre"
              class="max-w-full max-h-96 object-contain rounded-lg border mb-4"
            />
            <h3 class="text-2xl font-bold text-gray-900">{{ selectedArticulo.nombre }}</h3>
            <p class="text-lg text-gray-600">Clave: {{ selectedArticulo.clave }}</p>
            <p class="text-base text-gray-500">Unidad: {{ selectedArticulo.unidad }} | Peso: {{ selectedArticulo.peso }} kg</p>
            <p class="text-xl font-semibold text-gray-800 mt-2">
              Precio: {{ formatCurrency(selectedArticulo.precio_lista) }}
            </p>
          </div>
        </div>
      </div>

      <!-- El modal de ofertas fue eliminado -->

      <!-- Toast Notifications -->
      <transition-group
        tag="div"
        name="toast"
        class="fixed top-4 right-4 space-y-2 z-50 max-w-sm w-full"
      >
        <div
          v-for="toast in toasts"
          :key="toast.id"
          :class="{
            'bg-red-700': toast.type === 'error',
            'bg-red-600': toast.type === 'info',
            'bg-green-600': toast.type === 'success',
          }"
          class="px-5 py-3 rounded-lg shadow-lg text-white text-sm flex items-center gap-2 animate-in slide-in-from-top-2 duration-300"
          @click="removeToast(toast.id)"
        >
          <svg v-if="toast.type === 'error'" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 20c-.77 1.333.192 3 1.732 3z" />
          </svg>

          <svg v-else-if="toast.type === 'success'" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>

          <svg v-else class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>

          <span>{{ toast.message }}</span>
          <button class="ml-auto hover:bg-white/20 rounded p-1" @click.stop="removeToast(toast.id)">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </transition-group>

    <!-- Botón de Carrito Flotante (Arrastrable) -->
    <FloatingCartButton />

    <!-- Modal de Agregar al Carrito -->
    <div v-if="modalCarrito.visible" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" @click.self="cerrarModalCarrito">
      <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
        <!-- Header -->
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-xl font-bold text-gray-800">Agregar al Carrito</h3>
          <button @click="cerrarModalCarrito" class="text-gray-400 hover:text-gray-600">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Información del Artículo -->
        <div class="mb-4 p-3 bg-gray-50 rounded-lg">
          <p class="font-semibold text-gray-800">{{ modalCarrito.articulo?.nombre }}</p>
          <p class="text-sm text-gray-600">Código: {{ modalCarrito.articulo?.clave }}</p>
          <p class="text-lg font-bold text-red-600 mt-2">${{ formatCurrency(modalCarrito.articulo?.precio_lista) }}</p>
        </div>

        <!-- Formulario según tipo de artículo -->
        <div class="space-y-4">
          <!-- campoa1='c' o 'C': Artículos que se venden por peso (pero precio por cantidad) -->
          <div v-if="modalCarrito.articulo?.campoa1?.toLowerCase() === 'c'">
            <div class="mb-3 p-2 bg-blue-50 rounded border border-blue-200">
              <p class="text-xs text-blue-800">
                <span class="font-semibold">Peso por artículo:</span> {{ modalCarrito.articulo.peso }} kg
              </p>
              <p class="text-xs text-blue-600 mt-1">
                💡 Ingrese cantidad de artículos o peso total
              </p>
            </div>
            
            <label class="block text-sm font-medium text-gray-700 mb-1">Cantidad de Artículos</label>
            <input 
              v-model.number="modalCarrito.cantidad" 
              type="number" 
              min="1" 
              step="1"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
              placeholder="Ingrese cantidad de artículos"
            >
            
            <label class="block text-sm font-medium text-gray-700 mb-1 mt-3">Peso Total (kg)</label>
            <input 
              v-model.number="modalCarrito.peso" 
              type="number" 
              min="0" 
              :step="modalCarrito.articulo.peso"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
              placeholder="Ingrese peso total"
            >
            
            <div class="mt-3 p-3 bg-green-50 rounded-lg border border-green-200">
              <p class="text-sm text-gray-700">
                <span class="font-semibold">Resumen:</span> 
                <span class="text-green-600 font-bold">{{ modalCarrito.cantidad }} artículo(s)</span> = 
                <span class="text-green-600 font-bold">{{ modalCarrito.peso }} kg</span>
              </p>
            </div>
          </div>

          <!-- Tipo C o M (que NO sean campoa1='c'): Cantidad y Peso -->
          <div v-else-if="(modalCarrito.tipo === 'C' || modalCarrito.tipo === 'M') && modalCarrito.articulo?.campoa1?.toLowerCase() !== 'c'">
            <label class="block text-sm font-medium text-gray-700 mb-1">Cantidad</label>
            <input 
              v-model.number="modalCarrito.cantidad" 
              type="number" 
              min="1" 
              step="1"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
              placeholder="Ingrese cantidad"
            >
            
            <label class="block text-sm font-medium text-gray-700 mb-1 mt-3">Peso (kg)</label>
            <input 
              v-model.number="modalCarrito.peso" 
              type="number" 
              min="0" 
              step="0.01"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
              placeholder="Ingrese peso"
            >
          </div>

          <!-- Tipo A con mts2: Superficie -->
          <div v-if="modalCarrito.tipo === 'A' && modalCarrito.articulo?.mts2 > 0">
            <label class="block text-sm font-medium text-gray-700 mb-1">Superficie (m²)</label>
            <input 
              v-model.number="modalCarrito.superficie" 
              @input="calcularCantidadPorSuperficie"
              type="number" 
              min="0" 
              step="0.01"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
              placeholder="Ingrese superficie en m²"
            >
            
            <div class="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
              <p class="text-sm text-gray-700">
                <span class="font-semibold">m² por caja:</span> {{ modalCarrito.articulo.mts2 }}
              </p>
              <p class="text-sm text-gray-700 mt-1">
                <span class="font-semibold">Cajas necesarias:</span> 
                <span class="text-blue-600 font-bold">{{ modalCarrito.cantidad }}</span>
              </p>
            </div>
          </div>

          <!-- Tipo A sin mts2 o tipo normal -->
          <div v-if="(modalCarrito.tipo === 'A' && modalCarrito.articulo?.mts2 <= 0) || (!modalCarrito.tipo || (modalCarrito.tipo !== 'C' && modalCarrito.tipo !== 'M' && modalCarrito.tipo !== 'A'))">
            <label class="block text-sm font-medium text-gray-700 mb-1">Cantidad</label>
            <input 
              v-model.number="modalCarrito.cantidad" 
              type="number" 
              min="1" 
              step="1"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
              placeholder="Ingrese cantidad"
            >
          </div>

          <!-- Subtotal -->
          <div class="p-3 bg-green-50 rounded-lg border border-green-200">
            <div class="flex justify-between items-center">
              <span class="text-sm font-medium text-gray-700">Subtotal:</span>
              <span class="text-xl font-bold text-green-600">${{ formatCurrency(modalCarrito.subtotal) }}</span>
            </div>
          </div>
        </div>

        <!-- Botones -->
        <div class="flex gap-3 mt-6">
          <button 
            @click="cerrarModalCarrito" 
            class="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition"
          >
            Cancelar
          </button>
          <button 
            @click="agregarAlCarrito" 
            :disabled="!modalCarrito.cantidad || modalCarrito.cantidad <= 0"
            class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            Agregar
          </button>
        </div>
      </div>
    </div>

    </main>
  </div>
</template>

<style scoped>
/* Altura fija para tarjetas */
.bg-white.rounded-lg.shadow {
  min-height: 420px;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.hover\\:scale-102:hover {
  transform: scale(1.02);
}

/* Animación suave para ofertas */
@keyframes gentle-pulse {
  0% { box-shadow: 0 0 0 0 rgba(34,197,94,0.12); }
  50% { box-shadow: 0 8px 20px -6px rgba(34,197,94,0.18); }
  100% { box-shadow: 0 0 0 0 rgba(34,197,94,0.12); }
}
.offer-animate {
  animation: gentle-pulse 3.5s ease-in-out infinite;
}
.offer-expiry {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 6px;
  background: rgba(34,197,94,0.08);
  animation: gentle-pulse 4s ease-in-out infinite;
}

/* Para truncar texto largo */
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Animaciones para toast */
.toast-enter-active, .toast-leave-active {
  transition: all 0.3s ease;
}
.toast-enter-from, .toast-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>