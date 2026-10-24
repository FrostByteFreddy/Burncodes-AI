<template>
  <div class="cfg-stack">
    <!-- Basics -->
    <section class="panel">
      <h2 class="panel-title">{{ $t('configure.basics.title') }}</h2>
      <div class="cfg-fields">
        <div class="cfg-grid">
          <div>
            <label for="cfg-name" class="form-field">{{ $t('configure.basics.name') }}</label>
            <input v-model="local.name" id="cfg-name" type="text" required class="form-input" />
            <p class="field-hint">{{ $t('configure.basics.nameHint') }}</p>
          </div>
          <div>
            <label for="cfg-lang" class="form-field">{{ $t('configure.basics.language') }}</label>
            <select v-model="language" id="cfg-lang" class="form-input">
              <option v-for="l in CHATBOT_LANGUAGES" :key="l.value" :value="l.value">{{ l.text }}</option>
            </select>
            <p class="field-hint">{{ $t('configure.basics.languageHint') }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- First impression -->
    <section class="panel">
      <h2 class="panel-title">{{ $t('configure.welcome.title') }}</h2>
      <p class="panel-sub">{{ $t('configure.welcome.sub') }}</p>
      <div class="cfg-fields">
        <div>
          <label for="cfg-intro" class="form-field">{{ $t('configure.welcome.intro') }}</label>
          <AutoGrowTextarea v-model="local.intro_message" id="cfg-intro" rows="2" class="form-input" />
        </div>

        <div>
          <p class="form-field" id="cfg-starters-label">{{ $t('configure.welcome.starters') }}</p>
          <p class="field-hint field-hint--above">{{ $t('configure.welcome.startersHint') }}</p>
          <ul class="cfg-starters" aria-labelledby="cfg-starters-label">
            <li v-for="s in starters" :key="s.id" class="cfg-starter">
              <input v-model="s.label" type="text" :placeholder="$t('configure.welcome.starterPlaceholder')" class="form-input" :aria-label="$t('configure.welcome.starters')" />
              <button type="button" class="cfg-icon-btn" :aria-label="$t('configure.remove')" @click="removeStarter(s.id)">
                <font-awesome-icon :icon="['fas', 'xmark']" />
              </button>
            </li>
          </ul>
          <button type="button" class="btn-quiet cfg-add" @click="addStarter">
            <font-awesome-icon :icon="['fas', 'plus']" /> {{ $t('configure.welcome.addStarter') }}
          </button>
        </div>

        <div>
          <label for="cfg-placeholder" class="form-field">{{ $t('configure.welcome.placeholder') }}</label>
          <input v-model="local.widget_config.input_placeholder" id="cfg-placeholder" type="text" class="form-input" />
        </div>
      </div>
    </section>

    <!-- How it talks -->
    <section class="panel">
      <h2 class="panel-title">{{ $t('configure.tone.title') }}</h2>
      <p class="panel-sub">{{ $t('configure.tone.sub') }}</p>
      <div class="cfg-fields">
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
          <label for="cfg-persona" class="form-field">{{ $t('configure.tone.persona') }}</label>
          <AutoGrowTextarea v-model="local.system_persona" id="cfg-persona" rows="4" class="form-input" />
          <p class="field-hint">{{ $t('configure.tone.personaHint') }}</p>
        </div>
        <div>
          <label for="cfg-thinking" class="form-field">{{ $t('configure.tone.thinking') }}</label>
          <AutoGrowTextarea v-model="thinkingMessages" id="cfg-thinking" rows="3" class="form-input" />
          <p class="field-hint">{{ $t('configure.tone.thinkingHint') }}</p>
        </div>
      </div>
    </section>

    <!-- Advanced: the raw instruction template -->
    <details class="panel cfg-advanced">
      <summary class="cfg-advanced__summary">
        <span>
          <span class="panel-title">{{ $t('configure.advanced.title') }}</span>
          <span class="panel-sub">{{ $t('configure.advanced.sub') }}</span>
        </span>
        <font-awesome-icon :icon="['fas', 'chevron-down']" class="cfg-advanced__chevron" />
      </summary>
      <div class="cfg-fields">
        <p class="cfg-warning">
          <font-awesome-icon :icon="['fas', 'triangle-exclamation']" />
          <span>{{ $t('configure.advanced.warning', PLACEHOLDERS) }}</span>
        </p>
        <div>
          <label for="cfg-template" class="form-field">{{ $t('configure.advanced.template') }}</label>
          <AutoGrowTextarea v-model="local.rag_prompt_template" id="cfg-template" rows="6" class="form-input form-input--mono" />
          <p v-if="missingPersona" class="field-hint field-hint--warn">{{ $t('configure.advanced.missingPersona', PLACEHOLDERS) }}</p>
        </div>
        <div>
          <button type="button" class="btn-quiet" :disabled="isDefaultTemplate" @click="restoreTemplate">
            <font-awesome-icon :icon="['fas', 'rotate-left']" /> {{ $t('configure.advanced.restore') }}
          </button>
        </div>
      </div>
    </details>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { v4 as uuidv4 } from 'uuid';
import AutoGrowTextarea from '../../AutoGrowTextarea.vue';
import { CHATBOT_LANGUAGES, PROMPT_TEMPLATES, TONES } from '@/utils/chatbotDefaults';

// Shown literally in the help texts (vue-i18n would read them as parameters)
const PLACEHOLDERS = { persona: '{persona}', fine_tune_instructions: '{fine_tune_instructions}' };

const props = defineProps({ modelValue: { type: Object, required: true } });
const local = computed(() => props.modelValue);

// One language setting: what residents write in and what rules are phrased in
const language = computed({
  get: () => local.value.translation_target || local.value.doc_language || 'de',
  set: (v) => { local.value.translation_target = v; local.value.doc_language = v; },
});

const starters = computed(() => {
  if (!local.value.widget_config.conversation_starters) local.value.widget_config.conversation_starters = [];
  return local.value.widget_config.conversation_starters;
});
const addStarter = () => starters.value.push({ id: uuidv4(), label: '' });
const removeStarter = (id) => {
  local.value.widget_config.conversation_starters = starters.value.filter((s) => s.id !== id);
};

const thinkingMessages = computed({
  get: () => (local.value.widget_config.thinking_messages || []).join('\n'),
  set: (v) => { local.value.widget_config.thinking_messages = v.split('\n').map((s) => s.trim()).filter(Boolean); },
});

const activeTone = computed(() =>
  Object.keys(TONES).find((k) => Object.values(TONES[k]).includes((local.value.system_persona || '').trim())) || null
);
const applyTone = (key) => { local.value.system_persona = TONES[key][language.value] || TONES[key].en; };

const missingPersona = computed(() => !(local.value.rag_prompt_template || '').includes('{persona}'));
const isDefaultTemplate = computed(() => local.value.rag_prompt_template === (PROMPT_TEMPLATES[language.value] || PROMPT_TEMPLATES.en));
const restoreTemplate = () => { local.value.rag_prompt_template = PROMPT_TEMPLATES[language.value] || PROMPT_TEMPLATES.en; };
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

.cfg-starters { list-style: none; padding: 0; margin: 8px 0 0; display: flex; flex-direction: column; gap: 8px; }
.cfg-starters:empty { display: none; }
.cfg-starter { display: flex; gap: 8px; align-items: center; }
.cfg-add { margin-top: 10px; }

.cfg-advanced { padding: 0; }
.cfg-advanced__summary {
  display: flex; align-items: center; justify-content: space-between; gap: 16px;
  padding: 20px 24px; cursor: pointer; list-style: none;
}
.cfg-advanced__summary::-webkit-details-marker { display: none; }
.cfg-advanced__summary > span { display: flex; flex-direction: column; }
.cfg-advanced__chevron { color: var(--surface-muted); transition: transform var(--t-fast); }
.cfg-advanced[open] .cfg-advanced__chevron { transform: rotate(180deg); }
.cfg-advanced > .cfg-fields { padding: 0 24px 24px; margin-top: 0; }

.cfg-warning {
  display: grid; grid-template-columns: 16px minmax(0, 1fr); gap: 10px; align-items: baseline;
  font-size: var(--text-sm); color: var(--status-warning); max-width: var(--measure);
}

@media (max-width: 760px) {
  .cfg-tones { grid-template-columns: minmax(0, 1fr); }
}
</style>
