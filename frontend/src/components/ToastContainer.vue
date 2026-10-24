<template>
  <!-- Notices drop in at the top of the content column, clear of the sidebar and save bars -->
  <div class="toasts" :class="{ 'toasts--sidebar': withSidebar }">
    <div class="sr-live" aria-live="polite">{{ politeText }}</div>
    <div class="sr-live" aria-live="assertive">{{ urgentText }}</div>
    <TransitionGroup name="toast" tag="ol" class="toasts__list">
      <li
        v-for="toast in toasts"
        :key="toast.id"
        class="toast"
        :class="`toast--${toast.type}`"
        @mouseenter="pauseToast(toast.id)"
        @mouseleave="resumeToast(toast.id)"
        @focusin="pauseToast(toast.id)"
        @focusout="resumeToast(toast.id)"
      >
        <span class="toast__icon" aria-hidden="true">
          <font-awesome-icon :icon="['fas', ICONS[toast.type]]" />
        </span>
        <p class="toast__text">{{ toast.message }}</p>
        <button type="button" class="toast__close" :aria-label="$t('common.close')" @click="removeToast(toast.id)">
          <font-awesome-icon :icon="['fas', 'xmark']" />
        </button>
        <span
          :key="`${toast.id}-${toast.restarts}`"
          class="toast__time"
          :class="{ 'toast__time--paused': toast.paused }"
          :style="{ animationDuration: `${toast.duration}ms` }"
          aria-hidden="true"
        ></span>
      </li>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useToast } from '../composables/useToast'

defineProps({ withSidebar: { type: Boolean, default: false } })

const { toasts, removeToast, pauseToast, resumeToast } = useToast()

const ICONS = { success: 'check', error: 'exclamation', warning: 'triangle-exclamation', info: 'info' }

// Screen readers: errors interrupt, everything else waits its turn
const latest = (urgent) => [...toasts].reverse().find((t) => (t.type === 'error') === urgent)?.message || ''
const urgentText = computed(() => latest(true))
const politeText = computed(() => latest(false))
</script>

<style scoped>
.toasts {
  position: fixed; z-index: 1000; top: 16px;
  left: 50%;
  transform: translateX(-50%);
  width: min(440px, calc(100vw - 32px));
  pointer-events: none;
}
/* centre of the content column: the sidebar takes the first --sidebar-width */
.toasts--sidebar { left: calc(50% + var(--sidebar-width) / 2); }
.toasts__list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }

.toast {
  position: relative; overflow: hidden; pointer-events: auto;
  display: grid; grid-template-columns: 28px minmax(0, 1fr) 28px; align-items: center; gap: 12px;
  padding: 12px 10px 12px 12px;
  border-radius: var(--radius-lg);
  background: var(--surface-2); border: 1px solid var(--surface-3);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.45);
}
.toast__icon {
  width: 28px; height: 28px; border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center; font-size: 13px;
}
.toast--success .toast__icon { background: var(--status-success-soft); color: var(--status-success); }
.toast--error .toast__icon   { background: var(--status-error-soft, rgba(255, 107, 107, 0.15)); color: var(--status-error); }
.toast--warning .toast__icon { background: var(--status-warning-soft); color: var(--status-warning); }
.toast--info .toast__icon    { background: var(--interactive-soft); color: var(--interactive); }
.toast--error { border-color: rgba(255, 107, 107, 0.45); }

.toast__text { font-size: var(--text-sm); line-height: 1.45; color: var(--surface-heading); overflow-wrap: anywhere; }
.toast__close {
  width: 28px; height: 28px; border-radius: var(--radius-md); border: none; background: none;
  color: var(--surface-muted); cursor: pointer;
}
.toast__close:hover { color: var(--surface-heading); background: var(--surface-3); }

/* Time left, drawn as a line that shrinks; stops while hovered */
.toast__time {
  position: absolute; left: 0; bottom: 0; height: 2px; width: 100%;
  transform-origin: left; animation: toast-time linear forwards;
  background: currentColor; opacity: 0.6;
}
.toast--success .toast__time { color: var(--status-success); }
.toast--error .toast__time   { color: var(--status-error); }
.toast--warning .toast__time { color: var(--status-warning); }
.toast--info .toast__time    { color: var(--interactive); }
.toast__time--paused { animation-play-state: paused; }
@keyframes toast-time { from { transform: scaleX(1); } to { transform: scaleX(0); } }

.toast-enter-active, .toast-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.toast-enter-from { opacity: 0; transform: translateY(-12px); }
.toast-leave-to { opacity: 0; transform: translateY(-6px) scale(0.98); }
.toast-move { transition: transform 0.2s ease; }

.sr-live { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }

@media (max-width: 768px) {
  /* below the mobile top bar, centred on the screen */
  .toasts--sidebar { top: 64px; left: 50%; }
}
@media (prefers-reduced-motion: reduce) {
  .toast-enter-from, .toast-leave-to { transform: none; }
  .toast-move { transition: none; }
  .toast__time { animation: none; display: none; }
}
</style>
