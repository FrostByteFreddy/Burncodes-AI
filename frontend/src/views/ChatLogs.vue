<template>
  <h1 class="text-2xl font-bold mb-6">{{ $t("chatLogs.title") }}</h1>

  <div v-if="isLoading" class="flex justify-center items-center h-64">
    <span class="loading loading-spinner loading-lg"></span>
  </div>
  <div v-else-if="error" class="text-error">
    {{ error }}
  </div>

  <div v-else class="bg-base-100 p-6 rounded-lg shadow-lg">
    <div v-if="selectedConversation">
      <button
        @click="selectedConversation = null"
        class="btn btn-secondary mb-4"
      >
        <font-awesome-icon :icon="['fas', 'arrow-left']" class="mr-2" />
        {{ $t("chatLogs.back") }}
      </button>

      <div
        ref="chatContainer"
        class="max-h-[70vh] overflow-y-auto p-4 rounded-lg bg-base-200/50 space-y-4"
      >
        <div v-for="log in conversationLogs" :key="log.id">
          <div
            v-if="log.user_message"
            class="chat chat-end flex bg-primary-light p-4 rounded-lg"
          >
            <font-awesome-icon
              :icon="['fas', 'fa-user']"
              class="mr-2 mt-1 hidden sm:flex"
            />
            <div class="chat-bubble chat-bubble-primary">
              {{ log.user_message }}
            </div>
          </div>

          <div
            v-if="log.ai_message"
            class="chat chat-start flex mt-4 p-4 rounded-lg"
          >
            <font-awesome-icon
              :icon="['fas', 'fa-robot']"
              class="mr-2 mt-1 hidden sm:flex"
            />
            <div
              class="chat-bubble chat-bubble-secondary prose max-w-none"
              v-html="processBotMessage(log.ai_message).html"
            ></div>
          </div>
        </div>
      </div>
    </div>

    <div v-else>
      <div
        v-for="convo in conversations"
        :key="convo.conversation_id"
        @click="selectConversation(convo.conversation_id)"
        class="p-4 mb-2 rounded-lg hover:bg-base-200 cursor-pointer border border-base-200 transition-colors"
      >
        <div class="flex justify-between items-start mb-2">
          <p class="font-semibold text-lg truncate pr-4">
            {{ convo.first_message || $t("chatLogs.noMessage") }}
          </p>
          <span class="text-xs text-base-content/50 whitespace-nowrap">
            {{ new Date(convo.last_active).toLocaleString() }}
          </span>
        </div>
        <div class="flex gap-4 text-sm text-base-content/70">
          <span class="flex items-center gap-1">
            <font-awesome-icon :icon="['fas', 'comments']" />
            {{ convo.message_count }}
          </span>
          <span class="flex items-center gap-1">
            <font-awesome-icon :icon="['fas', 'coins']" />
            CHF {{ (convo.total_cost || 0).toFixed(4) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from "vue";
import { useRoute } from "vue-router";
import axios from "axios";
import { useAuthStore } from "@/stores/auth";
import { useToast } from "@/composables/useToast";
import { processBotMessage } from "@/utils/chatProcessor.js";
import { useI18n } from "vue-i18n";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:5000/api";

const route = useRoute();
const authStore = useAuthStore();
const { addToast } = useToast();
const { t } = useI18n();
const tenantId = ref(route.params.tenantId);
const conversations = ref([]);
const conversationLogs = ref([]);
const selectedConversation = ref(null);
const isLoading = ref(true);
const error = ref(null);
const chatContainer = ref(null); // Ref for the chat container DOM element

const fetchConversations = async () => {
  try {
    isLoading.value = true;
    error.value = null;
    const token = authStore.session.access_token;
    const response = await axios.get(
      `${API_BASE_URL}/chat/${tenantId.value}/conversations`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    conversations.value = response.data;
  } catch (err) {
    error.value = t("chatLogs.errors.loadConversations");
    console.error(err);
  } finally {
    isLoading.value = false;
  }
};

const selectConversation = async (conversationId) => {
  try {
    isLoading.value = true;
    error.value = null;
    selectedConversation.value = conversationId;
    const token = authStore.session.access_token;
    const response = await axios.get(
      `${API_BASE_URL}/chat/${tenantId.value}/conversation/${conversationId}`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    conversationLogs.value = response.data;

    // Wait for the DOM to update, then scroll to the bottom
    await nextTick();
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
    }
  } catch (err) {
    addToast(t("chatLogs.errors.loadLogs"), "error");
    console.error(err);
    selectedConversation.value = null; // Go back if loading fails
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  fetchConversations();
});
</script>

<style scoped>
.chat-bubble {
  hyphens: auto;
}
</style>
