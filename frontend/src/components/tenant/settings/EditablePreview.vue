<template>
  <div class="epv">
    <div class="epv__bar">
      <div class="epv__seg" role="group" :aria-label="$t('configure.edit.modeLabel')">
        <button v-for="m in ['edit', 'try']" :key="m" type="button" class="epv__seg-btn" :class="{ 'epv__seg-btn--on': mode === m }" :aria-pressed="mode === m" @click="setMode(m)">
          {{ $t(`configure.edit.modes.${m}`) }}
        </button>
      </div>
      <div v-if="mode === 'edit'" class="epv__seg" role="group" :aria-label="$t('configure.edit.stateLabel')">
        <button v-for="s in STATES" :key="s" type="button" class="epv__seg-btn" :class="{ 'epv__seg-btn--on': state === s }" :aria-pressed="state === s" @click="setState(s)">
          {{ $t(`configure.edit.states.${s}`) }}
        </button>
      </div>
    </div>

    <p v-if="mode === 'try'" class="epv__hint">{{ $t('configure.edit.tryHint') }}</p>
    <p v-else-if="hardToRead.length" class="epv__hint epv__hint--warn">
      <font-awesome-icon :icon="['fas', 'triangle-exclamation']" />
      {{ $t('configure.edit.hardToRead', { parts: hardToRead.join(', ') }) }}
    </p>
    <p v-else class="epv__hint">{{ $t('configure.edit.hint') }}</p>

    <div ref="stage" class="epv__stage">
      <!-- The real chatbot -->
      <ChatPreview v-if="mode === 'try'" :config="config" :tenant-id="tenantId" />

      <template v-else>
        <!-- Sample chat, not interactive; the hit areas on top do the editing -->
        <div v-if="state !== 'launcher'" ref="widget" class="epv__widget" inert>
          <BaseChat :config="config" :chat-history="sampleHistory" user-message="" />
        </div>

        <!-- A website corner with the chat button -->
        <div v-else ref="widget" class="epv__site" inert>
          <div class="epv__site-lines"><span></span><span></span><span></span><span></span></div>
          <div class="epv__launcher" :class="{ 'epv__launcher--off': config.widget_enabled === false }" :style="{ backgroundColor: colorOf(config, getStyle(config, 'launcher_background_color')) }">
            <img v-if="config.launcher_icon" :src="config.launcher_icon" alt="" />
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          </div>
        </div>

        <div class="epv__layer">
          <button
            v-for="hit in hits"
            :key="hit.id"
            type="button"
            class="epv__hit"
            :class="{ 'epv__hit--open': openId === hit.id, 'epv__hit--round': hit.round }"
            :style="hit.style"
            :aria-label="$t(`configure.edit.parts.${hit.key}`)"
            :aria-expanded="openId === hit.id"
            @click.stop="toggle(hit)"
          >
            <span class="epv__tag" :class="{ 'epv__tag--below': hit.tagBelow, 'epv__tag--end': hit.tagEnd }">{{ $t(`configure.edit.parts.${hit.key}`) }}</span>
          </button>

          <button v-if="addButton" type="button" class="epv__add" :style="addButton" @click.stop="addQuestion">
            <font-awesome-icon :icon="['fas', 'plus']" /> {{ $t('configure.edit.addQuestion') }}
          </button>

          <div v-if="openHit" ref="pop" class="epv__pop" :style="popStyle" role="dialog" :aria-label="$t(`configure.edit.parts.${openHit.key}`)" @click.stop @keydown.esc="close">
            <div class="epv__pop-head">
              <h3>{{ $t(`configure.edit.parts.${openHit.key}`) }}</h3>
              <button type="button" class="cfg-icon-btn" :aria-label="$t('configure.edit.close')" @click="close">
                <font-awesome-icon :icon="['fas', 'xmark']" />
              </button>
            </div>

            <!-- Texts -->
            <template v-if="openHit.key === 'header'">
              <Field>
                <FieldLabel for="epv-title">{{ $t('configure.header.chatTitle') }}</FieldLabel>
                <Input id="epv-title" v-model="config.chatbot_title" type="text"  />
              </Field>
              <ImageField field="epv-logo" :label="$t('configure.header.logo')" v-model="config.logo" />
            </template>
            <div v-if="openHit.key === 'bot' && state === 'start' && openHit.index === 0">
              <Label for="epv-intro" class="mb-2">{{ $t('configure.welcome.intro') }}</Label>
              <AutoGrowTextarea id="epv-intro" v-model="form.intro_message" rows="3" />
            </div>
            <div v-if="openHit.key === 'starter' && starters[openHit.index]">
              <Label for="epv-question" class="mb-2">{{ $t('configure.edit.question') }}</Label>
              <div class="epv__row">
                <Input id="epv-question" ref="questionInput" v-model="starters[openHit.index].label" type="text"  />
                <button type="button" class="cfg-icon-btn" :aria-label="$t('configure.edit.removeQuestion')" @click="removeQuestion(openHit.index)">
                  <font-awesome-icon :icon="['fas', 'trash-alt']" />
                </button>
              </div>
              <p class="field-hint">{{ $t('configure.edit.startersShared') }}</p>
            </div>
            <div v-if="openHit.key === 'input'">
              <Label for="epv-placeholder" class="mb-2">{{ $t('configure.welcome.placeholder') }}</Label>
              <Input id="epv-placeholder" v-model="config.input_placeholder" type="text"  />
            </div>

            <!-- Colours -->
            <div v-for="f in openHit.fields" :key="f">
              <p :id="`epv-${f}`" class="form-field">{{ $t(`configure.colors.labels.${f}`) }}</p>
              <SwatchPicker
                :model-value="getStyle(config, f)"
                :palette="config.color_palette"
                :label-id="`epv-${f}`"
                allow-custom
                @update:model-value="setStyle(config, f, $event)"
                @custom="useCustom(f, $event)"
              />
            </div>

            <!-- Switches -->
            <template v-if="openHit.key === 'header'">
              <Field orientation="horizontal" class="w-fit"><Switch v-model="config.show_reset_button" /><span class="text-sm">{{ $t('configure.header.reset') }}</span></Field>
              <Field orientation="horizontal" class="w-fit"><Switch v-model="config.show_share_button" /><span class="text-sm">{{ $t('configure.header.share') }}</span></Field>
            </template>
            <template v-if="openHit.key === 'launcher'">
              <ImageField field="epv-launcher-icon" :label="$t('configure.launcher.icon')" :hint="$t('configure.launcher.iconHint')" v-model="config.launcher_icon" />
              <Field orientation="horizontal" class="w-fit"><Switch v-model="launcherEnabled" /><span class="text-sm">{{ $t('configure.launcher.enabled') }}</span></Field>
              <p v-if="!launcherEnabled" class="field-hint field-hint--warn">{{ $t('configure.launcher.disabledHint') }}</p>
            </template>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { Switch } from '@/components/ui/switch';
