/**
 * router.js — Vue Router configuration.
 *
 * Uses hash-mode routing (URLs look like /#/login, /#/admin/dashboard).
 * Hash mode doesn't need any server-side route handling — Flask just
 * serves index.html and Vue Router reads the hash fragment.
 *
 * The beforeEach navigation guard enforces role-based access:
 *   - Unauthenticated users can only access /login and /register
 *   - Authenticated users are redirected away from auth pages
 *   - Each dashboard route is restricted to its role (admin/company/student)
 */

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: LoginView },
  { path: '/register', component: RegisterView },
  // Each dashboard route has a meta.role that the guard checks against localStorage.
  { path: '/admin/dashboard', component: AdminDashboardView, meta: { role: 'admin' } },
  { path: '/company/dashboard', component: CompanyDashboardView, meta: { role: 'company' } },
  { path: '/student/dashboard', component: StudentDashboardView, meta: { role: 'student' } },
]

const router = VueRouter.createRouter({
  history: VueRouter.createWebHashHistory(),
  routes,
})

// Navigation guard — runs before every route change.
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')  // JWT token (set on login)
  const role = localStorage.getItem('role')     // 'admin', 'company', or 'student'

  // If going to login/register and already logged in, redirect to their dashboard.
  if (to.path === '/login' || to.path === '/register') {
    return token ? next(`/${role}/dashboard`) : next()
  }

  // Not logged in? Send to login page.
  if (!token) return next('/login')

  // Logged in but trying to access a different role's dashboard? Redirect to own dashboard.
  if (to.meta.role && to.meta.role !== role) return next(`/${role}/dashboard`)

  // All good — proceed.
  next()
})
