<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold mb-6">Chat Logs</h1>
    <div v-if="isLoading" class="flex justify-center items-center h-64">
      <span class="loading loading-spinner loading-lg"></span>
    </div>
    <div v-else-if="error" class="text-error">
      {{ error }}
    </div>
    <div v-else class="bg-base-100 p-6 rounded-lg shadow-lg">
      <div v-if="selectedConversation" class="mb-6">
        <button @click="selectedConversation = null" class="btn btn-secondary mb-4">
          <font-awesome-icon :icon="['fas', 'arrow-left']" class="mr-2" />
          Back to Conversations
        </button>
        <div v-for="log in conversationLogs" :key="log.id" class="chat" :class="log.user_message ? 'chat-end' : 'chat-start'">
          <div class="chat-bubble" :class="log.user_message ? 'chat-bubble-primary' : 'chat-bubble-secondary'">
            {{ log.user_message || log.ai_message }}
          </div>
        </div>
      </div>
      <div v-else>
        <h2 class="text-xl font-bold mb-4">Conversations</h2>
        <div v-for="convo in conversations" :key="convo.conversation_id" @click="selectConversation(convo.conversation_id)" class="p-4 mb-2 rounded-lg hover:bg-base-200 cursor-pointer">
          <p class="font-semibold">{{ new Date(convo.created_at).toLocaleString() }}</p>
          <p class="text-sm text-base-content/70">{{ convo.conversation_id }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';
import { useAuthStore } from '@/stores/auth';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

const route = useRoute();
const authStore = useAuthStore();
const tenantId = ref(route.params.tenantId);
const conversations = ref([]);
const conversationLogs = ref([]);
const selectedConversation = ref(null);
const isLoading = ref(true);
const error = ref(null);

const fetchConversations = async () => {
  try {
    isLoading.value = true;
    const token = authStore.session.access_token;
    const response = await axios.get(`${API_BASE_URL}/chat/${tenantId.value}/conversations`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    conversations.value = response.data;
  } catch (err) {
    error.value = 'Failed to load conversations. Please try again later.';
    console.error(err);
  } finally {
    isLoading.value = false;
  }
};

const selectConversation = async (conversationId) => {
  try {
    isLoading.value = true;
    selectedConversation.value = conversationId;
    const token = authStore.session.access_token;
    const response = await axios.get(`${API_BASE_URL}/chat/${tenantId.value}/conversation/${conversationId}`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    conversationLogs.value = response.data;
  } catch (err) {
    error.value = 'Failed to load conversation logs. Please try again later.';
    console.error(err);
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  fetchConversations();
});
</script>