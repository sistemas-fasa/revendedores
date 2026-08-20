from pathlib import Path

path = Path('frontend/src/views/ArticulosView.vue')
text = path.read_text(encoding='utf-8')

text = text.replace("import FloatingCartButton from '@/components/FloatingCartButton.vue';", "import FloatingCartButton from '@/components/FloatingCartButton.vue';\nimport OrderSidebar from '@/components/OrderSidebar.vue';", 1)

state_anchor = "const searchInputRef = ref(null)\n"
state = "const searchInputRef = ref(null)\nconst cartSidebarCollapsed = ref(localStorage.getItem('order_sidebar_collapsed') === '1')\n"
text = text.replace(state_anchor, state, 1)

open_marker = '''    <main class="main-content">
      <div class="space-y-4">'''
open_replacement = '''    <main class="main-content">
      <div
        class="grid items-start gap-4 transition-[grid-template-columns] duration-200"
        :class="cartSidebarCollapsed
          ? 'xl:grid-cols-[minmax(0,1fr)_68px]'
          : 'xl:grid-cols-[minmax(0,1fr)_380px]'"
      >
        <div class="min-w-0 space-y-4">'''
if open_marker not in text:
    raise SystemExit('No se encontró apertura del contenido')
text = text.replace(open_marker, open_replacement, 1)

close_marker = '''        </div>
      </div>

      <!-- Modal de filtros (móvil) -->'''
close_replacement = '''        </div>

        <OrderSidebar v-model:collapsed="cartSidebarCollapsed" />
      </div>

      <!-- Modal de filtros (móvil) -->'''
if close_marker not in text:
    raise SystemExit('No se encontró cierre del contenido principal')
text = text.replace(close_marker, close_replacement, 1)

text = text.replace('<FloatingCartButton />', '<FloatingCartButton class="xl:hidden" />', 1)

path.write_text(text, encoding='utf-8')

# Trigger intencional.
