<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue';
import { CalendarPlus, ExternalLink } from '@lucide/vue';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface Item { q: string; a: string; source: string; calendar?: string }
interface Tab { key: string; label: string; title: string; items: Item[] }
const props = defineProps<{ tabs: Tab[]; label: string; pick: string; calendar: string }>();

const tabKey = ref(props.tabs[0].key);
const index = ref(0);
const thinking = ref(false);
const tab = computed(() => props.tabs.find((t) => t.key === tabKey.value) ?? props.tabs[0]);
const item = computed(() => tab.value.items[index.value]);

// A short pause, so a click reads like asking the question
let timer: ReturnType<typeof setTimeout> | undefined;
function ask(i: number) {
  index.value = i;
  thinking.value = true;
  clearTimeout(timer);
  timer = setTimeout(() => { thinking.value = false; }, 550);
}
function onTab(key: string | number) {
  tabKey.value = String(key);
  ask(0);
}
onBeforeUnmount(() => clearTimeout(timer));
</script>

<template>
  <figure class="overflow-hidden rounded-3xl bg-card text-card-foreground shadow-[0_24px_60px_rgba(7,22,133,0.32)]">
    <div class="flex items-center justify-between gap-3 border-b p-3">
      <Tabs :model-value="tabKey" @update:model-value="onTab">
        <TabsList>
          <TabsTrigger v-for="t in tabs" :key="t.key" :value="t.key">{{ t.label }}</TabsTrigger>
        </TabsList>
      </Tabs>
      <Badge variant="secondary" class="shrink-0">{{ label }}</Badge>
    </div>
    <figcaption class="px-5 pt-4 font-bold">{{ tab.title }}</figcaption>
    <div class="flex min-h-64 flex-col gap-3 p-5" aria-live="polite">
      <p class="max-w-[85%] self-end rounded-2xl bg-primary px-4 py-2.5 text-primary-foreground">{{ item.q }}</p>
      <div v-if="thinking" class="flex gap-1 self-start rounded-2xl bg-muted px-4 py-4" aria-hidden="true">
        <span v-for="n in 3" :key="n" class="size-2 animate-pulse rounded-full bg-muted-foreground" :style="{ animationDelay: `${n * 120}ms` }" />
      </div>
      <div v-else class="self-start rounded-2xl bg-muted px-4 py-3 animate-in fade-in slide-in-from-bottom-1">
        <p v-html="item.a" />
        <p class="mt-2 inline-flex items-center gap-1 font-semibold text-primary"><ExternalLink class="size-4" aria-hidden="true" />{{ item.source }}</p>
        <p v-if="item.calendar" class="mt-2 flex items-center gap-1.5 border-t border-border pt-2 text-sm font-semibold"><CalendarPlus class="size-4" aria-hidden="true" />{{ calendar }}: {{ item.calendar }}</p>
      </div>
    </div>
    <div class="border-t bg-background/60 p-4">
      <p class="mb-2 text-sm text-muted-foreground">{{ pick }}</p>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="(it, i) in tab.items" :key="it.q" type="button"
          class="cursor-pointer rounded-full border bg-card px-3 py-1.5 text-left text-sm transition-colors hover:border-primary hover:text-primary aria-pressed:border-primary aria-pressed:bg-accent aria-pressed:text-accent-foreground"
          :aria-pressed="i === index" @click="ask(i)"
        >{{ it.q }}</button>
      </div>
    </div>
  </figure>
</template>
