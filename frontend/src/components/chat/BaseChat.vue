<template>
  <div
    class="chat-widget"
    :class="{ 'is-widget': isWidget }"
    :style="widgetCssVariables"
  >
    <header class="chat-header">
      <div class="w-1/4"></div>
      <h1
        class="text-md font-bold text-center w-1/2 flex items-center justify-center"
      >
        <img v-if="config.logo" :src="config.logo" class="h-6 mr-2" />
        <span>{{ config.chatbot_title }}</span>
      </h1>
      <div class="w-1/4 flex justify-end">
        <button
          v-if="config.show_reset_button"
          @click="$emit('reset')"
          class="reset-button btn btn-secondary btn-xs btn-square rounded-custom aspect-square"
        >
          <font-awesome-icon :icon="['fas', 'arrows-rotate']" />
        </button>
      </div>
    </header>

    <main class="chat-main" ref="chatContainer">
      <div
        v-for="(message, index) in chatHistory"
        :key="index"
        :class="[
          message.isUser ? 'flex justify-end' : 'flex justify-start',
          'mb-3',
        ]"
      >
        <div
          class="max-w-xl lg:max-w-2xl px-5 py-3 shadow-md"
          :class="message.isUser ? 'user-message' : 'bot-message'"
        >
          <div v-if="message.isUser" class="whitespace-pre-wrap">
            {{ message.text }}
          </div>
          <div
            v-else
            class="prose prose-sm prose-neutral max-w-none bot-message-prose"
            v-html="processBotMessage(message.html)"
          ></div>
        </div>
      </div>

      <div v-if="isThinking" class="flex justify-start">
        <div
          class="max-w-xl lg:max-w-2xl px-5 py-3 shadow-md flex items-center space-x-2 bot-message"
        >
          <font-awesome-icon
            :icon="['fas', 'spinner']"
            class="animate-spin mr-1"
          />
          <Transition name="fade-text" mode="out-in">
            <span :key="currentThinkingMessage">{{
              currentThinkingMessage
            }}</span>
          </Transition>
        </div>
      </div>
    </main>

    <footer class="chat-footer">
      <div class="flex items-end gap-3">
        <textarea
          ref="textareaRef"
          :value="userMessage"
          @input="onInput"
          @keyup.enter.exact.prevent="$emit('sendMessage')"
          :placeholder="config.input_placeholder || $t('chat.inputPlaceholder')"
          class="chat-input outline-none flex-grow border p-4 text-sm focus:outline-none focus:ring-1 rounded-custom transition-all"
          rows="1"
          style="resize: none; overflow-y: hidden"
        ></textarea>
        <button
          @click="$emit('sendMessage')"
          :disabled="!userMessage.trim() || isThinking"
          class="send-button font-bold py-2 px-4 btn-secondary btn-square rounded-custom aspect-square transition-all"
        >
          <font-awesome-icon :icon="['fas', 'paper-plane']" />
        </button>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick } from "vue";
import { useI18n } from "vue-i18n";

const { t } = useI18n();

const props = defineProps({
  config: {
    type: Object,
    required: true,
  },
  chatHistory: {
    type: Array,
    required: true,
  },
  isThinking: {
    type: Boolean,
    default: false,
  },
  userMessage: {
    type: String,
    default: "",
  },
  isWidget: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["update:userMessage", "sendMessage", "reset"]);

const chatContainer = ref(null);
const textareaRef = ref(null); // Ref for the textarea
const currentThinkingMessage = ref("");
let thinkingInterval = null;

// ADJUSTED: Randomized messages without extra fading logic
const startThinkingMessages = () => {
  const messages = props.config.thinking_messages;
  if (!messages || messages.length === 0) {
    currentThinkingMessage.value = t("chat.thinking");
    return;
  }

  // Pick a random starting message
  let currentIndex = Math.floor(Math.random() * messages.length);
  currentThinkingMessage.value = messages[currentIndex];

  if (messages.length > 1) {
    thinkingInterval = setInterval(() => {
      // Pick a new, different random index
      let newIndex = currentIndex;
      while (newIndex === currentIndex) {
        newIndex = Math.floor(Math.random() * messages.length);
      }
      currentIndex = newIndex;
      currentThinkingMessage.value = messages[currentIndex];
    }, 2000);
  }
};

// ADJUSTED: Simplified stop function
const stopThinkingMessages = () => {
  if (thinkingInterval) {
    clearInterval(thinkingInterval);
    thinkingInterval = null;
  }
};

/**
 * Resizes the textarea to fit its content.
 */
const resizeTextarea = () => {
  const textarea = textareaRef.value;
  if (textarea) {
    textarea.style.height = "auto"; // Reset height to calculate new scrollHeight
    textarea.style.height = `${textarea.scrollHeight}px`; // Set to content height
  }
};

/**
 * Handles the input event, emits the value, and resizes the textarea.
 */
const onInput = (event) => {
  emit("update:userMessage", event.target.value);
  // Wait for the DOM to update with the new value before resizing
  nextTick(resizeTextarea);
};

/**
 * Processes the bot's HTML message to make all links open in a new tab.
 * @param {string} html - The HTML content from the bot.
 * @returns {string} The modified HTML string.
 */
const processBotMessage = (html) => {
  if (!html) return "";
  // Use the browser's DOM parser to safely manipulate the HTML
  const parser = new DOMParser();
  const doc = parser.parseFromString(html, "text/html");

  // Find all anchor tags
  const links = doc.querySelectorAll("a");

  // Add target="_blank" and rel="noopener noreferrer" for security and functionality
  links.forEach((link) => {
    link.setAttribute("target", "_blank");
    link.setAttribute("rel", "noopener noreferrer");
  });

  // Return the modified HTML from the body of the parsed document
  return doc.body.innerHTML;
};

const scrollToBottom = async () => {
  await nextTick();
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
  }
};

