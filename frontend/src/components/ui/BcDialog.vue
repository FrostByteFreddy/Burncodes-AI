<template>
  <AlertDialog :open="open" @update:open="(o) => { if (!o && !loading) $emit('cancel'); }">
    <AlertDialogContent class="max-w-lg! gap-4 p-6 text-base">
      <AlertDialogHeader class="flex-row items-center gap-3 place-items-center text-left">
        <span v-if="icon" :class="['grid size-10 shrink-0 place-items-center rounded-full', tone === 'danger' ? 'bg-[var(--status-error-soft)] text-destructive' : 'bg-accent text-accent-foreground']"><BcIcon :name="icon" /></span>
        <AlertDialogTitle class="text-xl font-bold">{{ title }}</AlertDialogTitle>
      </AlertDialogHeader>
      <AlertDialogDescription as="div" class="text-base text-foreground"><slot /></AlertDialogDescription>
      <AlertDialogFooter class="m-0 border-0 bg-transparent p-0">
        <BcButton v-if="cancelLabel !== false" variant="secondary" :disabled="loading" @click="$emit('cancel')">{{ cancelLabel || $t('ui.cancel') }}</BcButton>
        <BcButton v-if="confirmLabel" :variant="tone === 'danger' ? 'destructive' : 'primary'" :disabled="confirmDisabled" :loading="loading" @click="$emit('confirm')">{{ confirmLabel }}</BcButton>
      </AlertDialogFooter>
    </AlertDialogContent>
  </AlertDialog>
</template>

<script setup>
import { AlertDialog, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from './alert-dialog';
import BcButton from './BcButton.vue';
import BcIcon from './BcIcon.vue';

// The confirm button repeats the action ("Ausschalten", "Durchlauf löschen"), never "OK"
defineProps({
  open: Boolean, title: { type: String, required: true }, tone: { type: String, default: 'default' }, icon: { type: String, default: '' },
  confirmLabel: { type: String, default: '' }, cancelLabel: { type: [String, Boolean], default: '' }, confirmDisabled: Boolean, loading: Boolean,
});
defineEmits(['confirm', 'cancel']);
</script>
