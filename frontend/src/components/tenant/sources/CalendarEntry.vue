<template>
  <div class="ce">
    <p class="ce__head">
      <span class="ce__name">{{ event.zone ? `${event.series} (${event.zone})` : event.series }}</span>
      <Badge v-if="event.is_exception" variant="outline" class="ce__moved">{{ $t('knowledge.overview.moved') }}</Badge>
    </p>
    <p class="ce__time">{{ time || $t('knowledge.month.allDay') }}</p>
    <p v-if="event.notes" class="ce__notes">{{ event.notes }}</p>
    <a v-if="event.source" :href="event.source.url" target="_blank" rel="noopener noreferrer" class="ce__source">
      {{ $t('knowledge.month.source', { page: event.source.title }) }}
      <BcIcon name="arrow-up-right-from-square" />
    </a>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { Badge } from '@/components/ui/badge';
import { BcIcon } from '@/components/ui';

// One date with what a person needs to check it: when, and the page it was read from
const props = defineProps({ event: { type: Object, required: true } });
const time = computed(() => {
  const { start_time: start, end_time: end } = props.event;
  if (!start) return '';
  return end ? `${start.slice(0, 5)} – ${end.slice(0, 5)}` : start.slice(0, 5);
});
</script>

<style scoped>
.ce { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.ce__head { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin: 0; }
.ce__name { font-weight: 700; color: var(--surface-heading); overflow-wrap: anywhere; }
.ce__moved { color: var(--status-warning); border-color: currentColor; }
.ce__time { margin: 0; font-variant-numeric: tabular-nums; color: var(--surface-heading); }
.ce__notes { margin: 0; font-size: var(--text-sm); color: var(--surface-text); }
.ce__source { font-size: var(--text-sm); font-weight: 600; color: var(--interactive); text-decoration: none; overflow-wrap: anywhere; }
.ce__source:hover { text-decoration: underline; }
.ce__source :deep(svg) { margin-left: 4px; font-size: 12px; }
</style>
