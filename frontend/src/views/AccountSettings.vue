<template>
  <div class="set">
    <div class="page-head">
      <div>
        <h1 class="page-title">{{ $t('settings.title') }}</h1>
        <p class="page-lede">{{ $t('settings.lede') }}</p>
      </div>
    </div>

    <div class="set-layout">
      <!-- Sections; a dropdown on phones -->
      <nav class="set-nav" :aria-label="$t('settings.title')">
        <router-link
          v-for="s in SECTIONS"
          :key="s.key"
          :to="{ name: 'AccountSettings', params: { section: s.key } }"
          class="set-nav__item"
          :class="{ 'set-nav__item--on': current === s.key, 'set-nav__item--danger': s.key === 'danger' }"
        >
          <font-awesome-icon :icon="['fas', s.icon]" class="set-nav__icon" />
          {{ $t(`settings.sections.${s.key}`) }}
        </router-link>
      </nav>
      <select class="set-select" :value="current" :aria-label="$t('settings.title')" @change="go($event.target.value)">
        <option v-for="s in SECTIONS" :key="s.key" :value="s.key">{{ $t(`settings.sections.${s.key}`) }}</option>
      </select>

      <div class="set-body">
        <component :is="SECTIONS.find((s) => s.key === current).component" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import ProfileSection from '@/components/settings/ProfileSection.vue';
import SecuritySection from '@/components/settings/SecuritySection.vue';
import BillingSection from '@/components/settings/BillingSection.vue';
import SchedulesSection from '@/components/settings/SchedulesSection.vue';
import DangerSection from '@/components/settings/DangerSection.vue';

const SECTIONS = [
  { key: 'profile', icon: 'user', component: ProfileSection },
  { key: 'security', icon: 'lock', component: SecuritySection },
  { key: 'billing', icon: 'wallet', component: BillingSection },
  { key: 'schedules', icon: 'clock', component: SchedulesSection },
  { key: 'danger', icon: 'triangle-exclamation', component: DangerSection },
];

const route = useRoute();
const router = useRouter();
const current = computed(() => (SECTIONS.some((s) => s.key === route.params.section) ? route.params.section : 'profile'));
const go = (key) => router.push({ name: 'AccountSettings', params: { section: key } });
</script>

<style scoped>
.set-layout { display: grid; grid-template-columns: 200px minmax(0, 1fr); gap: 32px; align-items: start; }
.set-nav { position: sticky; top: 40px; display: flex; flex-direction: column; gap: 2px; }
.set-nav__item {
  display: flex; align-items: center; gap: 10px; padding: 9px 12px; border-radius: var(--radius-md);
  font-size: 15px; font-weight: 500; color: var(--surface-muted); text-decoration: none;
}
.set-nav__item:hover { color: var(--surface-heading); background: var(--surface-1); }
.set-nav__item--on { color: var(--surface-heading); background: var(--surface-1); font-weight: 700; box-shadow: inset 3px 0 0 var(--interactive); }
.set-nav__item--danger { margin-top: 12px; }
.set-nav__item--danger.set-nav__item--on { box-shadow: inset 3px 0 0 var(--status-error); }
.set-nav__icon { width: 16px; }
.set-select { display: none; }
.set-body { min-width: 0; display: flex; flex-direction: column; gap: 20px; max-width: 820px; }

@media (max-width: 760px) {
  .set-layout { grid-template-columns: minmax(0, 1fr); gap: 16px; }
  .set-nav { display: none; }
  .set-select {
    display: block; width: 100%; padding: 10px 12px; border-radius: var(--radius-md);
    background: var(--surface-1); border: 1px solid var(--surface-3); color: var(--surface-heading); font: inherit;
  }
}
</style>
