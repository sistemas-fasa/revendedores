// src/utils/toast.js

class Toast {
  constructor() {
    this.toasts = [];
    this.toastId = 0;
    this.container = null;
    this.init();
  }

  init() {
    // Crear contenedor si no existe
    this.container = document.getElementById('toast-container');
    if (!this.container) {
      this.container = document.createElement('div');
      this.container.id = 'toast-container';
      this.container.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        gap: 10px;
        max-width: 300px;
      `;
      document.body.appendChild(this.container);
    }
  }

    show(message, type = 'info', duration = 3000) {
    const id = this.toastId++;
    const toast = document.createElement('div');
    toast.id = `toast-${id}`;
    toast.style.cssText = this.getStyle(type);
    toast.innerHTML = `
        <div style="padding: 12px 16px; border-radius: 6px; background: inherit; color: white; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 3px 10px rgba(0,0,0,0.2);">
        <span>${message}</span>
        <button onclick="window.Toast.remove(${id})" style="background: none; border: none; color: white; font-size: 18px; cursor: pointer; opacity: 0.7;">×</button>
        </div>
    `;
    this.container.appendChild(toast);

    const timeout = duration ? setTimeout(() => this.remove(id), duration) : null;

    this.toasts.push({ id, element: toast, timeout });

    return id; // ✅ Devuelve el ID para poder cerrarlo después
    }

  remove(id) {
    const toastObj = this.toasts.find(t => t.id === id);
    if (!toastObj) return;

    const { element } = toastObj;
    const timeout = element.dataset.timeout;
    if (timeout) clearTimeout(timeout);

    element.style.opacity = '0';
    element.style.transition = 'opacity 0.3s ease';
    setTimeout(() => {
      if (element.parentNode) element.parentNode.removeChild(element);
    }, 300);

    this.toasts = this.toasts.filter(t => t.id !== id);
  }

  getStyle(type) {
    const colors = {
      success: '#16a34a',
      error: '#b91c1c',
      warning: '#d97706',
      info: '#0284c7',
    };
    return `background-color: ${colors[type] || colors.info}; margin-bottom: 10px;`;
  }
}

// Hacerlo global para usarlo fácilmente
window.Toast = new Toast();

// Exportar por si se usa en módulos
export default window.Toast;