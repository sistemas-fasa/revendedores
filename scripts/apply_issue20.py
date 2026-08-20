from pathlib import Path

path = Path('frontend/src/views/ArticulosView.vue')
text = path.read_text(encoding='utf-8')

# Menor separación vertical general.
text = text.replace('<div class="space-y-6">', '<div class="space-y-4">', 1)

# El PageHeader duplicaba título/buscador y empujaba el catálogo hacia abajo.
start = text.index('        <PageHeader')
end = text.index('        </PageHeader>', start) + len('        </PageHeader>')
text = text[:start] + text[end:]

# Reemplazar la cabecera alta de búsqueda por una barra compacta de contexto + filtros.
start = text.index('          <div class="mobile-search-head')
body = text.index('          <div class="mobile-search-body', start)
compact = '''          <div class="flex flex-col gap-3 border-b border-gray-200 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-5">
            <div>
              <p class="text-sm font-black text-gray-950">Armar pedido</p>
              <p class="text-xs font-medium text-gray-500">Buscá por clave, nombre o código y agregá productos sin salir del catálogo.</p>
            </div>
            <div class="flex flex-wrap gap-2 text-xs font-bold">
              <RouterLink to="/productos?oferta=1" class="rounded-lg border border-green-200 bg-green-50 px-3 py-2 text-green-800 hover:bg-green-100">Ofertas</RouterLink>
              <RouterLink to="/productos?discontinuados=1" class="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-amber-800 hover:bg-amber-100">Discontinuados</RouterLink>
              <button type="button" class="rounded-lg border border-gray-200 bg-white px-3 py-2 text-gray-700 hover:bg-gray-50" @click="clearSearch">Ver todos</button>
              <button type="button" class="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-gray-600 hover:bg-gray-100" @click="showNotification('Carga rápida se habilitará en la próxima etapa', 'info')">Carga rápida</button>
            </div>
          </div>
'''
text = text[:start] + compact + text[body:]

# Buscador más bajo y menos dominante.
text = text.replace('class="mobile-search-body px-4 py-4 sm:px-6"', 'class="mobile-search-body px-4 py-3 sm:px-5"', 1)
text = text.replace('class="h-16 w-full rounded-lg border-0 bg-transparent py-4 pl-16 pr-4 text-lg font-black text-gray-950 placeholder:text-gray-400 focus:outline-none sm:h-20 sm:px-5 sm:pl-20 sm:pr-28 sm:text-2xl"',
                    'class="h-12 w-full rounded-lg border-0 bg-transparent py-3 pl-14 pr-4 text-base font-bold text-gray-950 placeholder:text-gray-400 focus:outline-none sm:h-14 sm:pl-16 sm:pr-24 sm:text-lg"', 1)
text = text.replace('class="mobile-clear-button inline-flex h-12 w-full items-center justify-center rounded-lg border border-red-200 bg-white px-7 text-sm font-black text-red-700 shadow-sm hover:bg-red-50 sm:h-20 lg:w-auto"',
                    'class="mobile-clear-button inline-flex h-12 w-full items-center justify-center rounded-lg border border-gray-200 bg-white px-5 text-sm font-bold text-red-700 shadow-sm hover:bg-red-50 sm:h-14 lg:w-auto"', 1)
text = text.replace('class="flex h-9 w-9 items-center justify-center rounded-lg bg-red-600 text-white shadow-sm sm:h-10 sm:w-10"',
                    'class="flex h-8 w-8 items-center justify-center rounded-lg bg-red-600 text-white shadow-sm sm:h-9 sm:w-9"', 1)

# Condiciones comerciales: conservar controles, quitar encabezado redundante y compactar cajas.
text = text.replace('<div v-if="isDesktop" class="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">',
                    '<div v-if="isDesktop" class="rounded-lg border border-gray-200 bg-white p-3 shadow-sm">', 1)
cond_start = text.index('          <div class="mb-3 flex items-center justify-between gap-3">')
cond_grid = text.index('          <div class="grid grid-cols-1 gap-3 md:grid-cols-[minmax(280px,1.4fr)_minmax(220px,0.8fr)_minmax(260px,0.9fr)]">', cond_start)
text = text[:cond_start] + '''          <div class="mb-2 flex items-center justify-between gap-3">
            <p class="text-xs font-black uppercase tracking-wide text-gray-500">Condiciones comerciales</p>
            <p class="text-xs font-medium text-gray-400">Se guardan automáticamente</p>
          </div>
''' + text[cond_grid:]
text = text.replace('class="rounded-lg border border-gray-200 bg-gray-50 p-3"', 'class="rounded-lg border border-gray-200 bg-gray-50 p-2.5"', 3)
text = text.replace('class="mb-2 block text-xs font-bold uppercase text-gray-600"', 'class="mb-1 block text-[11px] font-bold uppercase text-gray-500"', 3)
text = text.replace('class="ui-field border-gray-300 px-3 py-3 text-sm font-semibold shadow-sm"', 'class="ui-field border-gray-300 px-3 py-2 text-sm font-semibold shadow-sm"', 1)

path.write_text(text, encoding='utf-8')

# Trigger intencional del workflow temporal.
