<template>
  <main class="chat-page">
    <ChatWidget :share-id="shareId" />
  </main>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import ChatWidget from '@/components/chat/ChatWidget.vue';

const route   = useRoute();
const shareId = computed(() => route.params.shareId);
</script>

<style scoped>
/* ── Desktop ─────────────────────────────────────────────────────────────── */
.chat-page {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  width: 100%;
  height: 100dvh;
  padding: 1.5rem 0;
  background: none;
}

.chat-page > :deep(.chat-widget) {
  max-width: 650px;
  width: 100%;
  height: calc(100dvh - 3rem);
  box-shadow: none !important;
  border: none !important;
  border-radius: 0 !important;
}

/* ── Mobile ──────────────────────────────────────────────────────────────── */
@media (max-width: 768px) {
  :global(html),
  :global(body),
  :global(#app),
  :global(.app-root) {
    height: 100%;
    overflow: hidden;
    overscroll-behavior: none;
  }

  :global(:root) {
    --chat-border-radius: 0px !important;
    --chat-custom-radius: 0px !important;
  }

  .chat-page {
    height: 100%;
    width: 100%;
    padding: 0;
    align-items: stretch;
  }

  .chat-page > :deep(.chat-widget) {
    max-width: 100%;
    width: 100%;
    height: 100%;
    border-radius: 0 !important;
    box-shadow: none !important;
    border: none !important;
  }
}
</style>
