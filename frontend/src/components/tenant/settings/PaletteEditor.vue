<template>
  <section class="panel">
    <h2 class="panel-title">{{ $t('configure.colors.title') }}</h2>
    <p class="panel-sub">{{ $t('configure.colors.sub') }}</p>
    <ul class="pal">
      <li v-for="c in palette" :key="c.id" class="pal__row">
        <label class="pal__swatch" :style="{ backgroundColor: c.value }" :title="$t('configure.colors.pick')">
          <input type="color" :value="c.value" :aria-label="`${nameOf(c)}: ${$t('configure.colors.pick')}`" @input="setValue(c, $event.target.value)" />
        </label>
        <input
          v-if="isBase(c)"
          class="form-input pal__name"
          :value="nameOf(c)"
          :aria-label="$t('configure.colors.name')"
          readonly
          tabindex="-1"
        />
        <input v-else v-model="c.name" class="form-input pal__name" :aria-label="$t('configure.colors.name')" />
        <input
          class="form-input form-input--mono pal__hex"
          :class="{ 'pal__hex--bad': drafts[c.id] !== undefined && !parseHex(drafts[c.id]) }"
          :value="drafts[c.id] ?? c.value"
          :aria-label="`${nameOf(c)}: ${$t('configure.colors.hex')}`"
          maxlength="7"
          spellcheck="false"
          @input="typeHex(c, $event.target.value)"
          @blur="delete drafts[c.id]"
        />
        <button
          v-if="!isBase(c)"
          type="button"
          class="cfg-icon-btn"
          :aria-label="`${nameOf(c)}: ${$t('configure.colors.remove')}`"
          :title="$t('configure.colors.remove')"
          @click="removeColor(config, c.id)"
        >
          <font-awesome-icon :icon="['fas', 'trash-alt']" />
        </button>
        <span v-else class="pal__spacer" aria-hidden="true"></span>
      </li>
    </ul>
    <button type="button" class="btn-quiet pal__add" @click="add">
      <font-awesome-icon :icon="['fas', 'plus']" /> {{ $t('configure.colors.add') }}
    </button>
  </section>
</template>

<script setup>
import { computed, reactive } from 'vue';
import { useI18n } from 'vue-i18n';
import { v4 as uuidv4 } from 'uuid';
import { BASE_COLOR_IDS, removeColor, usePaletteNames } from './palette';

const props = defineProps({ config: { type: Object, required: true } });
const { t } = useI18n();
const { nameOf } = usePaletteNames();

const palette = computed(() => props.config.color_palette);
const isBase = (c) => BASE_COLOR_IDS.includes(c.id);

// "#abc", "abc123" and the like; anything else stays a draft until it's fixed
function parseHex(text) {
  const m = /^#?([0-9a-f]{3}|[0-9a-f]{6})$/i.exec((text || '').trim());
  if (!m) return null;
  const hex = m[1].length === 3 ? [...m[1]].map((d) => d + d).join('') : m[1];
  return `#${hex.toUpperCase()}`;
}

// What is being typed into a hex field, kept apart so half a value doesn't paint the chat
const drafts = reactive({});
function typeHex(c, text) {
  drafts[c.id] = text;
  const hex = parseHex(text);
  if (hex) c.value = hex;
}
const setValue = (c, hex) => { c.value = hex.toUpperCase(); delete drafts[c.id]; };

function add() {
  palette.value.push({ id: uuidv4(), name: t('configure.colors.newColor'), value: '#9CA3AF' });
}
</script>

<style scoped>
.pal { display: flex; flex-direction: column; gap: 8px; margin-top: 16px; }
.pal__row { display: grid; grid-template-columns: 40px minmax(0, 1fr) 7.5rem 36px; gap: 8px; align-items: center; }
.pal__swatch {
  position: relative; width: 40px; height: 40px; border-radius: var(--radius-md); cursor: pointer;
  border: 1px solid var(--surface-3);
}
.pal__swatch:focus-within { box-shadow: var(--focus-ring-shadow); }
.pal__swatch input { position: absolute; inset: 0; width: 100%; height: 100%; opacity: 0; cursor: pointer; }
.pal__name[readonly] { color: var(--surface-muted); cursor: default; }
.pal__hex { text-transform: uppercase; }
.pal__hex--bad { border-color: var(--status-warning); }
.pal__add { margin-top: 12px; }
</style>
