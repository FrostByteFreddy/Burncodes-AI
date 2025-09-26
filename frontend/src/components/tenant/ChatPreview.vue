<template>
    <BaseChat :config="config" :chatHistory="chatHistory" :isThinking="true" userMessage="Tell me about your services." />
</template>

<script setup>
import { ref } from 'vue';
import BaseChat from '@/components/chat/BaseChat.vue';

defineProps({
    config: {
        type: Object,
        required: true
    }
});

const chatHistory = ref([
    {
        text: 'Welcome! How can I help you today?',
        html: 'Welcome! How can I help you today?',
        isUser: false
    },
    {
        text: 'Tell me about your services.',
        isUser: true
    }
]);
</script>