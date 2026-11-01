<template>
  <Field :data-invalid="error ? 'true' : undefined">
    <FieldLabel :for="htmlFor || undefined">{{ label }}<span v-if="optional" class="font-normal text-muted-foreground"> {{ $t('ui.optional') }}</span></FieldLabel>
    <slot />
    <FieldError v-if="error" :id="htmlFor ? `${htmlFor}-err` : undefined">{{ error }}</FieldError>
    <FieldDescription v-else-if="hint" :id="htmlFor ? `${htmlFor}-hint` : undefined">{{ hint }}</FieldDescription>
  </Field>
</template>

<script setup>
import { Field, FieldDescription, FieldError, FieldLabel } from './field';

// One short hint line at most; an error says how to fix it.
defineProps({ label: { type: String, required: true }, htmlFor: { type: String, default: '' }, hint: { type: String, default: '' }, error: { type: String, default: '' }, optional: Boolean });
</script>
