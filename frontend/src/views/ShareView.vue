<template>
  <div class="chat-page">
    <ChatWidget :share-id="shareId" />
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import ChatWidget from '@/components/chat/ChatWidget.vue';

const route   = useRoute();
const shareId = computed(() => route.params.shareId);

const setAppHeight = () => {
  const h = window.visualViewport ? window.visualViewport.height : window.innerHeight;
  document.documentElement.style.setProperty('--app-height', `${h}px`);
};

onMounted(() => {
  setAppHeight();
  window.addEventListener('resize', setAppHeight);
  if (window.visualViewport) window.visualViewport.addEventListener('resize', setAppHeight);
});

onUnmounted(() => {
  window.removeEventListener('resize', setAppHeight);
  if (window.visualViewport) window.visualViewport.removeEventListener('resize', setAppHeight);
});
</script>

<style scoped>
.chat-page {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  width: 100%;
  height: var(--app-height, 100dvh);
  padding: 1.5rem 0;
  background: none;
}

.chat-page > :deep(.chat-widget) {
  max-width: 650px;
  width: 100%;
  height: calc(var(--app-height, 100dvh) - 3rem);
  box-shadow: none !important;
  border: none !important;
  border-radius: 0 !important;
}

@media (max-width: 768px) {
  :global(body) { overflow: hidden; }
  :global(:root) {
    --chat-border-radius: 0px !important;
    --chat-custom-radius: 0px !important;
  }
  .chat-page {
    padding: 0;
    width: 100vw;
    height: var(--app-height, 100dvh);
  }
  .chat-page > :deep(.chat-widget) {
    max-width: 100vw;
    width: 100vw;
    height: var(--app-height, 100dvh);
    border-radius: 0 !important;
    box-shadow: none !important;
    border: none !important;
  }
}
</style>
