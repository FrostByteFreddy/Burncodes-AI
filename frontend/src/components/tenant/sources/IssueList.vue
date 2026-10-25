<template>
  <div class="il">
    <section v-for="g in groups" :key="g.kind" class="il__group">
      <h3 class="il__title">
        <font-awesome-icon :icon="['fas', ICONS[g.kind] || 'triangle-exclamation']" class="il__icon" />
        {{ $t(`knowledge.issues.${g.kind}.title`) }}
        <span class="il__count">{{ g.items.length }}</span>
      </h3>
      <p class="il__hint">{{ $t(`knowledge.issues.${g.kind}.hint`) }}</p>
      <ul class="il__list">
        <li v-for="(it, i) in visible(g)" :key="i" class="il__item">
          <a :href="it.url" target="_blank" rel="noopener noreferrer" class="il__doc">{{ it.title }}</a>
          <span v-if="detail(it)" class="il__detail">{{ detail(it) }}</span>
        </li>
      </ul>
      <button v-if="g.items.length > LIMIT" type="button" class="il__more" @click="toggle(g.kind)">
        {{ open.has(g.kind) ? $t('knowledge.issues.showLess') : $t('knowledge.issues.showAll', { n: g.items.length }) }}
      </button>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive } from 'vue';
import { useI18n } from 'vue-i18n';

// issues: [{ kind, subject, n?, dates?, title, url }]
const props = defineProps({ issues: { type: Array, default: () => [] } });
const { t } = useI18n();

// most consequential first: what makes the chatbot answer wrongly
const ORDER = ['contradiction', 'expired', 'dates_rejected', 'dates_dropped', 'not_readable', 'unreadable'];
const ICONS = {
  contradiction: 'code-compare', expired: 'clock-rotate-left', dates_rejected: 'calendar-xmark',
  dates_dropped: 'calendar-minus', not_readable: 'image', unreadable: 'file-circle-xmark',
};
const LIMIT = 5;
const open = reactive(new Set());

const groups = computed(() => {
  const by = {};
  for (const it of props.issues) if (ORDER.includes(it.kind)) (by[it.kind] ||= []).push(it);
  return ORDER.filter((k) => by[k]).map((kind) => ({ kind, items: by[kind] }));
});
const visible = (g) => (open.has(g.kind) ? g.items : g.items.slice(0, LIMIT));
const toggle = (kind) => (open.has(kind) ? open.delete(kind) : open.add(kind));
const detail = (it) => {
  if (it.kind === 'dates_dropped') return t('knowledge.issues.dates_dropped.detail', { subject: it.subject, n: it.n, dates: (it.dates || []).join(', ') });
  return it.subject && it.subject !== it.title ? it.subject : '';
};
</script>

<style scoped>
.il { display: flex; flex-direction: column; gap: 22px; }
.il__group { display: flex; flex-direction: column; gap: 6px; }
.il__title { display: flex; align-items: center; gap: 10px; font-size: 15px; font-weight: 700; color: var(--surface-heading); }
.il__icon { width: 16px; color: var(--status-warning); }
.il__count { font-size: 11px; font-weight: 700; padding: 1px 8px; border-radius: var(--radius-pill); background: var(--status-warning-soft); color: var(--status-warning); }
.il__hint { font-size: var(--text-sm); color: var(--surface-muted); max-width: var(--measure); padding-left: 26px; }
.il__list { list-style: none; padding: 0 0 0 26px; margin: 4px 0 0; display: flex; flex-direction: column; }
.il__item { display: flex; flex-wrap: wrap; gap: 2px 10px; padding: 7px 0; border-top: 1px solid var(--surface-3); font-size: var(--text-sm); }
.il__item:first-child { border-top: none; }
.il__doc { color: var(--surface-heading); font-weight: 600; text-decoration: none; overflow-wrap: anywhere; }
.il__doc:hover { color: var(--interactive); text-decoration: underline; }
.il__detail { color: var(--surface-text); overflow-wrap: anywhere; }
.il__more { align-self: flex-start; margin-left: 26px; background: none; border: none; padding: 0; cursor: pointer; font-size: 13px; font-weight: 600; color: var(--interactive); }
.il__more:hover { text-decoration: underline; }
</style>