import { Field, FieldLabel } from '@/components/ui/field';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { v4 as uuidv4 } from 'uuid';
import ChatPreview from '../ChatPreview.vue';
import BaseChat from '../../chat/BaseChat.vue';
import AutoGrowTextarea from '../../AutoGrowTextarea.vue';
import SwatchPicker from './SwatchPicker.vue';
import ImageField from './ImageField.vue';
import { colorOf, contrast, getStyle, setStyle } from './palette';
import { processBotMessage } from '@/utils/chatProcessor';
import { DEFAULT_AUDIENCE, SAMPLE_CONVERSATION } from '@/utils/chatbotDefaults';

const props = defineProps({
  form:     { type: Object, required: true },
  tenantId: { type: String, required: true },
});
const { t, locale } = useI18n();
const config = computed(() => props.form.widget_config);

const STATES = ['start', 'conversation', 'launcher'];
const mode = ref('edit');
const state = ref('start');

// ── Sample content ──────────────────────────────────────────────────
const sample = computed(() => {
  const samples = SAMPLE_CONVERSATION[props.form.audience] || SAMPLE_CONVERSATION[DEFAULT_AUDIENCE];
  return samples[locale.value] || samples.en;
});
const bot = (text) => ({ ...processBotMessage(text || ''), isUser: false });
const sampleHistory = computed(() => {
  const intro = bot(props.form.intro_message);
  if (state.value === 'start') return [intro];
  return [intro, { text: config.value.conversation_starters?.[0]?.label || sample.value.question, isUser: true }, bot(sample.value.answer)];
});

