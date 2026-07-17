/**
 * Register.js — Account creation page (student or company).
 *
 * Features a role-switch toggle between Student and Company forms.
 * Validates all fields client-side before posting to
 * /api/auth/register/student or /api/auth/register/company.
 * On success, redirects to the login page after a short delay.
 */
const RegisterView = {
  template: `
  <div class="auth-wrap">
    <section class="auth-brand">
      <div class="brand-mark">
        <span class="glyph"><i class="bi bi-mortarboard-fill"></i></span>
        Placement Portal
      </div>
      <div>
        <h1>Join the<br/>placement season.</h1>
        <p class="lede">Students discover eligible drives and track every application. Companies post roles and manage candidates end to end.</p>
        <div class="facts">
          <div><div class="k">Students</div><div class="l">Apply &amp; track</div></div>
          <div><div class="k">Companies</div><div class="l">Hire on campus</div></div>
        </div>
      </div>
      <div class="small" style="color:#8ea3c8;">Institute Placement Cell</div>
    </section>

    <section class="auth-panel">
      <div class="auth-card">
        <h4 class="mb-1">Create your account</h4>
        <p class="text-muted mb-3">Choose the account type that fits you.</p>

        <div class="role-switch mb-4">
          <button :class="{ active: role === 'student' }" @click="role = 'student'">
            <i class="bi bi-person-fill me-1"></i>Student
          </button>
          <button :class="{ active: role === 'company' }" @click="role = 'company'">
            <i class="bi bi-building me-1"></i>Company
          </button>
        </div>

        <div v-if="error" class="alert alert-danger py-2">{{ error }}</div>
        <div v-if="success" class="alert alert-success py-2">{{ success }}</div>

        <div class="mb-3">
          <label class="form-label">Email</label>
          <input v-model="form.email" type="email" class="form-control" placeholder="you@example.com" />
        </div>
        <div class="mb-3">
          <label class="form-label">Password</label>
          <input v-model="form.password" type="password" class="form-control" placeholder="At least 6 characters" />
        </div>

        <template v-if="role === 'student'">
          <div class="row g-2">
            <div class="col-12 mb-2">
              <label class="form-label">Full name</label>
              <input v-model="form.full_name" type="text" class="form-control" />
            </div>
            <div class="col-6 mb-2">
              <label class="form-label">Roll number</label>
              <input v-model="form.roll_number" type="text" class="form-control" />
            </div>
            <div class="col-6 mb-2">
              <label class="form-label">Branch</label>
              <select v-model="form.branch" class="form-select">
                <option value="">Select</option>
                <option>CS</option><option>IT</option><option>ECE</option>
                <option>EEE</option><option>ME</option><option>CE</option>
              </select>
            </div>
            <div class="col-6 mb-2">
              <label class="form-label">CGPA</label>
              <input v-model="form.cgpa" type="number" step="0.1" min="0" max="10" class="form-control" />
            </div>
            <div class="col-6 mb-2">
              <label class="form-label">Year of study</label>
              <select v-model="form.year_of_study" class="form-select">
                <option value="">Select</option>
                <option>1</option><option>2</option><option>3</option><option>4</option>
              </select>
            </div>
            <div class="col-12 mb-2">
              <label class="form-label">Phone</label>
              <input v-model="form.phone" type="text" class="form-control" />
            </div>
          </div>
        </template>

        <template v-if="role === 'company'">
          <div class="mb-2">
            <label class="form-label">Company name</label>
            <input v-model="form.company_name" type="text" class="form-control" />
          </div>
          <div class="mb-2">
            <label class="form-label">HR name</label>
            <input v-model="form.hr_name" type="text" class="form-control" />
          </div>
          <div class="mb-2">
            <label class="form-label">HR email</label>
            <input v-model="form.hr_email" type="email" class="form-control" />
          </div>
          <div class="mb-2">
            <label class="form-label">Website</label>
            <input v-model="form.website" type="text" class="form-control" />
          </div>
          <div class="mb-2">
            <label class="form-label">Industry</label>
            <input v-model="form.industry" type="text" class="form-control" />
          </div>
        </template>

        <button class="btn btn-primary w-100 mt-3" @click="register" :disabled="loading">
          <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
          {{ loading ? 'Creating account…' : 'Create account' }}
        </button>
        <div class="text-center mt-3 small text-muted">
          Already have an account? <a href="#/login">Sign in</a>
        </div>
      </div>
    </section>
  </div>
  `,
  data() {
    return { role: 'student', form: {}, error: '', success: '', loading: false }
  },
  methods: {
    async register() {
      this.error = ''

      if (!this.form.email || !this.form.password) {
        this.error = 'Email and password are required.'
        return
      }
      if (!this.form.email.includes('@')) {
        this.error = 'Enter a valid email address.'
        return
      }
      if (this.form.password.length < 6) {
        this.error = 'Password must be at least 6 characters.'
        return
      }

      if (this.role === 'student') {
        if (!this.form.full_name?.trim()) { this.error = 'Full name is required.'; return }
        if (!this.form.roll_number?.trim()) { this.error = 'Roll number is required.'; return }
        if (!this.form.branch) { this.error = 'Select your branch.'; return }
        if (!this.form.cgpa || this.form.cgpa < 0 || this.form.cgpa > 10) { this.error = 'CGPA must be between 0 and 10.'; return }
        if (!this.form.year_of_study) { this.error = 'Select your year of study.'; return }
      }

      if (this.role === 'company') {
        if (!this.form.company_name?.trim()) { this.error = 'Company name is required.'; return }
        if (!this.form.hr_name?.trim()) { this.error = 'HR name is required.'; return }
        if (!this.form.hr_email?.includes('@')) { this.error = 'Enter a valid HR email.'; return }
      }

      this.loading = true
      try {
        const endpoint = this.role === 'student'
          ? '/api/auth/register/student'
          : '/api/auth/register/company'
        await axios.post(endpoint, { ...this.form })
        this.success = 'Account created. Taking you to sign-in…'
        this.form = {}
        setTimeout(() => this.$router.push('/login'), 1600)
      } catch (err) {
        this.error = err.response?.data?.error || 'Registration failed. Please try again.'
      } finally {
        this.loading = false
      }
    },
  },
}
