import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { ONBOARDING_PARAM, markOnboardingPending, onboardingPending } from "../utils/onboarding";

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
    component: () => import("../views/Tenant.vue"),
    meta: { requiresAuth: true },
    props: true,
    children: [
      { path: "", redirect: { name: "TenantOverview" } },
      { path: "overview",  name: "TenantOverview",  component: () => import("../views/Overview.vue") },
      { path: "sources",   name: "TenantSources",   component: () => import("../components/tenant/Sources.vue") },
      { path: "sources/calendar", name: "TenantCalendar", component: () => import("../components/tenant/MonthCalendar.vue") },
      { path: "sources/crawls/:jobId(\\d+)", name: "TenantCrawl", component: () => import("../components/tenant/CrawlDetail.vue"), props: true },
      { path: "configure", name: "TenantConfigure", component: () => import("../components/tenant/Settings.vue") },
      { path: "insights",  name: "TenantInsights",  component: () => import("../views/Insights.vue") },
      { path: "install",   name: "TenantInstall",   component: () => import("../views/Install.vue") },
      { path: "test-page", name: "TenantTestPage",  component: () => import("../views/TestPage.vue") },
      { path: "settings",  name: "TenantSettings",  component: () => import("../views/TenantSettings.vue") },
    ],

  },
  {
    path: "/settings/:section?",
    name: "AccountSettings",
    component: () => import("../views/AccountSettings.vue"),
    meta: { requiresAuth: true },
  },
  // Old addresses; Stripe sessions started before the move return to /subscription
  { path: "/profile", redirect: { name: "AccountSettings", params: { section: "profile" } } },
  { path: "/subscription", redirect: (to) => ({ name: "AccountSettings", params: { section: "billing" }, query: to.query }) },
  {
    path: "/onboarding",
    name: "Onboarding",
    component: () => import("../views/Onboarding.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: "/manage-tenants",
    name: "ManageTenants",
    component: () => import("../views/ManageTenants.vue"),
    meta: { requiresAuth: true },
  },
  {
    path: `/chat/:tenantId(${uuidRegex})`,
    name: "Chat",
    component: () => import("../views/Chat.vue"),
    meta: { public: true, skipAuth: true },
    props: true,
  },
  {
    path: `/share/:shareId(${uuidRegex})`,
    name: "Share",
    component: () => import("../views/ShareView.vue"),
    meta: { public: true, skipAuth: true },
    props: true,
  },
];

// The app is served under /dashboard/, except the public /chat and /share pages,
// whose addresses are embedded on customer websites
const base = window.location.pathname.startsWith(import.meta.env.BASE_URL) ? import.meta.env.BASE_URL : "/";

const router = createRouter({
  history: createWebHistory(base),
  routes,
});

router.beforeEach(async (to, from, next) => {
  // Fully public standalone routes — skip auth entirely
  if (to.meta.skipAuth) return next();

  const authStore = useAuthStore();

  // ?onboarding on any address: the guided setup opens once logged in
  const wantsOnboarding = ONBOARDING_PARAM in to.query;
  if (wantsOnboarding) markOnboardingPending();

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
    next(onboardingPending() ? { name: "Onboarding" } : "/manage-tenants");
  } else if (wantsOnboarding && authStore.user && to.name !== "Onboarding") {
    next({ name: "Onboarding" });
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
