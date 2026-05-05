<template>
  <div class="page">
    <div class="page-header">
      <p class="page-label">{{ $t('profile.title').toUpperCase() }}</p>
    </div>

    <!-- Avatar row -->
    <div class="avatar-row">
      <div class="user-avatar-lg">{{ userInitial }}</div>
      <div>
        <p class="avatar-name">{{ userName || authStore.user?.email }}</p>
        <p class="avatar-email">{{ authStore.user?.email }}</p>
      </div>
    </div>

    <!-- Account Details -->
    <section class="form-section">
      <div class="section-header">
        <span class="section-label">{{ $t('profile.accountDetails') }}</span>
        <div class="section-line"></div>
      </div>
      <form v-if="authStore.user" @submit.prevent="handleUpdate" class="form-grid">
        <div class="field">
          <label class="field__label">{{ $t('profile.first_name') }}</label>
          <input v-model="formData.first_name" type="text" class="field__input" />
        </div>
        <div class="field">
          <label class="field__label">{{ $t('profile.last_name') }}</label>
          <input v-model="formData.last_name" type="text" class="field__input" />
        </div>
        <div class="field field--full">
          <label class="field__label">{{ $t('profile.email') }}</label>
          <div class="field__input-wrap">
            <input :value="authStore.user.email" type="email" class="field__input field__input--disabled" disabled />
            <font-awesome-icon :icon="['fas', 'lock']" class="field__lock-icon" />
          </div>
        </div>
        <div class="field">
          <label class="field__label">{{ $t('profile.phone_number') }}</label>
          <input v-model="formData.phone_number" type="tel" class="field__input" />
        </div>
        <div class="field">
          <label class="field__label">{{ $t('profile.language') }}</label>
          <select v-model="formData.language" class="field__input field__select">
            <option value="en">English</option>
            <option value="de">Deutsch</option>
            <option value="fr">Français</option>
          </select>
        </div>
        <div class="field--full form-actions">
          <button type="submit" :disabled="loading" class="btn-save" :class="{ 'btn-save--saved': justSaved }">
            <font-awesome-icon v-if="loading" :icon="['fas', 'spinner']" class="spin" />
            <font-awesome-icon v-else-if="justSaved" :icon="['fas', 'check']" />
            <span>{{ loading ? $t('profile.saving') : justSaved ? $t('profile.saved') : $t('profile.save_changes') }}</span>
          </button>
        </div>
      </form>
    </section>

    <!-- Change Password -->
    <section class="form-section">
      <div class="section-header">
        <span class="section-label">{{ $t('profile.changePassword') }}</span>
        <div class="section-line"></div>
      </div>
      <form @submit.prevent="handleChangePassword" class="form-grid">
        <div class="field field--full">
          <label class="field__label">{{ $t('profile.security.currentPassword') }}</label>
          <input v-model="passwordData.currentPassword" type="password" class="field__input" required />
        </div>
        <div class="field">
          <label class="field__label">{{ $t('profile.security.newPassword') }}</label>
          <input v-model="passwordData.newPassword" type="password" class="field__input" required minlength="6" />
        </div>
        <div class="field">
          <label class="field__label">{{ $t('profile.security.confirmPassword') }}</label>
          <input v-model="passwordData.confirmPassword" type="password" class="field__input" required minlength="6" />
        </div>
        <div class="field--full form-actions">
          <button type="submit" :disabled="passwordLoading" class="btn-save">
            <font-awesome-icon v-if="passwordLoading" :icon="['fas', 'spinner']" class="spin" />
            <span>{{ passwordLoading ? $t('profile.security.updating') : $t('profile.security.updatePassword') }}</span>
          </button>
        </div>
      </form>
    </section>

    <!-- Danger Zone -->
    <section class="form-section">
      <div class="section-header">
        <span class="section-label section-label--danger">{{ $t('profile.dangerZone') }}</span>
        <div class="section-line section-line--danger"></div>
      </div>
      <p class="danger-desc">{{ $t('profile.deleteAccountDesc') }}</p>
      <button class="btn-danger-outline" disabled>
        {{ $t('profile.deleteAccount') }}
      </button>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useToast } from '../composables/useToast'
import { useI18n } from 'vue-i18n'

const authStore = useAuthStore()
const { addToast } = useToast()
const { t, locale } = useI18n()

const loading = ref(false)
const passwordLoading = ref(false)
const justSaved = ref(false)

const formData = ref({ first_name: '', last_name: '', phone_number: '', language: 'en' })
const passwordData = ref({ currentPassword: '', newPassword: '', confirmPassword: '' })

const userInitial = computed(() => {
  const meta = authStore.user?.user_metadata
  if (meta?.first_name) return meta.first_name[0].toUpperCase()
  return authStore.user?.email?.[0]?.toUpperCase() || '?'
})

