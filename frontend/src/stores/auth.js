import { defineStore } from 'pinia'
import { ref } from 'vue'
import { supabase } from '../supabase'
import router from '../router'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const session = ref(null)

  async function fetchUser() {
    const { data, error } = await supabase.auth.getSession()
    if (error) {
      console.error('Error fetching session:', error)
      user.value = null
      session.value = null
    } else {
      session.value = data.session
      user.value = data.session?.user ?? null
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
    })
    if (error) throw error
    // Let onAuthStateChange handle setting the user and session
    return data
  }

  async function login(email, password) {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })
    if (error) throw error
    // Wait a moment for the session to be set by the client
    await new Promise(r => setTimeout(r, 200));
    await fetchUser();
    router.push('/dashboard')
  }

  async function logout() {
    const { error } = await supabase.auth.signOut()
    if (error) throw error
    user.value = null
    router.push('/login')
  }

  // Listen for auth state changes
  supabase.auth.onAuthStateChange((event, session) => {
    if (event === 'SIGNED_IN') {
      user.value = session.user
      fetchUser() // Fetch profile on sign in
    } else if (event === 'SIGNED_OUT') {
      user.value = null
    }
  })

  async function updateProfile(profileData) {
    if (!user.value) throw new Error('User not logged in.')

    const { data, error } = await supabase.auth.updateUser({
        data: profileData
    })

    if (error) throw error

    // Update the user object in the store
    if (data.user) {
        user.value = data.user
    }
    return data.user
  }

  return { user, fetchUser, signUp, login, logout, updateProfile }
})
