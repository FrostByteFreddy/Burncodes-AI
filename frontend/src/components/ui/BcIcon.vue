<template>
  <font-awesome-icon :icon="[regular ? 'far' : 'fas', name]" class="bc-icon"
    :role="label ? 'img' : undefined" :aria-label="label || undefined" :title="label || undefined" :aria-hidden="label ? undefined : 'true'" />
</template>

<script setup>
// A Font Awesome 6 icon at text size; decorative unless it has a label.
defineProps({ name: { type: String, required: true }, label: { type: String, default: '' }, regular: Boolean });
</script>
