<template>
  <ol class="bc-stepind" :aria-label="$t('ui.progress')">
    <li v-for="(s, i) in steps" :key="i" :class="['bc-stepind__item', `is-${state(i)}`]" :aria-current="i === current ? 'step' : undefined">
      <span class="bc-stepind__num" aria-hidden="true"><BcIcon v-if="i < current" name="check" /><template v-else>{{ i + 1 }}</template></span>
      <span class="bc-stepind__label">{{ s }}</span>
    </li>
  </ol>
</template>

<script setup>
import BcIcon from './BcIcon.vue';

const props = defineProps({ steps: { type: Array, required: true }, current: { type: Number, default: 0 } });
const state = (i) => (i < props.current ? 'done' : i === props.current ? 'current' : 'todo');
</script>
