/**
 * app.js — Vue application bootstrap.
 *
 * This file runs LAST (after all views, components, and the router are loaded).
 * It:
 *   1. Configures Axios for same-origin API calls with JWT auth headers
 *   2. Sets up a global 401-interceptor (auto-logout on expired tokens)
 *   3. Creates the Vue app and registers global components
 *   4. Provides a this.$toast() helper available in any component
 *   5. Mounts the app on the #app element
 */

// ── Axios configuration ────────────────────────────────────────
// baseURL is empty because Flask serves both the frontend and the API
// from the same origin (http://127.0.0.1:5000). No CORS needed.
axios.defaults.baseURL = ''

// Request interceptor: attach the JWT token to every outgoing request.
// The token is stored in localStorage after a successful login.
axios.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Response interceptor: if ANY API call returns 401 (Unauthorized),
// the token has expired or is invalid — clear everything and redirect to login.
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401) {
      localStorage.clear()
      if (router.currentRoute.value.path !== '/login') router.push('/login')
    }
    return Promise.reject(error)
  }
)

// ── Create the Vue app ─────────────────────────────────────────
const app = Vue.createApp({})

// ── Global toast notification system ───────────────────────────
// Usage from any component:  this.$toast('Profile saved!', 'ok')
//                            this.$toast('Something went wrong', 'err')
// Toasts auto-dismiss after 3.2 seconds.
const toastState = Vue.reactive({ items: [] })
app.config.globalProperties.$toast = function (message, kind = '') {
  const id = Date.now() + Math.random()
  toastState.items.push({ id, message, kind })
  setTimeout(() => {
    const i = toastState.items.findIndex(t => t.id === id)
    if (i !== -1) toastState.items.splice(i, 1)
  }, 3200)
}

// Toast host component — renders the stack of active toasts in the bottom-right.
// Included once in index.html as <toast-host></toast-host>.
app.component('toast-host', {
  setup() { return { toastState } },
  template: `
    <div class="pp-toast-wrap">
      <div v-for="t in toastState.items" :key="t.id" class="pp-toast" :class="t.kind">
        <i class="bi" :class="t.kind === 'ok' ? 'bi-check-circle' : t.kind === 'err' ? 'bi-exclamation-circle' : 'bi-info-circle'"></i>
        <span>{{ t.message }}</span>
      </div>
    </div>`
})

// ── Register global components and mount ───────────────────────
app.component('app-shell', AppShell)  // sidebar+topbar layout (from components/AppShell.js)
app.use(router)                        // connect Vue Router (from router.js)
app.mount('#app')                      // mount on the <div id="app"> in index.html