// ── Editable parts: what to look for in the widget, and what each one edits ──
const PARTS = [
  { key: 'header', selector: '.chat-header', fields: ['header_background_color', 'header_text_color'] },
  { key: 'reset', selector: '.reset-button', round: true, fields: ['reset_button_color', 'reset_button_icon_color'] },
  { key: 'share', selector: '.share-button', round: true, fields: ['share_button_color', 'share_button_icon_color'] },
  { key: 'close', selector: '.close-button', round: true, fields: ['close_button_background_color', 'close_button_icon_color'] },
  { key: 'background', selector: '.chat-main', fields: ['chat_background_color'] },
  { key: 'bot', selector: '.bot-message', fields: ['bot_message_background_color', 'bot_message_text_color'] },
  { key: 'user', selector: '.user-message', fields: ['user_message_background_color', 'user_message_text_color'] },
  { key: 'starter', selector: '.starter-chip', fields: ['starter_background_color', 'starter_text_color'] },
  { key: 'footer', selector: '.chat-footer', fields: ['footer_background_color'] },
  { key: 'input', selector: '.chat-input', fields: ['input_background_color', 'input_text_color'] },
  { key: 'send', selector: '.send-button', round: true, fields: ['send_button_background_color', 'send_button_text_color'] },
  { key: 'launcher', selector: '.epv__launcher', round: true, fields: ['launcher_background_color'] },
];

const stage = ref(null);
const widget = ref(null);
const pop = ref(null);
const questionInput = ref(null);
const hits = ref([]);
const addButton = ref(null);
const openId = ref(null);
const popStyle = ref({});
const openHit = computed(() => hits.value.find((h) => h.id === openId.value));

function measure() {
  const root = stage.value;
  const w = widget.value;
  if (!root || !w || mode.value !== 'edit') { hits.value = []; addButton.value = null; return; }
  const box = root.getBoundingClientRect();
  const rel = (r) => ({ left: r.left - box.left, top: r.top - box.top, width: r.width, height: r.height });
  const next = [];
  for (const part of PARTS) {
    w.querySelectorAll(part.selector).forEach((el, index) => {
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height) return;
      const p = rel(r);
      next.push({
        ...part, index, id: `${part.key}-${index}`, rect: p, area: p.width * p.height,
        tagBelow: p.top < 28,
        tagEnd: p.left > box.width / 2,
        style: { left: `${p.left}px`, top: `${p.top}px`, width: `${p.width}px`, height: `${p.height}px` },
      });
    });
  }
  // Smaller parts sit on top, so a bubble wins over the chat background behind it
  hits.value = next.sort((a, b) => b.area - a.area).map((h, i) => ({ ...h, style: { ...h.style, zIndex: i + 1 } }));

  // "Add question" sits under the last suggested question (or under the welcome bubble)
  addButton.value = null;
  if (state.value === 'start') {
    const anchor = [...w.querySelectorAll('.starter-chip')].pop() || w.querySelector('.bot-message');
    if (anchor) {
      const r = rel(anchor.getBoundingClientRect());
      const right = box.width - (r.left + r.width);
      addButton.value = { top: `${r.top + r.height + 10}px`, right: `${Math.max(right, 12)}px` };
    }
  }
  if (openId.value && !openHit.value) openId.value = null;
  placePopover();
}

async function placePopover() {
  if (!openHit.value || !stage.value) return;
  await nextTick();
  const box = stage.value.getBoundingClientRect();
  const h = pop.value?.offsetHeight || 260;
  const w = Math.min(320, box.width - 16);
  const r = openHit.value.rect;
  let top = r.top + r.height + 10;
  if (top + h > box.height - 8) top = r.top - h - 10;
  top = Math.min(Math.max(8, top), Math.max(8, box.height - h - 8));
  const left = Math.min(Math.max(8, r.left + r.width / 2 - w / 2), box.width - w - 8);
  popStyle.value = { top: `${top}px`, left: `${left}px`, width: `${w}px` };
}

