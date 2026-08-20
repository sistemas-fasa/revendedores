from pathlib import Path

path = Path('frontend/src/views/ArticulosView.vue')
text = path.read_text(encoding='utf-8')
old = '''          </div>
        </div>

        <OrderSidebar v-model:collapsed="cartSidebarCollapsed" />'''
new = '''          </div>
        </div>
        </div>

        <OrderSidebar v-model:collapsed="cartSidebarCollapsed" />'''
if old not in text:
    raise SystemExit('No se encontró cierre de layout a corregir')
path.write_text(text.replace(old, new, 1), encoding='utf-8')

# Trigger intencional.
