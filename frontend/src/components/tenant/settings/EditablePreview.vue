<template>
  <div ref="root" class="epv" @keydown.esc="open = null">
    <div ref="widget" class="epv__widget"><ChatPreview :config="config" :tenant-id="tenantId" /></div>

    <!-- Pens sit on top of the live widget; the widget itself stays untouched -->
    <div class="epv__layer" aria-hidden="false">
      <template v-for="spot in spots" :key="spot.key">
        <div v-if="hovered === spot.key || open === spot.key" class="epv__outline" :style="spot.outline"></div>
        <button
          type="button"
          class="epv__pen"
          :class="{ 'epv__pen--active': open === spot.key }"
          :style="spot.pen"
          :aria-label="$t('configure.edit.editPart', { part: $t(`configure.edit.parts.${spot.key}`) })"
          :aria-expanded="open === spot.key"
          @mouseenter="hovered = spot.key"
          @mouseleave="hovered = null"
          @focus="hovered = spot.key"
          @blur="hovered = null"
          @click.stop="toggle(spot.key)"
        >
          <font-awesome-icon :icon="['fas', 'pen']" />
        </button>
      </template>

      <div v-if="openSpot" ref="pop" class="epv__pop" :style="popStyle" role="dialog" :aria-label="$t(`configure.edit.parts.${openSpot.key}`)" @click.stop>
        <div class="epv__pop-head">
          <h3>{{ $t(`configure.edit.parts.${openSpot.key}`) }}</h3>
          <button type="button" class="cfg-icon-btn" :aria-label="$t('configure.edit.close')" @click="open = null">
            <font-awesome-icon :icon="['fas', 'xmark']" />
          </button>
        </div>

        <div v-if="openSpot.title" class="epv__field">
          <label for="epv-title" class="form-field">{{ $t('configure.header.chatTitle') }}</label>
          <input id="epv-title" v-model="config.chatbot_title" type="text" class="form-input" />
        </div>
        <ImageField v-if="openSpot.logo" field="epv-logo" :label="$t('configure.header.logo')" v-model="config.logo" />

        <div v-for="f in openSpot.fields" :key="f" class="epv__field">
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
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { v4 as uuidv4 } from 'uuid';
import ChatPreview from '../ChatPreview.vue';
import SwatchPicker from './SwatchPicker.vue';
import ImageField from './ImageField.vue';
import { getStyle, setStyle } from './palette';

const props = defineProps({
  config:   { type: Object, required: true },
  tenantId: { type: String, required: true },
});
const { t } = useI18n();

// What can be edited, where its pen goes, and which settings it opens
const PARTS = [
  { key: 'header', selector: '.chat-header', corner: 'inner-left', fields: ['header_background_color', 'header_text_color'] },
  { key: 'title', selector: '.chat-header h1', corner: 'right', title: true, logo: true, fields: [] },
  { key: 'buttons', selector: '.chat-header .btn-square', corner: 'below', fields: ['close_button_background_color', 'close_button_icon_color', 'reset_button_color', 'reset_button_icon_color', 'share_button_color', 'share_button_icon_color'] },
  { key: 'bot', selector: '.bot-message', corner: 'bottom-right', fields: ['bot_message_background_color', 'bot_message_text_color'] },
  { key: 'user', selector: '.user-message', corner: 'top-left', fields: ['user_message_background_color', 'user_message_text_color'] },
  { key: 'starters', selector: '.starter-chip', corner: 'top-left', fields: ['starter_background_color', 'starter_text_color'] },
  { key: 'background', selector: '.chat-main', corner: 'inner-bottom-right', fields: ['chat_background_color'] },
  { key: 'input', selector: '.chat-input', corner: 'top-left', fields: ['input_background_color', 'input_text_color', 'input_focus_ring_color'] },
  { key: 'send', selector: '.send-button', corner: 'top-left', fields: ['send_button_background_color', 'send_button_text_color'] },
];

const root = ref(null);
const widget = ref(null);
const pop = ref(null);
const spots = ref([]);
const open = ref(null);
const hovered = ref(null);
const popStyle = ref({});
const openSpot = computed(() => spots.value.find((s) => s.key === open.value));

const PEN = 26;
function penPosition(r, corner) {
  const half = PEN / 2;
  switch (corner) {
    case 'inner-left': return { left: r.left + 10, top: r.top + r.height / 2 - half };
    case 'below': return { left: r.left + r.width / 2 - half, top: r.bottom + 4 };
    case 'bottom-right': return { left: r.right - half, top: r.bottom - half };
    case 'right': return { left: r.right + 4, top: r.top + r.height / 2 - half };
    case 'top-right': return { left: r.right - half, top: r.top - half };
    case 'inner-bottom-right': return { left: r.right - PEN - 10, top: r.bottom - PEN - 10 };
    default: return { left: r.left - half, top: r.top - half };
  }
}

