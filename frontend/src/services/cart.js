import { reactive, computed, watch } from 'vue';
import api from './api';

// Función para cargar el carrito desde localStorage
const loadCartFromStorage = () => {
    try {
        const stored = localStorage.getItem('shopping_cart');
        if (stored) {
            const parsed = JSON.parse(stored);
            console.log('📦 Carrito cargado desde localStorage:', parsed);
            return parsed.items || [];
        }
    } catch (error) {
        console.error('❌ Error al cargar carrito desde localStorage:', error);
    }
    return [];
};

// Función para guardar el carrito en localStorage
const saveCartToStorage = (items) => {
    try {
        localStorage.setItem('shopping_cart', JSON.stringify({ items }));
        console.log('💾 Carrito guardado en localStorage:', items.length, 'items');
        
        // Sincronizar con el backend
        sincronizarConBackend(items);
    } catch (error) {
        console.error('❌ Error al guardar carrito en localStorage:', error);
    }
};

// Función para sincronizar el carrito con el backend
const sincronizarConBackend = async (items) => {
    try {
        // Sincronizar siempre, incluso si el carrito está vacío
        // (para limpiar el carrito en el backend cuando se eliminen todos los items)
        const response = await api.post('/api/sincronizar-carrito/', { items });
        console.log('✅ Carrito sincronizado con backend:', response.data);
    } catch (error) {
        // No mostrar error al usuario, solo logear
        console.warn('⚠️ No se pudo sincronizar carrito con backend:', error.message);
    }
};

export const cart = reactive({
    items: loadCartFromStorage(), // Cargar items al iniciar
    
    get totalItems() {
        // Retorna la cantidad de items diferentes (no la suma de cantidades)
        return this.items.length;
    },

    get totalPrice() {
        return this.items.reduce((total, item) => total + item.subtotal, 0);
    },

    add(articulo, cantidad = 1) {
        const existingItem = this.items.find(item => item.articulo.clave === articulo.clave);
        if (existingItem) {
            existingItem.cantidad += cantidad;
            existingItem.subtotal = existingItem.cantidad * existingItem.precio_unitario;
        } else {
            const precio_unitario = articulo.precio_lista;
            this.items.push({
                articulo: articulo,
                cantidad: cantidad,
                precio_unitario: precio_unitario,
                subtotal: cantidad * precio_unitario,
            });
        }
        saveCartToStorage(this.items); // Guardar después de agregar
    },

    remove(articulo_clave) {
        this.items = this.items.filter(item => item.articulo.clave !== articulo_clave);
        saveCartToStorage(this.items); // Guardar después de eliminar
    },

    updateQuantity(articulo_clave, cantidad) {
        const item = this.items.find(item => item.articulo.clave === articulo_clave);
        if (item) {
            item.cantidad = cantidad;
            item.subtotal = item.cantidad * item.precio_unitario;
            saveCartToStorage(this.items); // Guardar después de actualizar
        }
    },

    clear() {
        this.items = [];
        saveCartToStorage(this.items); // Guardar después de limpiar
    },

    async checkout(onProgress = null) {
        if (this.items.length === 0) {
            throw new Error('El carrito está vacío');
        }

        let pedido = null;

        try {
            console.log('🛒 Iniciando checkout...', { itemCount: this.items.length });
            
            // Paso 1: Crear el pedido (esto ya guarda en backend)
            if (onProgress) onProgress('Creando pedido...');
            const modalidad = localStorage.getItem('articulos_modalidad') || 'retira';
            const savedImpuestos = localStorage.getItem('articulos_con_impuestos');
            const con_impuestos = savedImpuestos === null ? true : savedImpuestos === 'true';

            const pedidoData = {
                modalidad,
                con_impuestos,
                items: this.items.map(item => ({
                    articulo: item.articulo.clave,
                    cantidad: item.cantidad,
                    precio_unitario: parseFloat(item.precio_unitario.toFixed(2)), // ✅ Redondeo
                })),
            };

            console.log('📦 Creando pedido...', pedidoData);
            const response = await api.post('/api/pedidos/', pedidoData);
            pedido = response.data;
            console.log('✅ Pedido creado:', pedido);

            // Paso 2: Confirmar el pedido
            if (onProgress) onProgress('Enviando confirmación...');
            console.log('📧 Confirmando pedido...', pedido.id);
            console.time('⏱️ Tiempo de confirmación');
            
            try {
                const confirmResponse = await api.post(`/api/pedidos/${pedido.id}/confirmar_pedido/`);
                console.timeEnd('⏱️ Tiempo de confirmación');
                console.log('✅ Pedido confirmado:', confirmResponse.data);
                console.log('📊 Status de confirmación:', confirmResponse.status);
                console.log('📝 Headers de respuesta:', confirmResponse.headers);

                // Limpiar carrito SOLO si todo fue bien
                this.clear();
                console.log('🧹 Carrito limpiado');

                return {
                    success: true,
                    message: confirmResponse.data.status || 'Pedido realizado con éxito.',
                    pedido,
                };
            } catch (confirmError) {
                console.timeEnd('⏱️ Tiempo de confirmación');
                console.error('❌ Error en confirmación:', confirmError);
                console.log('📋 Response data:', confirmError.response?.data);
                console.log('📊 Response status:', confirmError.response?.status);
                
                // Si el pedido se creó pero falló la confirmación, devolver info útil
                const confirmErrorMessage = confirmError.response?.data?.error || 
                                           confirmError.response?.data?.detail ||
                                           'Error al confirmar el pedido, pero el pedido fue creado';
                
                return {
                    success: false,
                    message: `Pedido #${pedido.id} creado pero ${confirmErrorMessage}`,
                    pedido,
                    error: confirmError
                };
            }

        } catch (error) {
            console.error('❌ Error en el proceso de checkout:', error);

            // Si el pedido se creó pero falló confirmación/correo, podrías querer notificarlo
            const errorMessage = error.response?.data?.error || 
                                error.response?.data?.detail ||
                                error.message ||
                                'No se pudo procesar tu pedido. Intenta de nuevo.';

            console.error('💥 Mensaje de error:', errorMessage);

            // En lugar de lanzar excepción, devolver objeto con success: false
            return {
                success: false,
                message: errorMessage,
                pedido, // podrías querer mostrar el ID del pedido aunque falle correo
                error: error
            };
        }
    },
});