watch(() => props.chatHistory, scrollToBottom, { deep: true });
watch(
  () => props.isThinking,
  (isThinking) => {
    scrollToBottom();
    if (isThinking) {
      startThinkingMessages();
    } else {
      stopThinkingMessages();
    }
  }
);

watch(
  () => props.userMessage,
  (newValue) => {
    // Reset textarea height when message is cleared
    if (newValue === "" && textareaRef.value) {
      textareaRef.value.style.height = "auto";
    }
  }
);

const widgetCssVariables = computed(() => {
  const config = props.config;
  if (!config) return {};

  const styles = config.component_styles || {};
  const palette = config.color_palette || [];
  const findColor = (colorId, fallback = "#000000") =>
    palette.find((c) => c.id === colorId)?.value || fallback;

  return {
    "--chat-header-background-color": findColor(
      styles.header_background_color,
      "#F3F4F6"
    ),
    "--chat-header-text-color": findColor(styles.header_text_color, "#1F2937"),
    "--chat-user-message-background-color": findColor(
      styles.user_message_background_color,
      "#A855F7"
    ),
    "--chat-user-message-text-color": findColor(
      styles.user_message_text_color,
      "#FFFFFF"
    ),
    "--chat-bot-message-background-color": findColor(
      styles.bot_message_background_color,
      "#F3F4F6"
    ),
    "--chat-bot-message-text-color": findColor(
      styles.bot_message_text_color,
      "#1F2937"
    ),
    "--chat-send-button-background-color": findColor(
      styles.send_button_background_color,
      "#A855F7"
    ),
    "--chat-send-button-text-color": findColor(
      styles.send_button_text_color,
      "#FFFFFF"
    ),
    "--chat-input-background-color": findColor(
      styles.input_background_color,
      "#F9FAFB"
    ),
    "--chat-input-text-color": findColor(styles.input_text_color, "#1F2937"),
    "--chat-input-focus-ring-color": findColor(
      styles.input_focus_ring_color,
      "#A855F7"
    ),
    "--chat-background-color": findColor(
      styles.chat_background_color,
      "#FFFFFF"
    ),
    "--chat-reset-button-background-color": findColor(
      styles.reset_button_color,
      "#FFFFFF"
    ),
    "--chat-border-radius": "32px",
    "--chat-custom-radius": "22px",
  };
});
</script>

<style scoped>
.chat-widget {
  border-radius: var(--chat-border-radius);
  overflow: hidden;
  border: 1px solid #e5e7eb;
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-widget.is-widget {
  border-radius: 0;
  border: none;
  box-shadow: none;
  width: 100%;
  height: 100vh;
}

.chat-header {
  background-color: var(--chat-header-background-color);
  color: var(--chat-header-text-color);
  padding: 0.75rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top-left-radius: var(--chat-border-radius);
  border-top-right-radius: var(--chat-border-radius);
}

.chat-main {
  background-color: var(--chat-background-color);
  padding: 1rem;
  flex-grow: 1;
  overflow-y: auto;
  height: 400px;
}

.user-message {
  background-color: var(--chat-user-message-background-color);
  border-radius: var(--chat-border-radius);
  font-size: 0.875rem; /* Same as .prose */
}

.bot-message {
  background-color: var(--chat-bot-message-background-color);
  border-radius: var(--chat-border-radius);
  font-size: 0.875rem; /* Same as .prose */
}

.user-message,
.user-message * {
  color: var(--chat-user-message-text-color) !important;
}

.bot-message,
.bot-message * {
  color: var(--chat-bot-message-text-color) !important;
}

.bot-message-prose a {
  color: var(--chat-bot-message-text-color);
  text-decoration: underline;
}

.bot-message-prose a:hover {
  opacity: 0.8;
}

.thinking-dot {
  background-color: var(--chat-bot-message-text-color);
  opacity: 0.75;
  position: relative;
  top: 3px;
}

.chat-footer {
  background-color: var(--chat-header-background-color);
  padding: 0.75rem;
  border-bottom-left-radius: var(--chat-border-radius);
  border-bottom-right-radius: var(--chat-border-radius);
}

.chat-input {
  background-color: var(--chat-input-background-color);
  color: var(--chat-input-text-color);
  border-color: var(--chat-header-background-color);
  --tw-ring-color: var(--chat-input-focus-ring-color);
}

.chat-input::placeholder {
  color: var(--chat-input-text-color);
  opacity: 0.8;
}

.rounded-custom {
  border-radius: var(--chat-custom-radius);
}
.send-button {
  background-color: var(--chat-send-button-background-color);
  color: var(--chat-send-button-text-color);
}

.reset-button {
  background-color: var(--chat-reset-button-background-color) !important;
  color: var(--chat-header-text-color) !important;
}
</style>
