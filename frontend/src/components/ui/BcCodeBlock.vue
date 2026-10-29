<template>
  <div class="bc-code">
    <div class="bc-code__head">
      <span class="bc-code__label">{{ label }}</span>
      <button type="button" :class="['bc-code__copy', { 'is-done': copied }]" @click="copy">
        <BcIcon :name="copied ? 'check' : 'copy'" /><span aria-live="polite">{{ copied ? $t('ui.copied') : $t('ui.copyCode') }}</span>
      </button>
    </div>
    <pre class="bc-code__pre"><code>{{ code }}</code></pre>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import BcIcon from './BcIcon.vue';

const props = defineProps({ code: { type: String, required: true }, label: { type: String, default: 'HTML' } });
const emit = defineEmits(['copy', 'copy-failed']);
const copied = ref(false);
async function copy() {
  try {
    await navigator.clipboard.writeText(props.code);
    copied.value = true;
    setTimeout(() => { copied.value = false; }, 2000);
    emit('copy');
  } catch {
    emit('copy-failed');
  }
}
</script>