// Measure the widget's parts relative to the preview; the first visible match wins
function measure() {
  const el = root.value;
  if (!el) return;
  const box = el.getBoundingClientRect();
  const main = el.querySelector('.chat-main')?.getBoundingClientRect();
  const next = [];
  for (const part of PARTS) {
    if (part.key === 'buttons' && !el.querySelector(part.selector)) continue;
    const target = [...el.querySelectorAll(part.selector)].find((n) => {
      const r = n.getBoundingClientRect();
      if (!r.width || !r.height) return false;
      // bubbles scroll inside the chat; only use ones currently in view
      return !main || n.closest('.chat-main') === null || part.key === 'background' || (r.top >= main.top && r.bottom <= main.bottom);
    });
    if (!target) continue;
    const r = target.getBoundingClientRect();
    const rel = { left: r.left - box.left, top: r.top - box.top, right: r.right - box.left, bottom: r.bottom - box.top, width: r.width, height: r.height };
    const p = penPosition(rel, part.corner);
    p.left = Math.min(Math.max(p.left, 2), box.width - PEN - 2);
    p.top = Math.min(Math.max(p.top, 2), box.height - PEN - 2);
    next.push({
      ...part,
      rect: rel,
      pen: { left: `${p.left}px`, top: `${p.top}px` },
      outline: { left: `${rel.left}px`, top: `${rel.top}px`, width: `${rel.width}px`, height: `${rel.height}px` },
    });
  }
  spots.value = next;
  if (open.value && !next.some((s) => s.key === open.value)) open.value = null;
  placePopover();
}

// Popover opens beside the part, kept inside the preview
async function placePopover() {
  if (!openSpot.value || !root.value) return;
  await nextTick();
  const box = root.value.getBoundingClientRect();
  const h = pop.value?.offsetHeight || 240;
  const w = Math.min(320, box.width - 16);
  const r = openSpot.value.rect;
  let top = r.bottom + 10;
  if (top + h > box.height - 8) top = Math.max(8, r.top - h - 10);
  const left = Math.min(Math.max(8, r.left), box.width - w - 8);
  popStyle.value = { top: `${top}px`, left: `${left}px`, width: `${w}px` };
}

const toggle = (key) => { open.value = open.value === key ? null : key; placePopover(); };

// A custom colour becomes a palette colour, so it shows up everywhere else too
function useCustom(field, hex) {
  const value = hex.toUpperCase();
  let color = props.config.color_palette.find((c) => c.value.toUpperCase() === value);
  if (!color) {
    color = { id: uuidv4(), name: t('configure.colors.newColor'), value };
    props.config.color_palette.push(color);
  }
  setStyle(props.config, field, color.id);
}

let frame = 0;
const schedule = () => { cancelAnimationFrame(frame); frame = requestAnimationFrame(measure); };
const onOutside = (e) => { if (open.value && root.value && !root.value.contains(e.target)) open.value = null; };
let resizeObs, mutationObs;
onMounted(() => {
  resizeObs = new ResizeObserver(schedule);
  resizeObs.observe(root.value);
  // messages, starters and config changes re-render the widget
  mutationObs = new MutationObserver(schedule);
  mutationObs.observe(widget.value, { childList: true, subtree: true, attributes: true, attributeFilter: ['class', 'style', 'src'] });
  root.value.addEventListener('scroll', schedule, true);
  document.addEventListener('click', onOutside);
  schedule();
});
onBeforeUnmount(() => {
  resizeObs?.disconnect();
  mutationObs?.disconnect();
  root.value?.removeEventListener('scroll', schedule, true);
  document.removeEventListener('click', onOutside);
  cancelAnimationFrame(frame);
});
</script>

<style scoped>
.epv { position: relative; height: 100%; }
.epv__widget { height: 100%; }
.epv__layer { position: absolute; inset: 0; pointer-events: none; }

.epv__pen {
  position: absolute; width: 26px; height: 26px; border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  pointer-events: auto; cursor: pointer; font-size: 11px;
  background: var(--interactive-strong); color: #fff;
  border: 2px solid #fff; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.35);
  transition: transform var(--t-fast), background var(--t-fast);
}
.epv__pen:hover, .epv__pen--active { transform: scale(1.12); background: var(--interactive); }
.epv__pen:focus-visible { box-shadow: var(--focus-ring); }

.epv__outline {
  position: absolute; pointer-events: none; border-radius: 8px;
  outline: 2px dashed var(--interactive-strong); outline-offset: 2px;
}

.epv__pop {
  position: absolute; pointer-events: auto; z-index: 5;
  display: flex; flex-direction: column; gap: 14px;
  max-height: calc(100% - 16px); overflow-y: auto;
  padding: 16px; border-radius: var(--radius-lg);
  background: var(--surface-1); border: 1px solid var(--surface-3);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5);
}
.epv__pop-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; margin: -4px -6px -4px 0; }
.epv__pop-head h3 { font-size: 15px; font-weight: 700; color: var(--surface-heading); }
.epv__field .form-field { font-size: var(--text-sm); }

@media (prefers-reduced-motion: reduce) {
  .epv__pen { transition: none; }
}
</style>
