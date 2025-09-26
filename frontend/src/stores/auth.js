import { defineStore } from "pinia";
import { ref } from "vue";
import { supabase } from "../supabase";
import router from "../router";
import { useToast } from "../composables/useToast";

export const useAuthStore = defineStore("auth", () => {
  const user = ref(null);
  const session = ref(null);
  const sessionExpired = ref(false);

  const { addToast } = useToast();

  async function fetchUser() {
    const { data, error } = await supabase.auth.getSession();
    if (error) {
      console.error("Error fetching session:", error);
      user.value = null;
      session.value = null;
    } else {
      session.value = data.session;
      user.value = data.session?.user ?? null;
    }
  }

  async function signUp(email, password, firstName, lastName) {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          first_name: firstName,
          last_name: lastName,
        },
      },
    });
    if (error) throw error;
    // Let onAuthStateChange handle setting the user and session
    return data;
  }

  async function login(email, password) {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    if (error) throw error;

    session.value = data.session;
    user.value = data.user;
    sessionExpired.value = false; // Reset on new login

    const lastRoute = localStorage.getItem("lastVisitedRoute");
    if (lastRoute) {
      router.push(lastRoute);
    } else {
      router.push("/manage-tenants");
    }
  }

  async function logout() {
    sessionExpired.value = false; // Also reset on logout

    // Attempt to sign out from Supabase, but don't let it block local cleanup
    const { error } = await supabase.auth.signOut();
    if (error) {
      // Log the error but continue with cleanup, as the session might already be invalid
      console.error("Error signing out from Supabase:", error.message);
    }

    // Clear local state
    user.value = null;
    session.value = null;

    // Dynamically import tenants store to clear its state and avoid circular deps
    const { useTenantsStore } = await import("./tenants");
    const tenantsStore = useTenantsStore();
    tenantsStore.selectTenant(null); // This clears currentTenant and localStorage key via watcher

    localStorage.removeItem("lastVisitedRoute");

    // Redirect to login page if not already there
    if (router.currentRoute.value.name !== "Login") {
      router.push("/login");
    }
  }

  // Listen for auth state changes
  supabase.auth.onAuthStateChange((event, _session) => {
    if (event === "SIGNED_IN") {
      session.value = _session;
      user.value = _session.user;
      sessionExpired.value = false;
    } else if (event === "SIGNED_OUT") {
      user.value = null;
      session.value = null;
    }
  });

  async function updateProfile(profileData) {
    if (!user.value) throw new Error("User not logged in.");

    const { data, error } = await supabase.auth.updateUser({
      data: profileData,
    });

    if (error) throw error;

    // Update the user object in the store
    if (data.user) {
      user.value = data.user;
    }
    return data.user;
  }

  async function handleSessionExpired() {
    addToast("Your session has expired. Please log in again.", "error");
    await logout();
  }

  return {
    user,
    session,
    sessionExpired,
    fetchUser,
    signUp,
    login,
    logout,
    updateProfile,
    handleSessionExpired,
  };
});