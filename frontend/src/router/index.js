import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";

const uuidRegex =
  "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}";

const routes = [
  { path: "/", redirect: "/manage-tenants" },
  { path: "/login", name: "Login", component: () => import("../views/Login.vue"), meta: { public: true } },
  {
    path: "/signup",
    name: "Signup",
    component: () => import("../views/Signup.vue"),
    meta: { public: true },
  },
  {
    path: `/tenant/:tenantId(${uuidRegex})`,
    name: "Tenant",
    component: () => import("../views/Tenant.vue"),
    meta: { requiresAuth: true },
    props: true,
    children: [
      { path: "", redirect: { name: "TenantSettings" } },
      { path: "settings", name: "TenantSettings", component: () => import("../components/tenant/Settings.vue") },
      { path: "sources", name: "TenantSources", component: () => import("../components/tenant/Sources.vue") },
      { path: "fine-tune", name: "TenantFineTune", component: () => import("../components/tenant/FineTune.vue") },
      { path: "analytics", name: "Analytics", component: () => import("@/views/Analytics.vue") },
      { path: "chat-logs", name: "ChatLogs", component: () => import("@/views/ChatLogs.vue") },
    ],
  },
  {
    path: "/profile",
    name: "Profile",
    component: () => import("../views/Profile.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/manage-tenants",
    name: "ManageTenants",
    component: () => import("../views/ManageTenants.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/subscription",
    name: "Subscription",
    component: () => import("../views/Subscription.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: `/chat/:tenantId(${uuidRegex})`,
    name: "Chat",
    component: () => import("../views/Chat.vue"),
    meta: { public: true },
    props: true,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore();

  let sessionFoundInStorage = false;
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key && key.startsWith("sb-") && key.endsWith("-auth-token")) {
      sessionFoundInStorage = true;
      break;
    }
  }

  // Try to auto-login user from session/localStorage
  if (!authStore.user) {
    await authStore.fetchUser();
  }

  if (sessionFoundInStorage && !authStore.user) {
    console.log("Session expired, showing modal.");
    authStore.sessionExpired = true;
  }

  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth);
  const isPublic = to.matched.some((record) => record.meta.public);

  if (requiresAuth && !authStore.user) {
    // Redirect to login if route requires auth and user is not logged in
    next("/login");
  } else if ((to.name === "Login" || to.name === "Signup") && authStore.user) {
    // If user is logged in, redirect from login/signup to the main view
    next("/manage-tenants");
  } else {
    // Otherwise, proceed
    next();
  }
});

router.afterEach((to) => {
  if (to.name !== 'Login' && to.name !== 'Signup') {
    localStorage.setItem('lastVisitedRoute', to.fullPath);
  }
});

export default router;
