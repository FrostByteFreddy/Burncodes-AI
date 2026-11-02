<script setup lang="ts">
import { computed, ref } from 'vue';
import { Slider } from '@/components/ui/slider';

const props = defineProps<{ title: string; label: string; result: string; note: string; rappen: number; locale: string }>();
const questions = ref([500]);
const fmt = (n: number) => n.toLocaleString(props.locale === 'de-CH' ? 'de-CH' : props.locale);
const cost = computed(() => Math.round((questions.value[0] * props.rappen) / 100));
</script>

<template>
  <div>
    <h2 class="h2">{{ title }}</h2>
    <div class="mt-6 rounded-2xl border bg-card p-6">
      <div class="flex items-baseline justify-between gap-4">
        <p id="calc-label" class="font-semibold">{{ label }}</p>
        <p class="text-2xl font-bold tabular-nums">{{ fmt(questions[0]) }}</p>
      </div>
      <Slider v-model="questions" :min="50" :max="5000" :step="50" class="mt-4" aria-labelledby="calc-label" />
      <p class="mt-6 text-5xl font-bold tabular-nums text-primary">CHF {{ fmt(cost) }}</p>
      <p class="mt-1 text-muted-foreground">{{ result }}</p>
      <p class="mt-4 text-sm text-muted-foreground">{{ note }}</p>
    </div>
  </div>
</template>
