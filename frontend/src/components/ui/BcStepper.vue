<template>
  <nav class="bc-stepper" :aria-label="$t('ui.setup')">
    <div class="bc-stepper__compact">{{ $t('ui.stepOf', { n: current + 1, total: steps.length }) }}<strong>{{ steps[current] }}</strong></div>
    <ol class="bc-stepper__list">
      <li v-for="(s, i) in steps" :key="i" :class="['bc-stepper__item', `is-${state(i)}`]" :aria-current="i === current ? 'step' : undefined">
        <span class="bc-stepper__num" aria-hidden="true"><BcIcon v-if="i < current" name="check" /><template v-else>{{ i + 1 }}</template></span>
        <span class="bc-stepper__label">{{ s }}<span v-if="i < current" class="bc-sr"> {{ $t('ui.doneSr') }}</span></span>
      </li>
    </ol>
    <div class="bc-stepper__bar" aria-hidden="true"><span :style="{ width: `${steps.length > 1 ? (current / (steps.length - 1)) * 100 : 0}%` }"></span></div>
  </nav>
</template>

<script setup>
import BcIcon from './BcIcon.vue';

// The guided setup's progress; collapses to "Schritt 3 von 8" on narrow screens
const props = defineProps({ steps: { type: Array, required: true }, current: { type: Number, default: 0 } });
const state = (i) => (i < props.current ? 'done' : i === props.current ? 'current' : 'todo');
</script>
