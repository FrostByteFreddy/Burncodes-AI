<script setup lang="ts">
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';

defineProps<{ items: string[][] }>();
</script>

<template>
  <!-- Closed answers stay in the HTML, so search engines can read them -->
  <Accordion type="single" collapsible :unmount-on-hide="false">
    <AccordionItem v-for="[q, a] in items" :key="q" :value="q">
      <AccordionTrigger class="text-left text-base font-bold">{{ q }}</AccordionTrigger>
      <AccordionContent class="text-base text-muted-foreground">{{ a }}</AccordionContent>
    </AccordionItem>
  </Accordion>
</template>
