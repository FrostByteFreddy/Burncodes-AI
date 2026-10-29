<template>
  <BcDialog :open="show" :title="title" tone="danger" icon="triangle-exclamation"
    :confirm-label="confirmButtonText || $t('modals.confirmation.confirm')" :confirm-disabled="isConfirmDisabled" :loading="loading"
    @confirm="onConfirm" @cancel="onCancel">
    <p v-html="message"></p>
    <p v-if="loading" class="cm-busy" role="status">{{ $t('modals.confirmation.deleting') }}</p>
    <div v-if="confirmationText" class="cm-type">
      <BcTextInput v-model="userInput" :label="$t('modals.confirmation.typeToConfirm', { text: confirmationText })" autocomplete="off" />
    </div>
  </BcDialog>
</template>

<script setup>
import { computed, ref } from 'vue';
import { BcDialog, BcTextInput } from './ui';

// A destructive confirmation. message may contain escaped HTML (bold names).
const props = defineProps({
  show: Boolean,
  title: { type: String, required: true },
  message: { type: String, required: true },
  confirmationText: { type: String, default: '' },
  confirmButtonText: { type: String, default: '' },
  // the action is running: the dialog stays open, with a spinner and a note, until the caller closes it
  loading: Boolean,
});
const emit = defineEmits(['confirm', 'cancel']);
const userInput = ref('');
const isConfirmDisabled = computed(() => Boolean(props.confirmationText) && userInput.value !== props.confirmationText);
const onConfirm = () => { emit('confirm'); userInput.value = ''; };
const onCancel = () => { emit('cancel'); userInput.value = ''; };
</script>

<style scoped>
.cm-type { margin-top: var(--space-4); }
.cm-busy { margin-top: var(--space-4); color: var(--text-secondary); }
</style>