const toggle = (hit) => { openId.value = openId.value === hit.id ? null : hit.id; placePopover(); };
const close = () => { openId.value = null; };
const setMode = (m) => { mode.value = m; close(); schedule(); };
const setState = (s) => { state.value = s; close(); schedule(); };

// ── Suggested questions ─────────────────────────────────────────────
const starters = computed(() => {
  if (!config.value.conversation_starters) config.value.conversation_starters = [];
  return config.value.conversation_starters;
});
async function addQuestion() {
  starters.value.push({ id: uuidv4(), label: sample.value.newQuestion });
  await nextTick();
  measure();
  openId.value = `starter-${starters.value.length - 1}`;
  await placePopover();
  questionInput.value?.focus();
  questionInput.value?.select();
}
function removeQuestion(index) {
  starters.value.splice(index, 1);
  close();
}

// ── Colours ─────────────────────────────────────────────────────────
// A custom colour joins the palette so it can be reused elsewhere
function useCustom(field, hex) {
  const value = hex.toUpperCase();
  let color = config.value.color_palette.find((c) => c.value.toUpperCase() === value);
  if (!color) {
    color = { id: uuidv4(), name: t('configure.colors.newColor'), value };
    config.value.color_palette.push(color);
  }
  setStyle(config.value, field, color.id);
}

const launcherEnabled = computed({
  get: () => config.value.widget_enabled !== false,
  set: (v) => { config.value.widget_enabled = v; },
});

// Text residents have to read against its background; WCAG AA asks for 4.5:1
const PAIRS = [
  ['header', 'header_text_color', 'header_background_color'],
  ['bot', 'bot_message_text_color', 'bot_message_background_color'],
  ['user', 'user_message_text_color', 'user_message_background_color'],
  ['input', 'input_text_color', 'input_background_color'],
  ['send', 'send_button_text_color', 'send_button_background_color'],
  ['starter', 'starter_text_color', 'starter_background_color'],
];
const hardToRead = computed(() => PAIRS
  .filter(([, fg, bg]) => getStyle(config.value, fg) && getStyle(config.value, bg)
    && contrast(colorOf(config.value, getStyle(config.value, fg)), colorOf(config.value, getStyle(config.value, bg))) < 4.5)
  .map(([key]) => t(`configure.edit.parts.${key}`)));

// ── Keep hit areas aligned with the widget ──────────────────────────
let frame = 0;
const schedule = () => { cancelAnimationFrame(frame); frame = requestAnimationFrame(() => nextTick(measure)); };
const onOutside = (e) => { if (openId.value && pop.value && !pop.value.contains(e.target)) close(); };
let resizeObs, mutationObs;
watch(widget, (el) => {
  mutationObs?.disconnect();
  if (el) mutationObs.observe(el, { childList: true, subtree: true, attributes: true, characterData: true });
  schedule();
});
onMounted(() => {
  resizeObs = new ResizeObserver(schedule);
  resizeObs.observe(stage.value);
  mutationObs = new MutationObserver(schedule);
  if (widget.value) mutationObs.observe(widget.value, { childList: true, subtree: true, attributes: true, characterData: true });
  document.addEventListener('click', onOutside);
  schedule();
});
onBeforeUnmount(() => {
  resizeObs?.disconnect();
  mutationObs?.disconnect();
  document.removeEventListener('click', onOutside);
  cancelAnimationFrame(frame);
});
</script>

<style scoped>
.epv { height: 100%; display: flex; flex-direction: column; gap: 10px; }

