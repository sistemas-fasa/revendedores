<template>
  <div class="chart-card">
    <div class="chart-title">{{ title }}</div>

    <div v-if="!hasData" class="empty-state">Sin datos para mostrar</div>

    <div v-else class="chart-area">
      <div class="bars">
        <div v-for="(value, idx) in values" :key="idx" class="bar-item">
          <div class="bar-value">{{ value }}</div>
          <div class="bar" :style="barStyle(value)"></div>
          <div class="bar-label" :title="labels[idx]">{{ shortLabel(labels[idx]) }}</div>
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
    maxValue() {
      return Math.max(1, ...this.values)
    },
    hasData() {
      return this.values.some(v => v > 0)
    },
  },
  methods: {
    barStyle(value) {
      const height = (value / this.maxValue) * 100
      return {
        height: `${Math.max(4, height)}%`,
      }
    },
    shortLabel(label) {
      if (!label) return ''
      return String(label).slice(5)
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

.chart-area {
  height: 320px;
  padding: 8px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
}

.bars {
  height: 100%;
  display: grid;
  grid-template-columns: repeat(14, minmax(0, 1fr));
  gap: 6px;
  align-items: end;
}

.bar-item {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: center;
}

.bar {
  width: 100%;
  max-width: 20px;
  background: #ef4444;
  border-radius: 4px 4px 0 0;
}

.bar-value {
  font-size: 0.75rem;
  color: #111827;
  margin-bottom: 4px;
}

.bar-label {
  margin-top: 6px;
  font-size: 0.65rem;
  color: #4b5563;
  writing-mode: vertical-rl;
  transform: rotate(180deg);
  max-height: 74px;
  overflow: hidden;
}

.empty-state {
  color: #6b7280;
  font-size: 0.95rem;
  padding: 28px 0;
  text-align: center;
}
</style>