<template>
  <Badge :variant="meta.tone" :class="{ 'text-xs': size === 'sm' }">
    <span :class="['bc-dot', { 'bc-dot--pulse': meta.pulse }]" aria-hidden="true"></span>
    {{ label || $t(`ui.status.${known ? status : 'off'}`) }}
  </Badge>
</template>

<script setup>
import { computed } from 'vue';
import { Badge } from './badge';

// Crawl states (scanning … stopped), chatbot states (on, off, hidden) and review states (warn, error)
const STATUS = {
  scanning: { tone: 'interactive', pulse: true },
  preparing: { tone: 'neutral', pulse: true },
  ready: { tone: 'interactive' },
  learning: { tone: 'ai', pulse: true },
  done: { tone: 'ok' },
  stopped: { tone: 'neutral' },
  on: { tone: 'ok' },
  off: { tone: 'neutral' },
  hidden: { tone: 'warn' },
  warn: { tone: 'warn' },
  error: { tone: 'error' },
};
const props = defineProps({ status: { type: String, required: true }, label: { type: String, default: '' }, size: { type: String, default: 'md' } });
const known = computed(() => props.status in STATUS);
const meta = computed(() => STATUS[props.status] || STATUS.off);
</script>
