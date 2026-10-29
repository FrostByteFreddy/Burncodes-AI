<template>
  <span :class="['bc-chip', tone && `bc-chip--${tone}`]">
    <BcIcon v-if="icon" :name="icon" />
    <span :class="{ 'bc-chip__mono': mono }">{{ text }}</span>
    <button v-if="removable" type="button" class="bc-chip__x" :aria-label="`${$t('ui.remove')}: ${text}`" @click="$emit('remove')"><BcIcon name="xmark" /></button>
  </span>
</template>

<script setup>
import BcIcon from './BcIcon.vue';

// A left-out path or host; mono because it is a real path
defineProps({ text: { type: String, required: true }, removable: Boolean, mono: { type: Boolean, default: true }, icon: { type: String, default: '' }, tone: { type: String, default: '' } });
defineEmits(['remove']);
</script>
