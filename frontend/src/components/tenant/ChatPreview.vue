<template>
  <div class="chat-preview-wrap">
    <ChatWidget :config="config" />
  </div>
</template>

<script setup>
import ChatWidget from '../chat/ChatWidget.vue';

defineProps({
  config: { type: Object, required: true },
});
</script>

<style scoped>
.chat-preview-wrap {
  height: 100%;
  min-height: 500px;
  border-radius: var(--radius-lg);
  overflow: hidden;
}
</style>