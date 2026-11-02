<template>
  <div class="auth">
    <!-- Brand panel: flat indigo, as on the website; only the logo has the gradient -->
    <aside class="auth-brand">
      <div class="auth-brand__noise"></div>
      <img src="/logo_white.svg" alt="Burncodes AI" class="auth-brand__logo" />
      <div class="auth-brand__foot">
        <p class="auth-brand__tagline">{{ tagline }}</p>
        <p class="auth-brand__powered"><span></span>{{ $t('auth.poweredBy') }}</p>
      </div>
    </aside>

    <main class="auth-main">
      <div class="auth-form">
        <img src="/logo.svg" alt="Burncodes AI" class="auth-form__logo" />
        <slot />
      </div>
    </main>
  </div>
</template>

<script setup>
defineProps({ tagline: { type: String, required: true } });
</script>

<style scoped>
.auth { min-height: 100dvh; display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); background: var(--surface-1); }

.auth-brand {
  position: relative; overflow: hidden; display: flex; flex-direction: column; justify-content: space-between;
  padding: var(--space-12); color: #fff;
  background: var(--brand-indigo);
}
.auth-brand__noise {
  position: absolute; inset: 0; opacity: 0.03; pointer-events: none;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
}
.auth-brand__logo { position: relative; height: 48px; width: auto; align-self: flex-start; }
.auth-brand__foot { position: relative; max-width: 30ch; }
.auth-brand__tagline { font-size: 26px; line-height: 36px; font-weight: 400; color: rgba(255, 255, 255, 0.92); margin-bottom: var(--space-6); }
.auth-brand__powered { display: flex; align-items: center; gap: var(--space-3); font-size: 14px; color: rgba(255, 255, 255, 0.72); }
.auth-brand__powered span { width: 32px; height: 1px; background: rgba(255, 255, 255, 0.5); }

.auth-main { display: flex; align-items: center; justify-content: center; padding: var(--space-12) var(--space-6); overflow-y: auto; }
.auth-form { width: 100%; max-width: 400px; display: flex; flex-direction: column; gap: var(--space-6); }
.auth-form__logo { display: none; height: 40px; width: auto; align-self: center; }

/* shared by both forms */
.auth-form :deep(.auth-title) { font-size: 32px; line-height: 40px; font-weight: 700; letter-spacing: -0.01em; }
.auth-form :deep(.auth-sub) { margin-top: var(--space-2); color: var(--text-secondary); }
.auth-form :deep(.auth-fields) { display: flex; flex-direction: column; gap: var(--space-4); }
.auth-form :deep(.auth-row) { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-4); }
.auth-form :deep(.auth-submit:hover:not(:disabled)) { filter: brightness(1.08); }
.auth-form :deep(.auth-submit:disabled) { background: var(--surface-2); color: var(--text-disabled); }

@media (max-width: 1023px) {
  .auth { grid-template-columns: minmax(0, 1fr); }
  .auth-brand { display: none; }
  .auth-form__logo { display: block; }
}
</style>
