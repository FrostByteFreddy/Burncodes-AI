<template>
  <div class="cfg-stack">
    <!-- Colours -->
    <section class="panel">
      <h2 class="panel-title">{{ $t('configure.colors.title') }}</h2>
      <p class="panel-sub">{{ $t('configure.colors.sub') }}</p>

      <ul class="cfg-palette">
        <li v-for="c in cfg.color_palette" :key="c.id" class="cfg-color">
          <label class="cfg-color__swatch" :style="{ backgroundColor: c.value }">
            <input v-model="c.value" type="color" class="cfg-color__input" :aria-label="nameOf(c)" />
          </label>
          <div class="cfg-color__text">
            <input v-if="!isBase(c)" v-model="c.name" type="text" class="cfg-color__name-input" :aria-label="$t('configure.colors.name')" />
            <span v-else class="cfg-color__name">{{ nameOf(c) }}</span>
            <span class="cfg-color__hex">{{ c.value.toUpperCase() }}</span>
          </div>
          <button v-if="!isBase(c)" type="button" class="cfg-icon-btn" :aria-label="$t('configure.remove')" @click="removeColor(c.id)">
            <font-awesome-icon :icon="['fas', 'xmark']" />
          </button>
        </li>
        <li>
          <button type="button" class="btn-quiet" @click="addColor">
            <font-awesome-icon :icon="['fas', 'plus']" /> {{ $t('configure.colors.add') }}
          </button>
        </li>
      </ul>

      <!-- Readability check -->
      <p v-if="!hardToRead.length" class="cfg-check cfg-check--ok">
        <font-awesome-icon :icon="['fas', 'check']" /> {{ $t('configure.colors.allReadable') }}
      </p>
      <div v-else class="cfg-check cfg-check--warn">
        <font-awesome-icon :icon="['fas', 'triangle-exclamation']" />
        <div>
          <p>{{ $t('configure.colors.hardToRead') }}</p>
          <ul><li v-for="p in hardToRead" :key="p">{{ p }}</li></ul>
        </div>
      </div>

      <details class="cfg-usage">
        <summary>
          <font-awesome-icon :icon="['fas', 'chevron-right']" class="cfg-usage__chevron" />
          {{ $t('configure.colors.usage') }}
        </summary>
        <div v-for="group in USAGE" :key="group.key" class="cfg-usage__group">
          <h3 class="cfg-usage__title">{{ $t(`configure.colors.groups.${group.key}`) }}</h3>
          <div class="cfg-grid">
            <div v-for="f in group.fields" :key="f">
              <p :id="`sw-${f}`" class="form-field">{{ $t(`configure.colors.labels.${f}`) }}</p>
              <SwatchPicker :model-value="getStyle(f)" :palette="cfg.color_palette" :label-id="`sw-${f}`" @update:model-value="setStyle(f, $event)" />
            </div>
          </div>
        </div>
      </details>
    </section>

    <!-- Chat window header -->
    <section class="panel">
      <h2 class="panel-title">{{ $t('configure.header.title') }}</h2>
      <div class="cfg-fields">
        <div>
          <label for="cfg-title" class="form-field">{{ $t('configure.header.chatTitle') }}</label>
          <input v-model="cfg.chatbot_title" id="cfg-title" type="text" class="form-input" />
          <p class="field-hint">{{ $t('configure.header.chatTitleHint') }}</p>
        </div>
        <ImageField field="logo" :label="$t('configure.header.logo')" :hint="$t('configure.header.logoHint')" v-model="cfg.logo" />
        <label class="cfg-toggle">
          <input v-model="cfg.show_reset_button" type="checkbox" />
          <span>{{ $t('configure.header.reset') }}</span>
        </label>
        <label class="cfg-toggle">
          <input v-model="cfg.show_share_button" type="checkbox" />
          <span>{{ $t('configure.header.share') }}</span>
        </label>
      </div>
    </section>

    <!-- Launcher button -->
    <section class="panel">
      <h2 class="panel-title">{{ $t('configure.launcher.title') }}</h2>
      <p class="panel-sub">{{ $t('configure.launcher.sub') }}</p>
      <div class="cfg-fields">
        <label class="cfg-toggle">
          <input v-model="widgetEnabled" type="checkbox" />
          <span>{{ $t('configure.launcher.enabled') }}</span>
        </label>
        <p v-if="!widgetEnabled" class="field-hint field-hint--warn">{{ $t('configure.launcher.disabledHint') }}</p>

        <div class="cfg-launcher" :class="{ 'cfg-launcher--off': !widgetEnabled }">
          <div class="cfg-fields cfg-fields--tight">
            <div>
              <p id="sw-launcher" class="form-field">{{ $t('configure.launcher.color') }}</p>
              <SwatchPicker :model-value="getStyle('launcher_background_color')" :palette="cfg.color_palette" label-id="sw-launcher" @update:model-value="setStyle('launcher_background_color', $event)" />
            </div>
            <ImageField field="launcher_icon" :label="$t('configure.launcher.icon')" :hint="$t('configure.launcher.iconHint')" v-model="cfg.launcher_icon" />
          </div>
          <LauncherPreview :icon="cfg.launcher_icon" :background-color="colorOf(getStyle('launcher_background_color'))" />
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { v4 as uuidv4 } from 'uuid';
import LauncherPreview from '../LauncherPreview.vue';
import SwatchPicker from './SwatchPicker.vue';
import ImageField from './ImageField.vue';
import { BASE_COLOR_IDS, contrast, usePaletteNames, getStyle as getStyleOf, setStyle as setStyleOf, colorOf as colorOfIn } from './palette';

