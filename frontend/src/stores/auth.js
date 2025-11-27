import { defineStore } from "pinia";
import { ref } from "vue";
import { supabase } from "../supabase";
import router from "../router";
import { useToast } from "../composables/useToast";
import i18n from "../i18n";

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
      if (user.value?.user_metadata?.language) {
        i18n.global.locale.value = user.value.user_metadata.language;
      }
    }
  }

  async function signUp(email, password, firstName, lastName, language) {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          first_name: firstName,
          last_name: lastName,
          language: language,
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
    if (user.value?.user_metadata?.language) {
      i18n.global.locale.value = user.value.user_metadata.language;
    }
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

    try {
      // Attempt to sign out from Supabase
      const { error } = await supabase.auth.signOut();
      if (error) {
        // Ignore "session_not_found" and "Auth session missing!"
        if (
          error.code !== "session_not_found" &&
          error.message !== "Auth session missing!"
        ) {
          console.error("Error signing out from Supabase:", error.message);
        }
      }
    } catch (err) {
      console.error("Unexpected error during logout:", err);
    } finally {
      // Force cleanup regardless of server errors

      // Clear local state
      user.value = null;
      session.value = null;

      // Clear all Supabase tokens from localStorage
      for (let i = localStorage.length - 1; i >= 0; i--) {
        const key = localStorage.key(i);
        if (key && key.startsWith("sb-") && key.endsWith("-auth-token")) {
          localStorage.removeItem(key);
        }
      }

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
  }

  // Listen for auth state changes
  supabase.auth.onAuthStateChange((event, _session) => {
    if (event === "SIGNED_IN") {
      session.value = _session;
      user.value = _session.user;
      if (user.value?.user_metadata?.language) {
        i18n.global.locale.value = user.value.user_metadata.language;
      }
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

  async function changePassword(currentPassword, newPassword) {
    if (!session.value?.access_token) throw new Error("User not logged in.");

    const API_BASE_URL =
      import.meta.env.VITE_API_BASE_URL || "http://localhost:5000/api";

    const response = await fetch(`${API_BASE_URL}/auth/change-password`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${session.value.access_token}`,
      },
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || "Failed to change password");
    }

    return await response.json();
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
    changePassword,
  };
});
