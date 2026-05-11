<template>
  <!-- Standalone browser page: center the chat card on a neutral background -->
  <div v-if="!isWidget" class="chat-standalone-page">
    <ChatWidget :tenant-id="tenantId" />
  </div>

  <!-- Embedded via widget.js iframe: full-screen, no chrome -->
  <ChatWidget v-else :tenant-id="tenantId" :is-widget="true" />
</template>

<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import ChatWidget from '@/components/chat/ChatWidget.vue';

const route    = useRoute();
const tenantId = computed(() => route.params.tenantId);
const isWidget = computed(() => 'widget' in route.query);
</script>

<style scoped>
.chat-standalone-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: #f3f4f6;
}

/* Give the card a sensible max-width so it doesn't stretch to full screen */
.chat-standalone-page :deep(.chat-widget) {
  width: 100%;
  max-width: 480px;
  height: 640px;
}
</style>
