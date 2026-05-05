<template>
  <div>
    <div class="flex justify-between items-center mb-8 border-b border-base-200/50 pb-6">
      <h3 class="text-2xl font-bold text-base-content flex items-center">
        <font-awesome-icon
          :icon="['fas', 'comments']"
          class="mr-3 text-primary"
        />
        {{ $t("chatLogs.title") }}
      </h3>
    </div>

    <div v-if="isLoading" class="flex justify-center items-center h-80 bg-base-100 rounded-xl border border-base-200/50 shadow-sm animate-pulse">
      <span class="loading loading-spinner text-primary loading-lg"></span>
    </div>
    
    <div v-else-if="error" class="flex justify-center items-center h-80 bg-error/10 text-error rounded-xl border border-error/20 p-6">
      <div class="text-center">
        <font-awesome-icon :icon="['fas', 'triangle-exclamation']" class="text-4xl mb-3" />
        <p class="font-bold text-lg">{{ error }}</p>
      </div>
    </div>

    <div v-else>
      <div v-if="selectedConversation" class="bg-base-100 rounded-xl p-6 shadow-sm border border-base-200/50">
        <button @click="selectedConversation = null" class="btn btn-ghost rounded-xl px-4 hover:bg-base-200 transition-colors mb-6">
          <font-awesome-icon :icon="['fas', 'arrow-left']" class="mr-2" />
          {{ $t("chatLogs.back") }}
        </button>

        <div ref="chatContainer" class="max-h-[60vh] overflow-y-auto space-y-6 px-2 scroll-smooth">
          <div v-for="log in conversationLogs" :key="log.id">
            <div v-if="log.user_message" class="chat chat-end">
              <div class="chat-bubble bg-gradient-to-r from-primary to-secondary text-primary-content shadow-md">{{ log.user_message }}</div>
            </div>
            <div v-if="log.ai_message" class="chat chat-start">
              <div class="chat-bubble bg-base-200 text-base-content shadow-sm prose max-w-none text-sm leading-relaxed"
                   v-html="processBotMessage(log.ai_message).html"></div>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="bg-base-100 rounded-xl shadow-sm border border-base-200/50 overflow-hidden">
        <div class="divide-y divide-base-200/50">
          <div
            v-for="convo in conversations"
            :key="convo.conversation_id"
            @click="selectConversation(convo.conversation_id)"
            class="flex items-center justify-between p-6 cursor-pointer hover:bg-base-200/30 transition-all duration-300 group"
          >
            <div class="min-w-0 flex-1">
              <p class="font-bold text-lg text-base-content truncate group-hover:text-primary transition-colors pb-1">{{ convo.first_message || $t("chatLogs.noMessage") }}</p>
              <div class="flex gap-6 mt-2">
                <span class="flex items-center gap-2 text-sm font-medium text-base-content/60 bg-base-200 px-3 py-1 rounded-full">
                  <font-awesome-icon :icon="['fas', 'comments']" class="text-primary/70" />
                  {{ convo.message_count }} Messages
                </span>
                <span class="flex items-center gap-2 text-sm font-medium text-base-content/60 bg-base-200 px-3 py-1 rounded-full">
                  <font-awesome-icon :icon="['fas', 'coins']" class="text-warning/70" />
                  CHF {{ (convo.total_cost || 0).toFixed(4) }}
                </span>
              </div>
            </div>
            <div class="flex items-center gap-4 ml-6 shrink-0">
              <span class="text-sm font-semibold text-base-content/40 bg-base-200/50 px-3 py-1 rounded-lg">{{ new Date(convo.last_active).toLocaleString() }}</span>
              <div class="w-10 h-10 rounded-full bg-base-200 flex items-center justify-center group-hover:bg-primary group-hover:text-primary-content transition-colors">
                <font-awesome-icon :icon="['fas', 'chevron-right']" class="w-4 h-4" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from "vue";
import apiClient from "@/utils/api";
import { useToast } from "@/composables/useToast";
import { processBotMessage } from "@/utils/chatProcessor.js";
import { useI18n } from "vue-i18n";
import { useTenantsStore } from "@/stores/tenants";

const { addToast } = useToast();
const { t } = useI18n();
const tenantsStore = useTenantsStore();

const conversations = ref([]);
const conversationLogs = ref([]);
const selectedConversation = ref(null);
const isLoading = ref(true);
const error = ref(null);
const chatContainer = ref(null);

const fetchConversations = async () => {
  if (!tenantsStore.currentTenant) return;
  try {
    isLoading.value = true;
    error.value = null;
    const response = await apiClient.get(`/chat/${tenantsStore.currentTenant.id}/conversations`);
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
    const response = await apiClient.get(
      `/chat/${tenantsStore.currentTenant.id}/conversation/${conversationId}`
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

watch(
  () => tenantsStore.currentTenant,
  (newTenant) => {
    if (newTenant) {
      selectedConversation.value = null;
      conversationLogs.value = [];
      fetchConversations();
    } else {
      conversations.value = [];
      conversationLogs.value = [];
    }
  },
  { immediate: true }
);
</script>

<style scoped>
.chat-bubble { hyphens: auto; }
</style>
