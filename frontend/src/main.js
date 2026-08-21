// src/main.js
import { createApp } from 'vue';
import App from './App.vue';
import { createPinia } from 'pinia';
import router from './router';
import './assets/index.css';
import './registerServiceWorker' // Importa el registro del service worker

// 🔥 Importa tu toast personalizado
import './utils/toast'; // ← esto crea window.Toast
import './utils/compactCommercialConditions';

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);

// Inicializar auth store después de que pinia esté disponible
import { useAuthStore } from './stores/auth';
const authStore = useAuthStore();
// El store ya se inicializa automáticamente al crearse

app.use(router);
app.mount('#app');