const userName = computed(() => {
  const meta = authStore.user?.user_metadata
  if (meta?.first_name) return `${meta.first_name} ${meta.last_name || ''}`.trim()
  return ''
})

const setFormData = () => {
  const meta = authStore.user?.user_metadata
  if (meta) formData.value = {
    first_name: meta.first_name || '',
    last_name: meta.last_name || '',
    phone_number: meta.phone_number || '',
    language: meta.language || 'en',
  }
}

onMounted(async () => {
  if (!authStore.user) await authStore.fetchUser()
  setFormData()
})
watch(() => authStore.user, setFormData, { deep: true })

const handleUpdate = async () => {
  loading.value = true
  try {
    await authStore.updateProfile(formData.value)
    if (formData.value.language) locale.value = formData.value.language
    justSaved.value = true
    setTimeout(() => { justSaved.value = false }, 2000)
  } catch {
    addToast(t('profile.error'), 'error')
  } finally {
    loading.value = false
  }
}

const handleChangePassword = async () => {
  if (passwordData.value.newPassword !== passwordData.value.confirmPassword) {
    addToast(t('profile.security.passwordMismatch'), 'error')
    return
  }
  passwordLoading.value = true
  try {
    await authStore.changePassword(passwordData.value.currentPassword, passwordData.value.newPassword)
    addToast(t('profile.security.success'), 'success')
    passwordData.value = { currentPassword: '', newPassword: '', confirmPassword: '' }
  } catch (e) {
    addToast(e.message || t('profile.security.error'), 'error')
  } finally {
    passwordLoading.value = false
  }
}
</script>

<style scoped>
.page { max-width: 560px; }

.page-header { margin-bottom: 24px; }
.page-label {
  font-size: 11px; font-weight: 700;
  letter-spacing: 0.08em;
  color: var(--surface-muted);
}

.avatar-row {
  display: flex; align-items: center; gap: 16px;
  margin-bottom: 36px;
  padding: 20px;
  background: var(--surface-1);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-lg);
}
.user-avatar-lg {
  width: 48px; height: 48px;
  border-radius: 50%;
  background: var(--gradient-brand);
  color: white; font-size: 18px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.avatar-name { font-size: 15px; font-weight: 600; color: var(--surface-heading); }
.avatar-email { font-size: 12px; color: var(--surface-muted); margin-top: 2px; }

.form-section { margin-bottom: 36px; }

.section-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
.section-label {
  font-size: 10px; font-weight: 700;
  letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--surface-muted); white-space: nowrap;
}
.section-label--danger { color: var(--status-error); }
.section-line { flex: 1; height: 1px; background: var(--surface-3); }
.section-line--danger { background: rgba(255,68,68,0.3); }

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.field { display: flex; flex-direction: column; gap: 6px; }
.field--full { grid-column: 1 / -1; }

.field__label {
  font-size: 11px; font-weight: 600;
  letter-spacing: 0.06em; text-transform: uppercase;
  color: var(--surface-muted);
}
.field__input {
  padding: 10px 14px;
  background: var(--surface-2);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-md);
  color: var(--surface-text);
  font-size: 14px;
  outline: none;
  transition: border-color var(--t-fast), box-shadow var(--t-fast);
  width: 100%;
}
.field__input:focus { border-color: var(--brand-indigo); box-shadow: 0 0 0 3px rgba(10,31,171,0.15); }
.field__input--disabled { background: var(--surface-0); color: var(--surface-muted); cursor: not-allowed; }
.field__select { appearance: none; cursor: pointer; }
.field__input-wrap { position: relative; }
.field__lock-icon {
  position: absolute; right: 12px; top: 50%;
  transform: translateY(-50%); color: var(--surface-muted); font-size: 12px;
}

.form-actions { display: flex; justify-content: flex-end; }

.btn-save {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 9px 20px;
  background: var(--gradient-brand);
  color: white; font-size: 13px; font-weight: 600;
  border: none; border-radius: var(--radius-md);
  cursor: pointer;
  transition: opacity var(--t-fast);
}
.btn-save:hover:not(:disabled) { opacity: 0.9; }
.btn-save:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-save--saved { background: var(--status-success) !important; }
.spin { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.danger-desc { font-size: 13px; color: var(--surface-muted); margin-bottom: 16px; }
.btn-danger-outline {
  padding: 8px 18px;
  background: none;
  border: 1px solid var(--status-error);
  color: var(--status-error);
  font-size: 13px; font-weight: 600;
  border-radius: var(--radius-md);
  cursor: not-allowed;
  opacity: 0.5;
}

@media (max-width: 520px) {
  .form-grid { grid-template-columns: 1fr; }
}
</style>
