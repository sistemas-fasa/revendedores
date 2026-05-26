<script setup>
import { nextTick, ref } from 'vue'
import api from '@/services/api'

const message = ref('')
const loading = ref(false)
const error = ref('')
const conversationContext = ref({})
const messages = ref([
  {
    role: 'bot',
    text: 'Chat local de prueba listo. Escribi una consulta como "precio cemento" o "precio .03.011".'
  }
])
const threadRef = ref(null)

const scrollToBottom = async () => {
  await nextTick()
  if (threadRef.value) {
    threadRef.value.scrollTop = threadRef.value.scrollHeight
  }
}

const sendMessage = async () => {
  const text = message.value.trim()
  if (!text || loading.value) return

  error.value = ''
  message.value = ''
  messages.value.push({ role: 'user', text })
  loading.value = true
  await scrollToBottom()

  try {
    const response = await api.post('/api/bot/test-chat/', {
      message: text,
      context: conversationContext.value
    })
    conversationContext.value = response.data.context || {}
    messages.value.push({
      role: 'bot',
      text: response.data.reply,
      debug: response.data.debug
    })
  } catch (err) {
    const serverMessage = err.response?.data?.error || 'No se pudo consultar el bot local.'
    error.value = serverMessage
    messages.value.push({ role: 'bot', text: serverMessage, error: true })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

const useExample = (text) => {
  message.value = text
}
</script>

<template>
  <section class="mx-auto flex h-[calc(100vh-8rem)] max-w-5xl flex-col overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
    <header class="border-b border-gray-200 px-5 py-4">
      <p class="text-xs font-semibold uppercase tracking-wide text-red-600">Prueba local</p>
      <h1 class="text-xl font-semibold text-gray-900">Bot WhatsApp</h1>
      <p class="mt-1 text-sm text-gray-500">
        Simula el mismo flujo de respuesta del bot sin enviar mensajes por Meta.
      </p>
    </header>

    <div ref="threadRef" class="flex-1 space-y-3 overflow-y-auto bg-gray-50 px-5 py-4">
      <div
        v-for="(item, index) in messages"
        :key="index"
        class="flex"
        :class="item.role === 'user' ? 'justify-end' : 'justify-start'"
      >
        <div
          class="max-w-[80%] whitespace-pre-line rounded-lg px-4 py-3 text-sm leading-relaxed shadow-sm"
          :class="[
            item.role === 'user'
              ? 'bg-red-600 text-white'
              : item.error
                ? 'border border-red-200 bg-red-50 text-red-800'
                : 'border border-gray-200 bg-white text-gray-800'
          ]"
        >
          {{ item.text }}
          <p v-if="item.debug" class="mt-2 border-t border-gray-100 pt-2 text-xs text-gray-400">
            usuario: {{ item.debug.username }}
          </p>
        </div>
      </div>
      <div v-if="loading" class="text-sm text-gray-500">Consultando...</div>
    </div>

    <div class="border-t border-gray-200 bg-white px-5 py-4">
      <div class="mb-3 flex flex-wrap gap-2">
        <button
          type="button"
          class="rounded border border-gray-300 px-3 py-1.5 text-xs text-gray-700 hover:bg-gray-50"
          @click="useExample('precio cemento')"
        >
          precio cemento
        </button>
        <button
          type="button"
          class="rounded border border-gray-300 px-3 py-1.5 text-xs text-gray-700 hover:bg-gray-50"
          @click="useExample('precio .03.011')"
        >
          precio .03.011
        </button>
        <button
          type="button"
          class="rounded border border-gray-300 px-3 py-1.5 text-xs text-gray-700 hover:bg-gray-50"
          @click="useExample('hola')"
        >
          hola
        </button>
      </div>

      <form class="flex gap-3" @submit.prevent="sendMessage">
        <input
          v-model="message"
          class="min-w-0 flex-1 rounded-md border border-gray-300 px-4 py-3 text-sm outline-none focus:border-red-500 focus:ring-2 focus:ring-red-100"
          placeholder="Escribi una consulta para el bot..."
          :disabled="loading"
        />
        <button
          type="submit"
          class="rounded-md bg-red-600 px-5 py-3 text-sm font-semibold text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:bg-gray-300"
          :disabled="loading || !message.trim()"
        >
          Enviar
        </button>
      </form>
      <p v-if="error" class="mt-2 text-sm text-red-600">{{ error }}</p>
    </div>
  </section>
</template>
