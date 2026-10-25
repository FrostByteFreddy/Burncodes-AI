<template>
  <ol v-if="rows.length" ref="listEl" class="alog" :style="{ maxHeight }" aria-live="polite">
    <li v-for="row in rows" :key="row.id" class="alog__row" :class="`alog__row--${row.state}`">
      <span class="alog__icon" aria-hidden="true">
        <font-awesome-icon v-if="row.state === 'running'" :icon="['fas', 'spinner']" class="animate-spin" />
        <font-awesome-icon v-else-if="row.state === 'failed'" :icon="['fas', 'triangle-exclamation']" />
        <font-awesome-icon v-else-if="row.state === 'done'" :icon="['fas', 'check']" />
        <span v-else class="alog__dot"></span>
      </span>
      <span class="alog__text">{{ row.text }}</span>
      <time class="alog__time" :datetime="row.created_at">{{ fmtTime(row.created_at) }}</time>
    </li>
  </ol>
  <p v-else class="alog__empty">{{ $t('knowledge.log.empty') }}</p>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue';
import { useCrawlText } from '@/composables/useCrawl';

const props = defineProps({
  entries: { type: Array, default: () => [] },
  maxHeight: { type: String, default: '420px' },
});
const { foldLog, fmtTime } = useCrawlText();
const listEl = ref(null);

const rows = computed(() => foldLog(props.entries));

// Keep the newest row in view while the user hasn't scrolled up
watch(() => rows.value.length, async () => {
  const el = listEl.value;
  if (!el) return;
  const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
  await nextTick();
  if (atBottom) el.scrollTop = el.scrollHeight;
});
</script>

<style scoped>
.alog {
  list-style: none; margin: 0; padding: 6px 0;
  overflow-y: auto;
  display: flex; flex-direction: column;
}
.alog__row {
  display: grid; grid-template-columns: 20px minmax(0, 1fr) auto; align-items: baseline; gap: 10px;
  padding: 7px 4px; border-top: 1px solid var(--surface-3);
  font-size: var(--text-sm); color: var(--surface-text);
}
.alog__row:first-child { border-top: none; }
.alog__icon { display: flex; justify-content: center; font-size: 12px; color: var(--surface-muted); }
.alog__dot { width: 5px; height: 5px; margin-top: 7px; border-radius: 50%; background: var(--surface-muted); }
.alog__row--running .alog__icon { color: var(--ai); }
.alog__row--done .alog__icon { color: var(--status-success); }
.alog__row--failed .alog__icon, .alog__row--failed .alog__text { color: var(--status-warning); }
.alog__text { min-width: 0; overflow-wrap: anywhere; line-height: 1.45; }
.alog__time { font-size: var(--text-xs); color: var(--surface-muted); }
.alog__empty { font-size: var(--text-sm); color: var(--surface-muted); }
</style>
