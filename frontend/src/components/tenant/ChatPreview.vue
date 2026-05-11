<template>
  <div class="chat-preview-wrap">
    <ChatWidget :config="config" :tenant-id="tenantId" />
  </div>
</template>

<script setup>
import ChatWidget from '../chat/ChatWidget.vue';

defineProps({
  config:   { type: Object, required: true },
  tenantId: { type: String, required: true },
});
</script>

<style scoped>
.chat-preview-wrap {
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
  /* Fixed height so it looks like a chat widget, not a stretched page */
  height: 560px;
  max-width: 420px;
  width: 100%;
  margin: 0 auto;
}
</style>