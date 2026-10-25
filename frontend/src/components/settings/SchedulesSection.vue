<template>
  <section class="panel">
    <h2 class="panel-title">{{ $t('settings.schedules.title') }}</h2>
    <p class="panel-sub">{{ $t('settings.schedules.sub') }}</p>

    <div v-if="!loaded" style="margin-top: 16px" aria-busy="true">
      <div v-for="n in 2" :key="n" class="ghost-row"><span class="ghost ghost--line" style="flex: 1"></span><span class="ghost ghost--btn" style="width: 160px"></span><span class="ghost ghost--btn" style="width: 160px"></span></div>
    </div>
    <p v-else-if="!tenants.length" class="meta" style="margin-top: 12px">{{ $t('settings.schedules.none') }}</p>

    <table v-else class="sch-table">
      <thead>
        <tr>
          <th>{{ $t('settings.schedules.chatbot') }}</th>
          <th>{{ $t('settings.schedules.websites') }}</th>
          <th>{{ $t('settings.schedules.reviews') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="t in tenants" :key="t.id">
          <th scope="row">
            <router-link :to="{ name: 'TenantOverview', params: { tenantId: t.id } }" class="sch-name">{{ t.name }}</router-link>
            <span v-if="t.is_active === false" class="sch-off">{{ $t('settings.schedules.switchedOff') }}</span>
          </th>
          <td>
            <select class="sch-select" :value="t.auto_recrawl ? String(t.recrawl_interval_days || 7) : 'off'" :disabled="saving === t.id" :aria-label="`${t.name}: ${$t('settings.schedules.websites')}`"
              @change="save(t, $event.target.value === 'off' ? { auto_recrawl: false } : { auto_recrawl: true, recrawl_interval_days: Number($event.target.value) })">
              <option value="off">{{ $t('settings.schedules.off') }}</option>
              <option v-for="n in [7, 14, 30]" :key="n" :value="String(n)">{{ $t(`knowledge.recrawl.every${n}`) }}</option>
            </select>
          </td>
          <td>
            <select class="sch-select" :value="t.review_chats ? String(t.review_interval_days || 1) : 'off'" :disabled="saving === t.id" :aria-label="`${t.name}: ${$t('settings.schedules.reviews')}`"
              @change="save(t, $event.target.value === 'off' ? { review_chats: false } : { review_chats: true, review_interval_days: Number($event.target.value) })">
              <option value="off">{{ $t('settings.schedules.off') }}</option>
              <option value="1">{{ $t('overview.auto.daily') }}</option>
              <option value="7">{{ $t('overview.auto.weekly') }}</option>
            </select>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- What re-crawls leave out: set in a crawl's selection, removable here -->
    <section v-for="t in tenantsWithExclusions" :key="`ex-${t.id}`" class="sch-ex">
      <h3 class="sch-ex__title">{{ $t('settings.schedules.excludedTitle', { name: t.name }) }}</h3>
      <ul class="sch-ex__list">
        <li v-for="r in excludedOf(t)" :key="r.path || r.url" class="sch-ex__item">
          <font-awesome-icon :icon="['fas', r.path ? 'folder' : 'file-lines']" class="sch-ex__icon" />
          <span class="sch-ex__label">
            {{ r.title || r.path || r.url }}
            <span class="meta">{{ r.path || r.url }}</span>
          </span>
          <button type="button" class="btn-quiet" :disabled="saving === t.id" @click="removeExclusion(t, r)">{{ $t('settings.schedules.excludedRemove') }}</button>
        </li>
      </ul>
    </section>

    <ul class="sch-notes">
      <li>{{ $t('overview.auto.recrawlHow') }}</li>
      <li>{{ $t('settings.schedules.reviewNote') }}</li>
      <li v-if="tenantsWithExclusions.length">{{ $t('settings.schedules.excludedNote') }}</li>
    </ul>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import apiClient from '@/utils/api';
import { useTenantsStore } from '@/stores/tenants';
import { useToast } from '@/composables/useToast';

const tenantsStore = useTenantsStore();
const { addToast } = useToast();
const { t } = useI18n();
const loaded = ref(false);
const saving = ref(null);
const tenants = computed(() => tenantsStore.tenants || []);

// Only "leave out" rules are listed; "keep" rules are exceptions inside them
const excludedOf = (tenant) => (tenant.crawl_exclusions || []).filter((r) => r.exclude);
const tenantsWithExclusions = computed(() => tenants.value.filter((x) => excludedOf(x).length));
const inside = (path, folder) => path === folder || path.startsWith(`${folder.replace(/\/$/, '')}/`);
const removeExclusion = (tenant, rule) => {
  const rest = (tenant.crawl_exclusions || []).filter((r) => r !== rule
    // a folder's exceptions go with it
    && !(rule.path && r.path && !r.exclude && inside(r.path, rule.path)));
  return save(tenant, { crawl_exclusions: rest });
};

onMounted(async () => { await tenantsStore.fetchTenants(); loaded.value = true; });

const save = async (tenant, payload) => {
  saving.value = tenant.id;
  try {
    await apiClient.put(`/tenants/${tenant.id}`, payload);
    Object.assign(tenant, payload);
    addToast(t('settings.saved'), 'success');
  } catch {
    addToast(t('tenant.settings.actions.saveFailed'), 'error');
    await tenantsStore.fetchTenants();
  } finally { saving.value = null; }
};
</script>

<style scoped>
.sch-table { width: 100%; margin-top: 16px; border-collapse: collapse; }
.sch-table thead th { text-align: left; font-size: var(--text-sm); font-weight: 600; color: var(--surface-muted); padding: 0 12px 8px 0; border-bottom: 1px solid var(--surface-3); }
.sch-table tbody th, .sch-table td { padding: 12px 12px 12px 0; border-bottom: 1px solid var(--surface-3); text-align: left; vertical-align: middle; }
.sch-table tbody tr:last-child th, .sch-table tbody tr:last-child td { border-bottom: none; }
.sch-name { font-size: 15px; font-weight: 700; color: var(--surface-heading); text-decoration: none; }
.sch-name:hover { color: var(--interactive); text-decoration: underline; }
.sch-off { margin-left: 8px; padding: 1px 8px; border-radius: var(--radius-pill); font-size: var(--text-xs); font-weight: 700; background: var(--status-error-soft, rgba(255, 107, 107, 0.12)); color: var(--status-error); }
.sch-select {
  width: 100%; min-width: 150px; padding: 8px 32px 8px 12px; border-radius: var(--radius-md);
  background-color: var(--surface-2); border: 1px solid var(--surface-3);
  color: var(--surface-heading); font: inherit; font-size: var(--text-sm); cursor: pointer;
}
.sch-select:hover:not(:disabled) { border-color: var(--surface-muted); }
.sch-ex { margin-top: 22px; display: flex; flex-direction: column; gap: 8px; }
.sch-ex__title { font-size: 15px; font-weight: 700; color: var(--surface-heading); }
.sch-ex__list { list-style: none; padding: 0; display: flex; flex-direction: column; border: 1px solid var(--surface-3); border-radius: var(--radius-md); }
.sch-ex__item { display: flex; align-items: center; gap: 12px; padding: 8px 12px; border-top: 1px solid var(--surface-3); font-size: var(--text-sm); }
.sch-ex__item:first-child { border-top: none; }
.sch-ex__icon { color: var(--surface-muted); flex-shrink: 0; }
.sch-ex__label { flex: 1; min-width: 0; display: flex; flex-direction: column; color: var(--surface-heading); overflow-wrap: anywhere; }
.sch-notes { margin: 18px 0 0; padding-left: 18px; display: flex; flex-direction: column; gap: 6px; font-size: var(--text-sm); color: var(--surface-muted); max-width: var(--measure); }

@media (max-width: 760px) {
  .sch-table thead { display: none; }
  .sch-table tr { display: grid; gap: 8px; padding: 12px 0; border-bottom: 1px solid var(--surface-3); }
  .sch-table tbody th, .sch-table td { padding: 0; border: none; }
}
</style>
