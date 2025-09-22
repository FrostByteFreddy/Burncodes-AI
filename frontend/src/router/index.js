import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";

import Login from "../views/Login.vue";
import Signup from "../views/Signup.vue";
import Tenant from "../views/Tenant.vue";
import Profile from "../views/Profile.vue";
import Chat from "../views/Chat.vue";
import ManageTenants from "../views/ManageTenants.vue";
import Subscription from "../views/Subscription.vue";
import TenantSettings from "../components/tenant/Settings.vue";
import TenantSources from "../components/tenant/Sources.vue";
import TenantFineTune from "../components/tenant/FineTune.vue";

const uuidRegex =
  "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}";

const routes = [
  { path: "/", redirect: "/manage-tenants" },
  { path: "/login", name: "Login", component: Login, meta: { public: true } },
  {
    path: "/signup",
    name: "Signup",
    component: Signup,
    meta: { public: true },
  },
  {
    path: `/tenant/:tenantId(${uuidRegex})`,
    name: "Tenant",
    component: Tenant,
    meta: { requiresAuth: true },
    props: true,
    children: [
      { path: "", redirect: { name: "TenantSettings" } },
      { path: "settings", name: "TenantSettings", component: TenantSettings },
      { path: "sources", name: "TenantSources", component: TenantSources },
      { path: "fine-tune", name: "TenantFineTune", component: TenantFineTune },
    ],
  },
  {
    path: "/profile",
    name: "Profile",
    component: Profile,
    meta: { requiresAuth: true },
  },
  {
    path: "/manage-tenants",
    name: "ManageTenants",
    component: ManageTenants,
    meta: { requiresAuth: true },
  },
  {
    path: "/subscription",
    name: "Subscription",
    component: Subscription,
    meta: { requiresAuth: true },
  },
  {
    path: `/chat/:tenantId(${uuidRegex})`,
    name: "Chat",
    component: Chat,
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

export default router;
