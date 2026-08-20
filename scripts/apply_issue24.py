from pathlib import Path

path = Path('frontend/src/views/ArticulosView.vue')
text = path.read_text(encoding='utf-8')

text = text.replace("import MobileOrderDrawer from '@/components/MobileOrderDrawer.vue';", "import MobileOrderDrawer from '@/components/MobileOrderDrawer.vue';\nimport QuickLoadPanel from '@/components/QuickLoadPanel.vue';", 1)

anchor = "const cartSidebarCollapsed = ref(localStorage.getItem('order_sidebar_collapsed') === '1')\n"
text = text.replace(anchor, anchor + "const showQuickLoad = ref(false)\n", 1)

old_button = '''<button type="button" class="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-gray-600 hover:bg-gray-100" @click="showNotification('Carga rápida se habilitará en la próxima etapa', 'info')">Carga rápida</button>'''
new_button = '''<button type="button" class="rounded-lg border border-gray-900 bg-gray-900 px-3 py-2 text-white hover:bg-black" @click="showQuickLoad = true">Carga rápida</button>'''
if old_button not in text:
    raise SystemExit('No se encontró botón placeholder de carga rápida')
text = text.replace(old_button, new_button, 1)

insert_marker = '''      <!-- Modal de filtros (móvil) -->'''
panel = '''      <QuickLoadPanel
        v-model:open="showQuickLoad"
        :modalidad="modalidad"
        :con-impuestos="conImpuestos"
        :condicion-pago="condicionPago"
        @added="showNotification($event, 'success')"
      />

'''
if insert_marker not in text:
    raise SystemExit('No se encontró punto de inserción del panel')
text = text.replace(insert_marker, panel + insert_marker, 1)

path.write_text(text, encoding='utf-8')
