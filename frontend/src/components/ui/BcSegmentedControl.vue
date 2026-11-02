<template>
  <ToggleGroup type="single" :model-value="model" :spacing="1" :aria-label="label || undefined"
    class="w-fit rounded-md bg-muted p-0.5" @update:model-value="(v) => { if (v !== undefined && v !== '') model = v; }">
    <ToggleGroupItem v-for="o in options" :key="o.value" :value="o.value"
      :class="['rounded-[5px] border-0 font-semibold text-muted-foreground hover:bg-transparent hover:text-foreground data-[state=on]:bg-card data-[state=on]:text-foreground data-[state=on]:shadow-sm', size === 'sm' ? 'h-7 px-2.5 text-sm' : 'h-9 px-3 text-sm']">
      <BcIcon v-if="o.icon" :name="o.icon" />{{ o.label }}<Badge v-if="o.count" variant="neutral" class="px-1.5 py-0 text-xs">{{ o.count }}</Badge>
    </ToggleGroupItem>
  </ToggleGroup>
</template>

<script setup>
import { ToggleGroup, ToggleGroupItem } from './toggle-group';
import { Badge } from './badge';
import BcIcon from './BcIcon.vue';

defineProps({ options: { type: Array, required: true }, label: { type: String, default: '' }, size: { type: String, default: 'md' } });
const model = defineModel({ type: [String, Number], default: null });
</script>
