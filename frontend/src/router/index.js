import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

import Login from '../views/Login.vue'
import Signup from '../views/Signup.vue'
import Dashboard from '../views/Dashboard.vue'
import Tenant from '../views/Tenant.vue'
import Profile from '../views/Profile.vue' // We will create this view next
import Chat from '../views/Chat.vue' // We will create this view next
import TenantSettings from '../components/tenant/Settings.vue'
import TenantSources from '../components/tenant/Sources.vue'
import TenantAdvanced from '../components/tenant/Advanced.vue'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/login', name: 'Login', component: Login, meta: { public: true } },
  { path: '/signup', name: 'Signup', component: Signup, meta: { public: true } },
  { path: '/dashboard', name: 'Dashboard', component: Dashboard, meta: { requiresAuth: true } },
  {
    path: '/tenant/:tenantId',
    component: Tenant,
    meta: { requiresAuth: true },
    props: true,
    children: [
      { path: '', redirect: { name: 'TenantSettings' } },
      { path: 'settings', name: 'TenantSettings', component: TenantSettings },
      { path: 'sources', name: 'TenantSources', component: TenantSources },
      { path: 'advanced', name: 'TenantAdvanced', component: TenantAdvanced },
    ]
  },
  { path: '/profile', name: 'Profile', component: Profile, meta: { requiresAuth: true } },
  { path: '/chat/:tenantId', name: 'Chat', component: Chat, meta: { public: true }, props: true },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore();

  // Try to auto-login user from session/localStorage
  if (!authStore.user) {
    await authStore.fetchUser();
  }

  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const isPublic = to.matched.some(record => record.meta.public);

  if (requiresAuth && !authStore.user) {
    // Redirect to login if route requires auth and user is not logged in
    next('/login');
  } else if ((to.name === 'Login' || to.name === 'Signup') && authStore.user) {
    // If user is logged in, redirect from login/signup to dashboard
    next('/dashboard');
  }
  else {
    // Otherwise, proceed
    next();
  }
});

export default router