const props = defineProps({ modelValue: { type: Object, required: true } });
const { t } = useI18n();
const { nameOf } = usePaletteNames();
const cfg = computed(() => props.modelValue.widget_config);

const isBase = (c) => BASE_COLOR_IDS.includes(c.id);
const colorOf = (id) => colorOfIn(cfg.value, id);
const getStyle = (f) => getStyleOf(cfg.value, f);
const setStyle = (f, id) => setStyleOf(cfg.value, f, id);

const USAGE = [
  { key: 'header', fields: ['header_background_color', 'header_text_color', 'reset_button_color', 'reset_button_icon_color', 'close_button_background_color', 'close_button_icon_color', 'share_button_color', 'share_button_icon_color'] },
  { key: 'messages', fields: ['chat_background_color', 'bot_message_background_color', 'bot_message_text_color', 'user_message_background_color', 'user_message_text_color'] },
  { key: 'input', fields: ['input_background_color', 'input_text_color', 'input_focus_ring_color', 'send_button_background_color', 'send_button_text_color'] },
  { key: 'starters', fields: ['starter_background_color', 'starter_text_color'] },
];

// Text/background pairs residents have to read; WCAG AA asks for 4.5:1
const PAIRS = [
  ['header', 'header_text_color', 'header_background_color'],
  ['botMessage', 'bot_message_text_color', 'bot_message_background_color'],
  ['userMessage', 'user_message_text_color', 'user_message_background_color'],
  ['input', 'input_text_color', 'input_background_color'],
  ['sendButton', 'send_button_text_color', 'send_button_background_color'],
  ['starters', 'starter_text_color', 'starter_background_color'],
];
const hardToRead = computed(() =>
  PAIRS.filter(([, fg, bg]) => getStyle(fg) && getStyle(bg) && contrast(colorOf(getStyle(fg)), colorOf(getStyle(bg))) < 4.5)
    .map(([key]) => t(`configure.colors.pairs.${key}`))
);

