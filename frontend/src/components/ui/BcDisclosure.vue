<template>
  <div :class="['bc-disc', { 'is-open': open }]">
    <button type="button" class="bc-disc__btn" :aria-expanded="open ? 'true' : 'false'" :aria-controls="did" @click="open = !open">
      <BcIcon name="chevron-right" class="bc-disc__chev" /><span>{{ title }}</span><span v-if="meta" class="bc-disc__meta">{{ meta }}</span>
    </button>
    <div v-if="open" :id="did" class="bc-disc__body"><slot /></div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import BcIcon from './BcIcon.vue';
import { useFieldId } from './useFieldId';

// Folds expert settings away; meta names what's inside ("Bereiche auslassen · Gründlich")
const props = defineProps({ title: { type: String, required: true }, meta: { type: String, default: '' }, defaultOpen: Boolean });
const open = ref(props.defaultOpen);
const did = useFieldId('dc');
</script>
