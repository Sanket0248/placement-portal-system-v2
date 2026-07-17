/**
 * AppShell.js — Reusable sidebar + topbar dashboard layout.
 *
 * This component provides the common "chrome" for all three dashboards
 * (admin, company, student). It renders:
 *   - A dark sidebar with the portal logo, nav items, and logout button
 *   - A topbar showing the active section name and role badge
 *   - A content area (<slot>) where each dashboard injects its tab content
 *
 * Props:
 *   role       — 'admin' | 'company' | 'student' (sets the accent color via CSS)
 *   title      — display name (not currently shown, but available)
 *   navItems   — array of { key, label, icon } for sidebar buttons
 *   modelValue — the currently active tab key (v-model binding)
 *
 * The [data-role] attribute on the root element activates CSS custom
 * properties that tint the accent color per role (cobalt / emerald / violet).
 *
 * Mobile: the sidebar collapses off-screen and is toggled via a hamburger
 * button in the topbar. A backdrop overlay closes it on tap.
 */

const AppShell = {
  props: {
    role: { type: String, required: true },
    title: { type: String, default: '' },
    navItems: { type: Array, required: true },
    modelValue: { type: String, required: true },  // active tab key
  },
  emits: ['update:modelValue'],
  data() {
    return {
      navOpen: false,  // mobile sidebar toggle
      email: localStorage.getItem('email') || '',
    }
  },
  computed: {
    // Show the label of the currently active tab in the topbar.
    activeLabel() {
      const item = this.navItems.find(t => t.key === this.modelValue)
      return item ? item.label : this.title
    },
  },
  methods: {
    // When a sidebar nav item is clicked, emit the new tab key to the parent
    // (which uses v-model to sync) and close the mobile nav.
    select(key) { this.$emit('update:modelValue', key); this.navOpen = false },
    // Clear all auth data and go back to login.
    logout() { localStorage.clear(); window.location.href = '/' },
  },
  template: `
  <div class="app-shell" :class="{ 'nav-open': navOpen }" :data-role="role">

    <!-- ── Sidebar (fixed on desktop, slide-in on mobile) ── -->
    <aside class="app-sidebar">
      <div class="brand">
        <span class="glyph"><i class="bi bi-mortarboard-fill"></i></span>
        Placement Portal
      </div>
      <div class="role-tag">{{ role }} workspace</div>

      <!-- Navigation buttons — one per tab -->
      <nav class="side-nav">
        <button v-for="item in navItems" :key="item.key"
          :class="{ active: modelValue === item.key }" @click="select(item.key)">
          <i :class="item.icon"></i><span>{{ item.label }}</span>
        </button>
      </nav>

      <!-- Bottom section: user email + logout -->
      <div class="side-foot">
        <div class="who"><i class="bi bi-person-circle me-1"></i>{{ email }}</div>
        <button class="btn btn-outline-light btn-sm w-100" @click="logout">
          <i class="bi bi-box-arrow-right me-1"></i>Log out
        </button>
      </div>
    </aside>

    <!-- Mobile overlay backdrop (closes sidebar on tap) -->
    <div v-if="navOpen" class="app-backdrop" @click="navOpen = false"></div>

    <!-- ── Main content area ── -->
    <div class="app-main">
      <!-- Topbar with hamburger toggle (mobile only) and section title -->
      <header class="app-topbar">
        <div class="d-flex align-items-center gap-2">
          <button class="btn btn-sm btn-outline-secondary sidebar-toggle" @click="navOpen = !navOpen">
            <i class="bi bi-list"></i>
          </button>
          <span class="title">{{ activeLabel }}</span>
        </div>
        <span class="role-chip">{{ role }}</span>
      </header>

      <!-- Page content — each dashboard view fills this slot -->
      <main class="app-content">
        <slot></slot>
      </main>
    </div>
  </div>`,
}
