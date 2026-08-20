from pathlib import Path

path = Path('frontend/src/views/ArticulosView.vue')
text = path.read_text(encoding='utf-8')

text = text.replace("import FloatingCartButton from '@/components/FloatingCartButton.vue';", "import MobileOrderDrawer from '@/components/MobileOrderDrawer.vue';", 1)
text = text.replace('<FloatingCartButton class="xl:hidden" />', '<MobileOrderDrawer />', 1)
text = text.replace('<div class="ui-page">', '<div class="ui-page pb-20 xl:pb-0">', 1)

path.write_text(text, encoding='utf-8')

# Trigger intencional.
