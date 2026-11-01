<template>
  <Accordion type="multiple" :default-value="['personality']" :unmount-on-hide="false" class="cfg-stack">
    <!-- Look: palette and font; the click-to-edit preview covers the rest -->
    <AccordionItem value="look" class="rounded-lg border bg-card">
      <AccordionTrigger class="items-center px-6 py-5 text-left hover:no-underline">
        <span class="flex flex-col font-normal">
          <span class="panel-title">{{ $t('configure.look.title') }}</span>
          <span class="panel-sub">{{ $t('configure.look.sub') }}</span>
        </span>
      </AccordionTrigger>
      <AccordionContent class="px-6 pb-6 text-base">
      <div class="cfg-fields mt-0!">
        <PaletteEditor :config="local.widget_config" />
        <FontPicker :config="local.widget_config" />
      </div>
    </AccordionContent>
    </AccordionItem>

    <!-- Personality: name, tone and the texts shown while it thinks -->
    <AccordionItem value="personality" class="rounded-lg border bg-card">
      <AccordionTrigger class="items-center px-6 py-5 text-left hover:no-underline">
        <span class="flex flex-col font-normal">
          <span class="panel-title">{{ $t('configure.personality.title') }}</span>
          <span class="panel-sub">{{ $t('configure.tone.sub') }}</span>
        </span>
      </AccordionTrigger>
      <AccordionContent class="px-6 pb-6 text-base">
      <div class="cfg-fields mt-0!">
        <div>
          <Label for="cfg-name" class="mb-2">{{ $t('configure.basics.name') }}</Label>
          <Input v-model="local.name" id="cfg-name" type="text" required  />
          <p class="field-hint">{{ $t('configure.basics.nameHint') }}</p>
        </div>
        <div class="cfg-tones" role="group" :aria-label="$t('configure.tone.presets')">
          <button
            v-for="key in Object.keys(TONES)"
            :key="key"
            type="button"
            class="cfg-tone"
            :class="{ 'cfg-tone--active': activeTone === key }"
            :aria-pressed="activeTone === key"
            @click="applyTone(key)"
          >
            <span class="cfg-tone__name">{{ $t(`configure.tone.${key}`) }}</span>
            <span class="cfg-tone__desc">{{ $t(`configure.tone.${key}Desc`) }}</span>
          </button>
        </div>
        <div>
          <Label for="cfg-persona" class="mb-2">{{ $t('configure.tone.persona') }}</Label>
          <AutoGrowTextarea v-model="local.system_persona" id="cfg-persona" rows="4" />
          <p class="field-hint">{{ $t('configure.tone.personaHint') }}</p>
        </div>
        <div>
          <Label for="cfg-thinking" class="mb-2">{{ $t('configure.tone.thinking') }}</Label>
          <AutoGrowTextarea v-model="thinkingMessages" id="cfg-thinking" rows="3" />
          <p class="field-hint">{{ $t('configure.tone.thinkingHint') }}</p>
        </div>
      </div>
    </AccordionContent>
    </AccordionItem>

    <!-- Advanced: the raw instruction template -->
    <AccordionItem value="advanced" class="rounded-lg border bg-card">
      <AccordionTrigger class="items-center px-6 py-5 text-left hover:no-underline">
        <span class="flex flex-col font-normal">
          <span class="panel-title">{{ $t('configure.advanced.title') }}</span>
          <span class="panel-sub">{{ $t('configure.advanced.sub') }}</span>
        </span>
      </AccordionTrigger>
      <AccordionContent class="px-6 pb-6 text-base">
      <div class="cfg-fields mt-0!">
        <p class="cfg-warning">
          <font-awesome-icon :icon="['fas', 'triangle-exclamation']" />
          <span>{{ $t('configure.advanced.warning', PLACEHOLDERS) }}</span>
        </p>
        <div>
          <Label for="cfg-template" class="mb-2">{{ $t('configure.advanced.template') }}</Label>
          <AutoGrowTextarea v-model="local.rag_prompt_template" id="cfg-template" rows="6" class="font-mono text-sm" />
          <p v-if="missingPersona" class="field-hint field-hint--warn">{{ $t('configure.advanced.missingPersona', PLACEHOLDERS) }}</p>
        </div>
        <div>
          <BcButton variant="secondary" type="button"  :disabled="isDefaultTemplate" @click="restoreTemplate">
            <font-awesome-icon :icon="['fas', 'rotate-left']" /> {{ $t('configure.advanced.restore') }}
          </BcButton>
        </div>
      </div>
    </AccordionContent>
    </AccordionItem>
  </Accordion>
</template>

<script setup>
import { BcButton } from '@/components/ui';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { computed } from 'vue';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import AutoGrowTextarea from '../../AutoGrowTextarea.vue';
import PaletteEditor from './PaletteEditor.vue';
import FontPicker from './FontPicker.vue';
import { PROMPT_TEMPLATE, TONES } from '@/utils/chatbotDefaults';

// Shown literally in the help texts (vue-i18n would read them as parameters)
const PLACEHOLDERS = { persona: '{persona}', fine_tune_instructions: '{fine_tune_instructions}' };

const props = defineProps({ modelValue: { type: Object, required: true } });
const local = computed(() => props.modelValue);

const thinkingMessages = computed({
  get: () => (local.value.widget_config.thinking_messages || []).join('\n'),
  set: (v) => { local.value.widget_config.thinking_messages = v.split('\n').map((s) => s.trim()).filter(Boolean); },
});

const activeTone = computed(() =>
  Object.keys(TONES).find((k) => TONES[k] === (local.value.system_persona || '').trim()) || null
);
const applyTone = (key) => { local.value.system_persona = TONES[key]; };

const missingPersona = computed(() => !(local.value.rag_prompt_template || '').includes('{persona}'));
const isDefaultTemplate = computed(() => local.value.rag_prompt_template === PROMPT_TEMPLATE);
const restoreTemplate = () => { local.value.rag_prompt_template = PROMPT_TEMPLATE; };
</script>

<style scoped>
.cfg-tones { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.cfg-tone {
  display: flex; flex-direction: column; gap: 4px; text-align: left;
  padding: 12px 14px; border-radius: var(--radius-md);
  background: var(--surface-2); border: 1px solid var(--surface-3);
  color: var(--surface-text); cursor: pointer; font: inherit;
  transition: border-color var(--t-fast);
}
.cfg-tone:hover { border-color: var(--surface-muted); }
.cfg-tone--active { border-color: var(--interactive); background: var(--interactive-soft); }
.cfg-tone__name { font-size: 15px; font-weight: 700; color: var(--surface-heading); }
.cfg-tone__desc { font-size: var(--text-sm); color: var(--surface-muted); line-height: 1.4; }


.cfg-warning {
  display: grid; grid-template-columns: 16px minmax(0, 1fr); gap: 10px; align-items: baseline;
  font-size: var(--text-sm); color: var(--status-warning); max-width: var(--measure);
}

@media (max-width: 760px) {
  .cfg-tones { grid-template-columns: minmax(0, 1fr); }
}
</style>
