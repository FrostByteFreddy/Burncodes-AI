<template>
  <div class="bc-unsaved" role="region" :aria-label="text || $t('ui.unsaved')">
    <BcIcon name="circle-dot" class="bc-unsaved__icon" />
    <span class="bc-unsaved__text">{{ text || $t('ui.unsaved') }}</span>
    <div class="bc-unsaved__actions">
      <BcButton variant="quiet" :disabled="saving" @click="$emit('discard')">{{ $t('ui.discard') }}</BcButton>
      <BcButton variant="primary" type="submit" :loading="saving" @click="$emit('save')">{{ $t('ui.save') }}</BcButton>
    </div>
  </div>
</template>

<script setup>
import BcButton from './BcButton.vue';
import BcIcon from './BcIcon.vue';

defineProps({ text: { type: String, default: '' }, saving: Boolean });
defineEmits(['discard', 'save']);
</script>