.epv__bar { display: flex; flex-wrap: wrap; gap: 8px; justify-content: space-between; }
.epv__seg { display: inline-flex; gap: 2px; padding: 3px; border-radius: var(--radius-pill); background: var(--surface-1); border: 1px solid var(--surface-3); }
.epv__seg-btn {
  padding: 5px 12px; border: none; border-radius: var(--radius-pill); background: none; cursor: pointer;
  font: inherit; font-size: var(--text-sm); font-weight: 600; color: var(--surface-muted);
}
.epv__seg-btn:hover { color: var(--surface-heading); }
.epv__seg-btn--on { background: var(--surface-3); color: var(--surface-heading); }
.epv__hint { font-size: var(--text-sm); color: var(--surface-muted); }
.epv__hint--warn { color: var(--status-warning); }

.epv__stage { position: relative; flex: 1; min-height: 0; }
.epv__widget, .epv__site {
  height: 100%; border-radius: 20px; overflow: hidden;
  box-shadow: var(--shadow-3);
}

/* Mock website for the chat button */
.epv__site { position: relative; background: #F4F5F7; padding: 32px; }
.epv__site-lines { display: flex; flex-direction: column; gap: 14px; max-width: 70%; }
.epv__site-lines span { height: 12px; border-radius: 6px; background: #DFE2E8; }
.epv__site-lines span:first-child { height: 22px; width: 60%; background: #CDD2DB; }
.epv__site-lines span:last-child { width: 45%; }
.epv__launcher {
  position: absolute; right: 24px; bottom: 24px; width: 60px; height: 60px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center; box-shadow: 0 6px 18px rgba(0, 0, 0, 0.25);
}
.epv__launcher img { width: 30px; height: 30px; object-fit: contain; }
.epv__launcher--off { opacity: 0.35; }

/* Hit areas: invisible until hovered or focused, then outlined with a name tag */
.epv__layer { position: absolute; inset: 0; pointer-events: none; }
.epv__hit {
  position: absolute; pointer-events: auto; cursor: pointer;
  background: none; border: none; padding: 0; border-radius: 10px;
}
.epv__hit--round { border-radius: 50%; }
.epv__hit:hover, .epv__hit:focus-visible, .epv__hit--open {
  /* Only a frame: the part stays visible while it's being edited. The light
     ring keeps the frame readable on a header in the same colour. */
  outline: 2px dashed var(--interactive-strong); outline-offset: 2px;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.9);
}
.epv__tag {
  position: absolute; left: 0; bottom: calc(100% + 6px); white-space: nowrap;
  padding: 2px 8px; border-radius: var(--radius-pill);
  background: var(--interactive-strong); color: #fff; font-size: var(--text-xs); font-weight: 700;
  opacity: 0; pointer-events: none; transition: opacity var(--t-fast);
}
.epv__tag--below { bottom: auto; top: calc(100% + 6px); }
.epv__tag--end { left: auto; right: 0; }
.epv__hit:hover > .epv__tag, .epv__hit:focus-visible > .epv__tag { opacity: 1; }
.epv__hit--open > .epv__tag { opacity: 0; }

.epv__add {
  position: absolute; pointer-events: auto; z-index: 100;
  display: inline-flex; align-items: center; gap: 6px;
  padding: 6px 14px; border-radius: var(--radius-pill); cursor: pointer;
  background: rgba(255, 255, 255, 0.85); border: 2px dashed var(--brand-indigo);
  color: var(--brand-indigo); font: inherit; font-size: var(--text-sm); font-weight: 700;
}
.epv__add:hover { background: #fff; }

.epv__pop {
  position: absolute; pointer-events: auto; z-index: 200;
  display: flex; flex-direction: column; gap: 14px;
  max-height: calc(100% - 16px); overflow-y: auto;
  padding: 16px; border-radius: var(--radius-lg);
  background: var(--surface-1); border: 1px solid var(--surface-3);
  box-shadow: var(--shadow-3);
}
.epv__pop-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin: -4px -6px -4px 0; }
.epv__pop-head h3 { font-size: 15px; font-weight: 700; color: var(--surface-heading); }
.epv__pop .form-field { font-size: var(--text-sm); }
.epv__row { display: flex; gap: 6px; align-items: center; }


@media (prefers-reduced-motion: reduce) {
  .epv__tag { transition: none; }
}
</style>
