<template>
  <div class="chat-page">
    <ChatWidget :tenant-id="tenantId" :is-widget="true" />
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import ChatWidget from '@/components/chat/ChatWidget.vue';

const route    = useRoute();
const tenantId = computed(() => route.params.tenantId);
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
/*
 * Key: build a height:100% chain from html down to the chat widget.
 * With `interactive-widget=resizes-content` in the viewport meta, the browser
 * shrinks the layout height when the keyboard appears — the chain propagates
 * that shrinkage down naturally, no JS needed.
 *
 * Do NOT use dvh / vh here: on iOS they reference the layout viewport which
 * does not change with keyboard even with interactive-widget=resizes-content
 * on all Safari versions. Percentage inherits the already-shrunk parent.
 */
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
