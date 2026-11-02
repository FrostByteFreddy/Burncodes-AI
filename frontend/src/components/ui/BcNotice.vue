<template>
  <Alert :variant="tone" :role="tone === 'error' || tone === 'warning' ? 'alert' : undefined">
    <BcIcon :name="icon || ICONS[tone]" />
    <AlertTitle v-if="heading" class="text-base font-bold">{{ heading }}</AlertTitle>
    <AlertDescription v-if="$slots.default" class="col-start-2 text-base text-foreground"><slot /></AlertDescription>
    <div v-if="$slots.actions" class="col-start-2 mt-3 flex flex-wrap gap-3"><slot name="actions" /></div>
  </Alert>
</template>

<script setup>
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { Alert, AlertDescription, AlertTitle } from './alert';
import BcIcon from './BcIcon.vue';

const ICONS = { info: 'circle-info', success: 'circle-check', warning: 'triangle-exclamation', error: 'circle-exclamation', ai: 'brain', tip: 'lightbulb' };
// tone: info · success · warning · error · ai (something the AI found) · tip ("Gut zu wissen", quiet)
const props = defineProps({ tone: { type: String, default: 'info' }, title: { type: String, default: null }, icon: { type: String, default: '' } });
const { t } = useI18n();
const heading = computed(() => props.title ?? (props.tone === 'tip' ? t('ui.goodToKnow') : ''));
</script>
