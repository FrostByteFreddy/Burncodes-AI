<template>
  <ChatWidget
    :tenant-id="tenantId"
    :is-widget="isWidget"
    class="h-screen"
  />
</template>

<script setup>
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import ChatWidget from '@/components/chat/ChatWidget.vue';

const route  = useRoute();
const tenantId = computed(() => route.params.tenantId);
const isWidget = computed(() => 'widget' in route.query);
</script>
