<template>
  <section>
    <h3 class="cfg-subhead">{{ $t('configure.font.title') }}</h3>
    <p class="field-hint">{{ $t('configure.font.sub') }}</p>
    <div class="fnt" role="radiogroup" :aria-label="$t('configure.font.title')">
      <button
        v-for="(font, key) in CHAT_FONTS"
        :key="key"
        type="button"
        role="radio"
        class="fnt__opt"
        :class="{ 'fnt__opt--on': current === key }"
        :aria-checked="current === key"
        :style="{ fontFamily: stacks[key] }"
        @click="config.font_family = key"
      >
        <span class="fnt__sample" aria-hidden="true">Aa</span>
        <span class="fnt__name">{{ font.name || $t('configure.font.system') }}</span>
        <span v-if="key === DEFAULT_FONT" class="fnt__note">{{ $t('configure.font.readable') }}</span>
      </button>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue';
import { CHAT_FONTS, DEFAULT_FONT, loadChatFont } from '@/utils/chatFonts';

const props = defineProps({ config: { type: Object, required: true } });
const current = computed(() => (CHAT_FONTS[props.config.font_family] ? props.config.font_family : DEFAULT_FONT));

// Every option shows itself in its own font
const stacks = Object.fromEntries(Object.keys(CHAT_FONTS).map((key) => [key, loadChatFont(key)]));
</script>

<style scoped>
.cfg-subhead { font-size: 15px; font-weight: 700; color: var(--surface-heading); }
.fnt { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 10px; margin-top: 16px; }
.fnt__opt {
  display: flex; flex-direction: column; align-items: flex-start; gap: 2px; text-align: left;
  padding: 12px 14px; border-radius: var(--radius-md); cursor: pointer;
  background: var(--surface-2); border: 1px solid var(--surface-3); color: var(--surface-text);
  transition: border-color var(--t-fast);
}
.fnt__opt:hover { border-color: var(--surface-muted); }
.fnt__opt:focus-visible { box-shadow: var(--focus-ring-shadow); }
.fnt__opt--on { border-color: var(--interactive); background: var(--interactive-soft); }
.fnt__sample { font-size: 26px; line-height: 1.2; font-weight: 600; color: var(--surface-heading); }
.fnt__name { font-size: 15px; }
.fnt__note { font-family: var(--font-sans); font-size: var(--text-xs); color: var(--surface-muted); }
</style>
