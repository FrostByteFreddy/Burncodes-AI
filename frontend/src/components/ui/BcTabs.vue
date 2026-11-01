<template>
  <Tabs v-model="model">
    <TabsList variant="line" :aria-label="label || undefined" class="h-auto! w-full justify-start gap-6 overflow-x-auto border-b p-0">
      <TabsTrigger v-for="t in tabs" :key="t.id" :value="t.id"
        class="h-11 flex-none rounded-none border-0 border-b-2 border-transparent px-0 text-base font-semibold after:hidden data-active:border-primary! data-active:text-foreground">
        {{ t.label }}<Badge v-if="t.count != null" :variant="model === t.id ? 'interactive' : 'neutral'" class="px-1.5 py-0 text-[13px]">{{ formatNumber(t.count) }}</Badge>
      </TabsTrigger>
    </TabsList>
  </Tabs>
</template>

<script setup>
import { Badge } from './badge';
import { Tabs, TabsList, TabsTrigger } from './tabs';
import { formatNumber } from '@/utils/format';

defineProps({ tabs: { type: Array, required: true }, label: { type: String, default: '' } });
const model = defineModel({ type: String, default: '' });
</script>
