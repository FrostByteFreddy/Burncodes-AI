<template>
  <h1 class="text-2xl font-bold mb-6">{{ $t("chatLogs.title") }}</h1>

  <div v-if="isLoading" class="flex justify-center items-center h-64">
    <span class="loading loading-spinner loading-lg"></span>
  </div>
  <div v-else-if="error" class="text-error">{{ error }}</div>

  <div v-else>
    <div v-if="selectedConversation">
      <button @click="selectedConversation = null" class="btn btn-ghost btn-sm mb-4 -ml-2">
        <font-awesome-icon :icon="['fas', 'arrow-left']" class="mr-2" />
        {{ $t("chatLogs.back") }}
      </button>

      <div ref="chatContainer" class="max-h-[70vh] overflow-y-auto space-y-4">
        <div v-for="log in conversationLogs" :key="log.id">
          <div v-if="log.user_message" class="chat chat-end">
            <div class="chat-bubble chat-bubble-primary">{{ log.user_message }}</div>
          </div>
          <div v-if="log.ai_message" class="chat chat-start">
            <div class="chat-bubble chat-bubble-secondary prose max-w-none"
                 v-html="processBotMessage(log.ai_message).html"></div>
          </div>
        </div>
      </div>
    </div>

    <div v-else>
      <div class="border-t border-base-200">
        <div
          v-for="convo in conversations"
          :key="convo.conversation_id"
          @click="selectConversation(convo.conversation_id)"
          class="flex items-center justify-between py-4 border-b border-base-200 cursor-pointer hover:bg-base-200/50 px-2 rounded transition-colors"
        >
          <div class="min-w-0 flex-1">
            <p class="font-semibold truncate">{{ convo.first_message || $t("chatLogs.noMessage") }}</p>
            <div class="flex gap-4 text-sm text-base-content/60 mt-0.5">
              <span class="flex items-center gap-1">
                <font-awesome-icon :icon="['fas', 'comments']" class="text-xs" />
                {{ convo.message_count }}
              </span>
              <span class="flex items-center gap-1">
                <font-awesome-icon :icon="['fas', 'coins']" class="text-xs" />
                CHF {{ (convo.total_cost || 0).toFixed(4) }}
              </span>
            </div>
          </div>
          <div class="flex items-center gap-3 ml-4 shrink-0">
            <span class="text-xs text-base-content/50">{{ new Date(convo.last_active).toLocaleString() }}</span>
            <font-awesome-icon :icon="['fas', 'chevron-right']" class="text-base-content/30 w-4 h-4" />
          </div>
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

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000/api";

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
const chatContainer = ref(null);

const fetchConversations = async () => {
  try {
    isLoading.value = true;
    error.value = null;
    const token = authStore.session.access_token;
    const response = await axios.get(`${API_BASE_URL}/chat/${tenantId.value}/conversations`, {
      headers: { Authorization: `Bearer ${token}` },
    });
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
      { headers: { Authorization: `Bearer ${token}` } }
    );
    conversationLogs.value = response.data;
    await nextTick();
    if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
  } catch (err) {
    addToast(t("chatLogs.errors.loadLogs"), "error");
    console.error(err);
    selectedConversation.value = null;
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => { fetchConversations(); });
</script>

<style scoped>
.chat-bubble { hyphens: auto; }
</style>
