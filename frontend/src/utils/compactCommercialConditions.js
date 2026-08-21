const SUMMARY_ID = 'commercial-conditions-summary'

const findConditionsPanel = () => {
  const candidates = Array.from(document.querySelectorAll('div'))
  return candidates.find((node) => {
    if (node.id === SUMMARY_ID) return false
    const title = Array.from(node.querySelectorAll('p')).find(
      (p) => p.textContent?.trim() === 'Condiciones comerciales'
    )
    return Boolean(title && node.querySelector('select'))
  }) || null
}

const getConditionLabel = (panel) => {
  const select = panel.querySelector('select')
  const selected = select?.options?.[select.selectedIndex]
  return selected?.textContent?.replace(/\s+/g, ' ')?.trim() || 'Condición de pago'
}

const getActiveButtonLabel = (panel, heading) => {
  const labels = Array.from(panel.querySelectorAll('label'))
  const label = labels.find((item) => item.textContent?.trim().toUpperCase() === heading)
  const section = label?.parentElement
  const active = section?.querySelector('button.bg-red-600')
  return active?.textContent?.replace(/\s+/g, ' ')?.trim() || ''
}

const buildSummary = (panel) => {
  let summary = document.getElementById(SUMMARY_ID)
  if (summary) return summary

  summary = document.createElement('div')
  summary.id = SUMMARY_ID
  summary.className = 'rounded-lg border border-gray-200 bg-white px-3 py-2 shadow-sm'
  summary.innerHTML = `
    <div class="flex flex-wrap items-center gap-2">
      <span class="text-[11px] font-black uppercase tracking-wide text-gray-500">Condiciones</span>
      <span data-commercial-condition class="max-w-[460px] truncate rounded-full bg-gray-100 px-3 py-1 text-xs font-bold text-gray-800"></span>
      <span data-commercial-modality class="rounded-full bg-red-50 px-3 py-1 text-xs font-bold text-red-800"></span>
      <span data-commercial-tax class="rounded-full bg-red-50 px-3 py-1 text-xs font-bold text-red-800"></span>
      <button type="button" data-commercial-toggle class="ml-auto rounded-lg border border-gray-300 bg-white px-3 py-1.5 text-xs font-black text-gray-800 transition hover:border-red-300 hover:bg-red-50 hover:text-red-700" aria-expanded="false">
        Cambiar
      </button>
    </div>
  `

  panel.parentElement?.insertBefore(summary, panel)
  return summary
}

const install = () => {
  const panel = findConditionsPanel()
  if (!panel || panel.dataset.compactCommercialInstalled === '1') return

  panel.dataset.compactCommercialInstalled = '1'
  const summary = buildSummary(panel)
  let expanded = false

  const conditionEl = summary.querySelector('[data-commercial-condition]')
  const modalityEl = summary.querySelector('[data-commercial-modality]')
  const taxEl = summary.querySelector('[data-commercial-tax]')
  const toggle = summary.querySelector('[data-commercial-toggle]')

  const refresh = () => {
    conditionEl.textContent = getConditionLabel(panel)
    modalityEl.textContent = getActiveButtonLabel(panel, 'MODALIDAD') || 'Modalidad'
    taxEl.textContent = getActiveButtonLabel(panel, 'PRECIO') || 'Precio'
  }

  const setExpanded = (value) => {
    expanded = Boolean(value)
    panel.style.display = expanded ? '' : 'none'
    toggle.textContent = expanded ? 'Listo' : 'Cambiar'
    toggle.setAttribute('aria-expanded', String(expanded))
  }

  toggle.addEventListener('click', (event) => {
    event.stopPropagation()
    setExpanded(!expanded)
  })

  panel.addEventListener('change', () => window.setTimeout(refresh, 0))
  panel.addEventListener('click', () => window.setTimeout(refresh, 0))

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && expanded) setExpanded(false)
  })

  document.addEventListener('click', (event) => {
    if (!expanded) return
    if (panel.contains(event.target) || summary.contains(event.target)) return
    setExpanded(false)
  })

  refresh()
  setExpanded(false)
}

const observer = new MutationObserver(() => install())

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    install()
    observer.observe(document.body, { childList: true, subtree: true })
  }, { once: true })
} else {
  install()
  observer.observe(document.body, { childList: true, subtree: true })
}
