<template>
  <div :class="['bc-log', `bc-log--${state}`]">
    <span class="bc-log__mark" aria-hidden="true">
      <span v-if="state === 'running'" class="bc-spinner bc-spinner--sm"></span>
      <BcIcon v-else :name="ICONS[state] || 'check'" />
    </span>
    <div class="bc-log__body">
      <div class="bc-log__title">{{ title }}<span v-if="tag" class="bc-log__tag">{{ tag }}</span></div>
      <div v-if="path" class="bc-log__path">{{ path }}</div>
      <div v-if="meta" class="bc-log__meta">{{ meta }}</div>
    </div>
    <time v-if="time" class="bc-log__time">{{ time }}</time>
  </div>
</template>

<script setup>
import BcIcon from './BcIcon.vue';

const ICONS = { done: 'check', failed: 'xmark', info: 'circle-info', learned: 'check', skipped: 'minus' };
// state: running · done · learned · failed · info · skipped. path shows which page when titles repeat.
defineProps({
  state: { type: String, default: 'done' },
  title: { type: String, required: true },
  path: { type: String, default: '' },
  tag: { type: String, default: '' },
  meta: { type: String, default: '' },
  time: { type: String, default: '' },
});
</script>
