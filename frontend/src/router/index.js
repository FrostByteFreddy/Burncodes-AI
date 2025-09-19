import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

import Login from '../views/Login.vue'
import Signup from '../views/Signup.vue'
import Tenant from '../views/Tenant.vue'
import Profile from '../views/Profile.vue' 
import Chat from '../views/Chat.vue'
import ManageTenants from '../views/ManageTenants.vue'
import Subscription from '../views/Subscription.vue'
import TenantSettings from '../components/tenant/Settings.vue'
import TenantSources from '../components/tenant/Sources.vue'
import TenantAdvanced from '../components/tenant/Advanced.vue'

const uuidRegex = '[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}';

const routes = [
  { path: '/', redirect: '/manage-tenants' },
  { path: '/login', name: 'Login', component: Login, meta: { public: true } },
  { path: '/signup', name: 'Signup', component: Signup, meta: { public: true } },
  {
    path: `/tenant/:tenantId(${uuidRegex})`,
    name: 'Tenant',
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
  { path: '/manage-tenants', name: 'ManageTenants', component: ManageTenants, meta: { requiresAuth: true } },
  { path: '/subscription', name: 'Subscription', component: Subscription, meta: { requiresAuth: true } },
  { path: `/chat/:tenantId(${uuidRegex})`, name: 'Chat', component: Chat, meta: { public: true }, props: true },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore();
  const tenantsStore = useTenantsStore(); // Make sure to import useTenantsStore

  // Try to auto-login user from session/localStorage
  if (!authStore.user) {
    await authStore.fetchUser();
  }

  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);

  if (requiresAuth && !authStore.user) {
    return next('/login');
  }

  // If navigating to a tenant route, ensure tenant data is loaded before proceeding
  if (to.params.tenantId && !tenantsStore.currentTenant) {
    await tenantsStore.fetchTenant(to.params.tenantId);
  }

  if ((to.name === 'Login' || to.name === 'Signup') && authStore.user) {
    return next('/manage-tenants');
  }

  next();
});

export default router
