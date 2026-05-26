<template>
  <div class="chart-card">
    <div class="chart-title">{{ title }}</div>

    <div v-if="!hasData" class="empty-state">Sin datos para mostrar</div>

    <div v-else class="pie-wrapper">
      <div class="pie" :style="pieStyle"></div>

      <div class="legend">
        <div v-for="(item, idx) in legendItems" :key="idx" class="legend-item">
          <span class="dot" :style="{ backgroundColor: item.color }"></span>
          <span class="name">{{ item.label }}</span>
          <span class="value">{{ item.value }}</span>
          <span class="pct">({{ item.percent }}%)</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    data: {
      type: Object,
      required: true,
    },
    title: {
      type: String,
      default: '',
    },
  },
  computed: {
    labels() {
      return Array.isArray(this.data?.labels) ? this.data.labels : []
    },
    values() {
      const raw = this.data?.datasets?.[0]?.data
      return Array.isArray(raw) ? raw.map(v => Number(v) || 0) : []
    },
    colors() {
      const fromData = this.data?.datasets?.[0]?.backgroundColor
      if (Array.isArray(fromData) && fromData.length >= this.values.length) {
        return fromData
      }
      return ['#ef4444', '#3b82f6', '#6b7280', '#10b981', '#f59e0b']
    },
    total() {
      return this.values.reduce((acc, n) => acc + n, 0)
    },
    hasData() {
      return this.total > 0
    },
    legendItems() {
      return this.values.map((value, idx) => {
        const percent = this.total > 0 ? ((value / this.total) * 100).toFixed(1) : '0.0'
        return {
          label: this.labels[idx] || `Item ${idx + 1}`,
          value,
          percent,
          color: this.colors[idx % this.colors.length],
        }
      })
    },
    pieStyle() {
      const stops = []
      let acc = 0
      this.values.forEach((value, idx) => {
        const angle = this.total > 0 ? (value / this.total) * 360 : 0
        const start = acc
        const end = acc + angle
        const color = this.colors[idx % this.colors.length]
        stops.push(`${color} ${start}deg ${end}deg`)
        acc = end
      })

      return {
        background: `conic-gradient(${stops.join(', ')})`,
      }
    },
  },
}
</script>

<style scoped>
.chart-card {
  width: 100%;
}

.chart-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 12px;
  text-align: center;
}

.pie-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  min-height: 320px;
}

.pie {
  width: 220px;
  height: 220px;
  border-radius: 50%;
  box-shadow: inset 0 0 0 1px #e5e7eb;
}

.legend {
  min-width: 200px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.legend-item {
  display: grid;
  grid-template-columns: auto 1fr auto auto;
  gap: 8px;
  align-items: center;
  font-size: 0.92rem;
  color: #111827;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.name {
  color: #374151;
}

.value {
  font-weight: 700;
}

.pct {
  color: #6b7280;
}

.empty-state {
  color: #6b7280;
  font-size: 0.95rem;
  padding: 28px 0;
  text-align: center;
}

@media (max-width: 900px) {
  .pie-wrapper {
    flex-direction: column;
  }
}
</style>
