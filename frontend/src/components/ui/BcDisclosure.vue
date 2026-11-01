<template>
  <Collapsible v-model:open="open" :class="['bc-disc', { 'is-open': open }]">
    <CollapsibleTrigger class="bc-disc__btn">
      <BcIcon name="chevron-right" class="bc-disc__chev" /><span>{{ title }}</span><span v-if="meta" class="bc-disc__meta">{{ meta }}</span>
    </CollapsibleTrigger>
    <CollapsibleContent class="bc-disc__body"><slot /></CollapsibleContent>
  </Collapsible>
</template>

<script setup>
import { ref } from 'vue';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './collapsible';
import BcIcon from './BcIcon.vue';

// Folds expert settings away; meta names what's inside ("Bereiche auslassen · Gründlich")
const props = defineProps({ title: { type: String, required: true }, meta: { type: String, default: '' }, defaultOpen: Boolean });
const open = ref(props.defaultOpen);
</script>
