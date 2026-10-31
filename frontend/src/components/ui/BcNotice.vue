<template>
  <div :class="['bc-notice', `bc-notice--${tone}`]" :role="tone === 'error' || tone === 'warning' ? 'alert' : undefined">
    <BcIcon :name="icon || ICONS[tone]" class="bc-notice__icon" />
    <div class="bc-notice__body">
      <div v-if="heading" class="bc-notice__title">{{ heading }}</div>
      <div v-if="$slots.default" class="bc-notice__text"><slot /></div>
      <div v-if="$slots.actions" class="bc-notice__actions"><slot name="actions" /></div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import BcIcon from './BcIcon.vue';

const ICONS = { info: 'circle-info', success: 'circle-check', warning: 'triangle-exclamation', error: 'circle-exclamation', ai: 'brain', tip: 'lightbulb' };
// tone: info · success · warning · error · ai (something the AI found) · tip ("Gut zu wissen", quiet)
const props = defineProps({ tone: { type: String, default: 'info' }, title: { type: String, default: null }, icon: { type: String, default: '' } });
const { t } = useI18n();
const heading = computed(() => props.title ?? (props.tone === 'tip' ? t('ui.goodToKnow') : ''));
</script>
