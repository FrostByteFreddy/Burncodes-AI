<script setup lang="ts">
import { Menu } from '@lucide/vue';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';

defineProps<{
  links: { href: string; label: string }[];
  languages: { code: string; href: string; current: boolean }[];
  start: string;
  startHref: string;
  menu: string;
  language: string;
}>();
</script>

<template>
  <Sheet>
    <SheetTrigger as-child>
      <Button variant="ghost" size="icon" class="lg:hidden" :aria-label="menu"><Menu /></Button>
    </SheetTrigger>
    <SheetContent side="right" class="w-[min(20rem,85vw)]">
      <SheetHeader><SheetTitle>{{ menu }}</SheetTitle></SheetHeader>
      <nav class="flex flex-col gap-1 px-4" :aria-label="menu">
        <a v-for="l in links" :key="l.href" :href="l.href" class="rounded-md px-3 py-2.5 font-semibold hover:bg-accent hover:text-accent-foreground">{{ l.label }}</a>
      </nav>
      <div class="flex flex-col gap-4 p-4">
        <Button as="a" :href="startHref">{{ start }}</Button>
        <ul class="flex gap-1" :aria-label="language">
          <li v-for="l in languages" :key="l.code">
            <a :href="l.href" :lang="l.code" :aria-current="l.current ? 'true' : undefined" class="block rounded px-3 py-2 uppercase" :class="l.current ? 'font-bold' : 'text-muted-foreground'">{{ l.code }}</a>
          </li>
        </ul>
      </div>
    </SheetContent>
  </Sheet>
</template>
