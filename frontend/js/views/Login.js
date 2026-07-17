/**
 * Login.js — Sign-in page with split brand panel.
 *
 * Left panel: branding + tagline. Right panel: email/password form.
 * On successful login, stores JWT token + role + email in localStorage
 * and redirects to the role-appropriate dashboard via Vue Router.
 * Calls POST /api/auth/login.
 */
const LoginView = {
  template: `
  <div class="auth-wrap">
    <section class="auth-brand">
      <div class="brand-mark">
        <span class="glyph"><i class="bi bi-mortarboard-fill"></i></span>
        Placement Portal
      </div>
      <div>
        <h1>Where campus talent<br/>meets opportunity.</h1>
        <p class="lede">One place for students, recruiters, and the placement cell to run the entire hiring season.</p>
        <div class="facts">
          <div><div class="k">3</div><div class="l">Roles</div></div>
          <div><div class="k">Live</div><div class="l">Drive tracking</div></div>
          <div><div class="k">Auto</div><div class="l">Reminders</div></div>
        </div>
      </div>
      <div class="small" style="color:#8ea3c8;">Institute Placement Cell · secure sign-in</div>
    </section>

    <section class="auth-panel">
      <div class="auth-card">
        <h4 class="mb-1">Welcome back</h4>
        <p class="text-muted mb-4">Sign in to continue to your dashboard.</p>

        <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>

        <div class="mb-3">
          <label class="form-label">Email</label>
          <input v-model="email" type="email" class="form-control" placeholder="you@example.com"
            @keyup.enter="login" />
        </div>
        <div class="mb-4">
          <label class="form-label">Password</label>
          <input v-model="password" type="password" class="form-control" placeholder="Your password"
            @keyup.enter="login" />
        </div>

        <button class="btn btn-primary w-100 mb-3" @click="login" :disabled="loading">
          <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
          {{ loading ? 'Signing in…' : 'Sign in' }}
        </button>

        <div class="text-center text-muted small">
          New here? <a href="#/register">Create an account</a>
        </div>
      </div>
    </section>
  </div>
  `,
  data() {
    return { email: '', password: '', error: '', loading: false }
  },
  methods: {
    async login() {
      if (!this.email || !this.password) {
        this.error = 'Enter your email and password to continue.'
        return
      }
      this.loading = true
      this.error = ''
      try {
        const res = await axios.post('/api/auth/login', { email: this.email, password: this.password })
        localStorage.setItem('token', res.data.token)
        localStorage.setItem('role', res.data.user.role)
        localStorage.setItem('email', res.data.user.email)
        localStorage.setItem('user_id', res.data.user.id)
        this.$router.push(`/${res.data.user.role}/dashboard`)
      } catch (err) {
        this.error = err.response?.data?.error || 'Sign-in failed. Please try again.'
      } finally {
        this.loading = false
      }
    },
  },
}
