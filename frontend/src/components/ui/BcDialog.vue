<template>
  <Teleport to="body">
    <div v-if="open" class="bc-overlay">
      <div class="bc-scrim" @click="!loading && $emit('cancel')"></div>
      <div class="bc-dialog" role="alertdialog" aria-modal="true" :aria-label="title">
        <div class="bc-dialog__head">
          <span v-if="icon" :class="['bc-dialog__icon', { 'is-danger': tone === 'danger' }]"><BcIcon :name="icon" /></span>
          <h2 class="bc-dialog__title">{{ title }}</h2>
        </div>
        <div class="bc-dialog__body"><slot /></div>
        <div class="bc-dialog__foot">
          <BcButton v-if="cancelLabel !== false" variant="secondary" :disabled="loading" @click="$emit('cancel')">{{ cancelLabel || $t('ui.cancel') }}</BcButton>
          <BcButton v-if="confirmLabel" :variant="tone === 'danger' ? 'destructive' : 'primary'" :disabled="confirmDisabled" :loading="loading" @click="$emit('confirm')">{{ confirmLabel }}</BcButton>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import BcButton from './BcButton.vue';
import BcIcon from './BcIcon.vue';

// The confirm button repeats the action ("Ausschalten", "Durchlauf löschen"), never "OK"
defineProps({
  open: Boolean, title: { type: String, required: true }, tone: { type: String, default: 'default' }, icon: { type: String, default: '' },
  confirmLabel: { type: String, default: '' }, cancelLabel: { type: [String, Boolean], default: '' }, confirmDisabled: Boolean, loading: Boolean,
});
defineEmits(['confirm', 'cancel']);
</script>