const addColor = () => cfg.value.color_palette.push({ id: uuidv4(), name: t('configure.colors.newColor'), value: '#5F6DFF' });
const removeColor = (id) => {
  // Anything that used the removed colour falls back to the main colour
  for (const f of USAGE.flatMap((g) => g.fields).concat('launcher_background_color')) {
    if (getStyle(f) === id) setStyle(f, 'c_primary');
  }
  cfg.value.color_palette = cfg.value.color_palette.filter((c) => c.id !== id);
};

const widgetEnabled = computed({
  get: () => cfg.value.widget_enabled !== false,
  set: (v) => { cfg.value.widget_enabled = v; },
});
</script>

<style scoped>
.cfg-palette { list-style: none; padding: 0; margin: 18px 0 0; display: flex; flex-wrap: wrap; gap: 12px; align-items: center; }
.cfg-color {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 10px 8px 8px; border-radius: var(--radius-md);
  background: var(--surface-2); border: 1px solid var(--surface-3);
}
.cfg-color__swatch {
  position: relative; width: 40px; height: 40px; border-radius: var(--radius-sm); cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.18);
}
.cfg-color__swatch:focus-within { box-shadow: var(--focus-ring); }
.cfg-color__input { position: absolute; inset: 0; opacity: 0; width: 100%; height: 100%; cursor: pointer; }
.cfg-color__text { display: flex; flex-direction: column; min-width: 0; }
.cfg-color__name { font-size: var(--text-sm); font-weight: 700; color: var(--surface-heading); }
.cfg-color__name-input {
  width: 120px; padding: 0; background: none; border: none; border-bottom: 1px dashed var(--surface-muted);
  font: inherit; font-size: var(--text-sm); font-weight: 700; color: var(--surface-heading); outline: none;
}
.cfg-color__hex { font-size: var(--text-xs); color: var(--surface-muted); }

.cfg-check { display: flex; gap: 10px; align-items: baseline; margin-top: 18px; font-size: var(--text-sm); }
.cfg-check--ok { color: var(--status-success); }
.cfg-check--warn { color: var(--status-warning); }
.cfg-check--warn ul { margin: 4px 0 0; padding-left: 18px; color: var(--surface-text); }

.cfg-usage { margin-top: 18px; border-top: 1px solid var(--surface-3); padding-top: 14px; }
.cfg-usage summary {
  display: inline-flex; align-items: center; gap: 8px; cursor: pointer; list-style: none;
  font-size: 15px; font-weight: 600; color: var(--interactive);
}
.cfg-usage summary::-webkit-details-marker { display: none; }
.cfg-usage__chevron { font-size: 11px; transition: transform var(--t-fast); }
.cfg-usage[open] .cfg-usage__chevron { transform: rotate(90deg); }
.cfg-usage__group { margin-top: 20px; }
.cfg-usage__title { font-size: 15px; font-weight: 700; color: var(--surface-heading); margin-bottom: 12px; }

.cfg-toggle { display: inline-flex; align-items: center; gap: 12px; cursor: pointer; font-size: 15px; color: var(--surface-text); }
/* Switch drawn from the native checkbox, so keyboard and screen readers work as usual */
.cfg-toggle input {
  appearance: none; flex-shrink: 0; position: relative; cursor: pointer;
  width: 40px; height: 22px; border-radius: var(--radius-pill);
  background: var(--surface-3); transition: background var(--t-fast);
}
.cfg-toggle input::after {
  content: ''; position: absolute; top: 3px; left: 3px; width: 16px; height: 16px; border-radius: 50%;
  background: var(--surface-heading); transition: transform var(--t-fast);
}
.cfg-toggle input:checked { background: var(--interactive-strong); }
.cfg-toggle input:checked::after { transform: translateX(18px); }
.cfg-toggle input:focus-visible { box-shadow: var(--focus-ring); }

.cfg-launcher { display: flex; gap: 32px; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; }
.cfg-launcher--off { opacity: 0.5; }
.cfg-fields--tight { margin-top: 0; flex: 1; min-width: 240px; }
</style>
