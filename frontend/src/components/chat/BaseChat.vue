<template>
  <div
    class="chat-widget"
    :class="{ 'is-widget': isWidget }"
    :style="widgetCssVariables"
  >
    <header class="chat-header">
      <div class="w-1/4 flex items-center">
        <button
          v-if="config.show_share_button"
          @click="$emit('share')"
          :disabled="!hasUserMessages"
          class="share-button btn btn-secondary btn-xs btn-square rounded-custom aspect-square"
          :class="{ 'opacity-40 cursor-not-allowed': !hasUserMessages }"
          :title="hasUserMessages ? $t('chat.share') : ''"
        >
          <font-awesome-icon :icon="['fas', 'share-nodes']" />
        </button>
      </div>
      <h1
        class="text-md font-bold text-center w-1/2 flex items-center justify-center"
      >
        <img v-if="config.logo" :src="config.logo" class="h-6 mr-2" />
        <span>{{ config.chatbot_title }}</span>
      </h1>
      <div class="w-1/4 flex justify-end items-center gap-2">
        <button
          v-if="config.show_reset_button && !isSharedView"
          @click="$emit('reset')"
          class="reset-button btn btn-secondary btn-xs btn-square rounded-custom aspect-square"
          :title="$t('chat.reset')"
        >
          <font-awesome-icon :icon="['fas', 'arrows-rotate']" />
        </button>
        <button
          v-if="!isSharedView"
          @click="$emit('close')"
          class="close-button btn btn-secondary btn-xs btn-square rounded-custom aspect-square"
          :title="$t('chat.close')"
        >
          <font-awesome-icon :icon="['fas', 'xmark']" />
        </button>
      </div>
    </header>

    <main class="chat-main" :class="{ 'chat-main--rounded-bottom': isSharedView }" ref="chatContainer">
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
            class="prose prose-neutral max-w-none bot-message-prose"
            v-html="processBotMessage(message.html)"
          ></div>

          <!-- Dates in this answer: one link that opens the visitor's own calendar app (the server picks Apple or Google) -->
          <div v-if="!message.isUser && feedsFor(message).length" class="cal">
            <a v-for="feed in feedsFor(message)" :key="feed.key" :href="feed.add || feed.webcal"
              target="_blank" rel="noopener noreferrer" class="cal__link">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="18" rx="2" /><path d="M16 2v4M8 2v4M3 10h18M12 14v4M10 16h4" /></svg>
              {{ $t('chat.calendar.add', { name: feedLabel(feed) }) }}
            </a>
          </div>
        </div>
      </div>

      <!-- Conversation starters: shown before first user message -->
      <div
        v-if="startersVisible"
        class="starters-container"
      >
        <button
          v-for="starter in config.conversation_starters"
          :key="starter.id"
          type="button"
          class="starter-chip"
          :style="getStarterStyle()"
          @click="handleStarterClick(starter)"
        >
          {{ starter.label }}
        </button>
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

    <footer v-if="!isSharedView" class="chat-footer">
      <div class="chat-input-row">
        <textarea
          ref="textareaRef"
          :value="userMessage"
          @input="onInput"
          @keyup.enter.exact.prevent="$emit('sendMessage')"
          :placeholder="config.input_placeholder || $t('chat.inputPlaceholder')"
          class="chat-input outline-none border px-4 py-3 rounded-custom"
          rows="1"
          style="resize: none; overflow-y: hidden"
        ></textarea>
        <button
          @click="$emit('sendMessage')"
          :disabled="!userMessage.trim() || isThinking"
          class="send-button font-bold btn-secondary btn-square rounded-custom aspect-square chat-send-btn"
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
  isSharedView: {
    type: Boolean,
    default: false,
  },
  /** key → calendar feed the visitor can subscribe to (from /api/calendar/<tenant>) */
  calendarFeeds: {
    type: Object,
    default: () => ({}),
  },
});

// ── Calendar subscriptions ─────────────────────────────────────────────
const feedsFor = (message) => (message.calendars || []).map((k) => props.calendarFeeds[k]).filter(Boolean);
const feedLabel = (feed) => (feed.zone ? `${feed.series} (${feed.zone})` : feed.series);

const emit = defineEmits(["update:userMessage", "sendMessage", "reset", "close", "share"]);

// Starters: show only when no user message has been sent yet
const hasUserMessages = computed(() => props.chatHistory.some(m => m.isUser));
const startersVisible = computed(() =>
  !hasUserMessages.value &&
  Array.isArray(props.config.conversation_starters) &&
  props.config.conversation_starters.length > 0
);

const getStarterStyle = () => {
  const palette = props.config.color_palette || [];
  const find = (id) => palette.find(c => c.id === id)?.value;
  return {
    backgroundColor: find(props.config.starter_background_color) || props.config.starter_background_color || '#A855F7',
    color:           find(props.config.starter_text_color)        || props.config.starter_text_color        || '#FFFFFF',
  };
};

const handleStarterClick = (starter) => {
  emit('update:userMessage', starter.label);
  nextTick(() => emit('sendMessage'));
};

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
    // the server marks where an answer comes from: [short](url "source: full title")
    const title = link.getAttribute("title") || "";
    if (title.startsWith("source:")) {
      link.classList.add("src-chip");
      link.setAttribute("title", title.slice(7).trim());
    }
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
    // Footer had no colour of its own before; it followed the header
    "--chat-footer-background-color": findColor(
      styles.footer_background_color || styles.header_background_color,
      "#F3F4F6"
    ),
    "--chat-background-color": findColor(
      styles.chat_background_color,
      "transparent"
    ),
    "--chat-reset-button-background-color": findColor(
      styles.reset_button_color,
      "#FFFFFF"
    ),
    "--chat-reset-button-icon-color": findColor(
      styles.reset_button_icon_color,
      "#1F2937"
    ),
    "--chat-close-button-background-color": findColor(
      styles.close_button_background_color,
      "#FFFFFF"
    ),
    "--chat-close-button-icon-color": findColor(
      styles.close_button_icon_color,
      "#1F2937"
    ),
    "--chat-share-button-background-color": findColor(
      styles.share_button_color,
      "#FFFFFF"
    ),
    "--chat-share-button-icon-color": findColor(
      styles.share_button_icon_color,
      "#1F2937"
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
  /* 16px base prevents iOS Safari from auto-zooming any child input on focus */
  font-size: 16px;
}

.chat-widget.is-widget {
  border-radius: 0;
  border: none;
  box-shadow: none;
  width: 100%;
  /* Falls back to 100dvh on desktop widget (iframe) mode.
     On mobile the height:100% from the parent chain takes over
     via the media query below. */
  height: 100dvh;
}

/* the dashboard's global heading colour (App.vue) must not reach the widget */
.chat-header h1 { color: inherit; }

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
  background-color: var(--chat-background-color, #ffffff);
  padding: 1rem;
  flex-grow: 1;
  overflow-y: auto;
  min-height: 0; /* required for flex children to scroll correctly */
}

.chat-main--rounded-bottom {
  border-bottom-left-radius: var(--chat-border-radius);
  border-bottom-right-radius: var(--chat-border-radius);
}

.user-message {
  background-color: var(--chat-user-message-background-color);
  border-radius: var(--chat-border-radius);
  word-break: break-word;
  overflow-wrap: anywhere;
}

.bot-message {
  background-color: var(--chat-bot-message-background-color);
  border-radius: var(--chat-border-radius);
  word-break: break-word;
  overflow-wrap: anywhere;
}

.user-message,
.user-message * {
  color: var(--chat-user-message-text-color) !important;
}

.bot-message,
.bot-message
  :is(
    p,
    h1,
    h2,
    h3,
    h4,
    h5,
    h6,
    ul,
    ol,
    li,
    blockquote,
    table,
    thead,
    tbody,
    tr,
    th,
    td,
    strong,
    em
  ) {
  color: var(--chat-bot-message-text-color) !important;
}

/* answer HTML comes in through v-html, so scoped styles need :deep */
.bot-message-prose :deep(a) {
  color: var(--chat-bot-message-text-color);
  text-decoration: underline;
  text-underline-offset: 2px;
  font-weight: 600;
}

/* where a statement comes from: an inline link with a small icon, no box */
.bot-message-prose :deep(a.src-chip) {
  font-size: 0.85em;
  font-weight: 500;
  text-decoration: underline;
  text-decoration-thickness: 1px;
  text-underline-offset: 2px;
  opacity: 0.75;
  white-space: normal;
}
.bot-message-prose :deep(a.src-chip)::before { content: "↗\00a0"; text-decoration: none; display: inline-block; }
.bot-message-prose :deep(a.src-chip:hover),
.bot-message-prose :deep(a.src-chip:focus-visible) { opacity: 1; }

.bot-message-prose :deep(a:hover) {
  opacity: 0.8;
}

.thinking-dot {
  background-color: var(--chat-bot-message-text-color);
  opacity: 0.75;
  position: relative;
  top: 3px;
}

.chat-footer {
  background-color: var(--chat-footer-background-color);
  padding: 0.75rem;
  /* Extend padding into the safe area so the home indicator / gesture bar
     never clips the input on iOS and Android. */
  padding-bottom: calc(0.75rem + env(safe-area-inset-bottom, 0px));
  border-bottom-left-radius: var(--chat-border-radius);
  border-bottom-right-radius: var(--chat-border-radius);
}

/* ── Footer input row ─────────────────────────────────────────────────────── */
.chat-input-row {
  position: relative;
  display: flex;
  align-items: flex-end;
}

.chat-input {
  background-color: var(--chat-input-background-color);
  color: var(--chat-input-text-color);
  border-color: var(--chat-footer-background-color);
  /* Full-width — button overlays on top of the right edge */
  width: 100%;
  /* Offset text from the overlaid send button */
  padding-right: 3.5rem;
}

/* Looks the same while typing: no ring, no changed corners (the dashboard's
   global :focus-visible style would otherwise apply here too) */
.chat-input:focus,
.chat-input:focus-visible {
  outline: none;
  box-shadow: none;
  border-color: var(--chat-footer-background-color);
  border-radius: var(--chat-custom-radius);
}

.chat-input::placeholder {
  color: var(--chat-input-text-color);
  opacity: 0.8;
}

.rounded-custom {
  border-radius: var(--chat-custom-radius);
}

.chat-send-btn {
  background-color: var(--chat-send-button-background-color);
  color: var(--chat-send-button-text-color);
  /* Overlay on the right side of the textarea */
  position: absolute;
  right: 0rem;
  top: 50%;
  transform: translateY(-50%);
  padding: 0.5rem;
  width: 3.1rem;
  height: 3.1rem;
  flex-shrink: 0;

  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    cursor: pointer;
  }
}

.send-button {
  background-color: var(--chat-send-button-background-color);
  color: var(--chat-send-button-text-color);
}

.reset-button {
  background-color: var(--chat-reset-button-background-color) !important;
  color: var(--chat-reset-button-icon-color) !important;
}

.close-button {
  background-color: var(--chat-close-button-background-color) !important;
  color: var(--chat-close-button-icon-color) !important;
}

.share-button {
  background-color: var(--chat-share-button-background-color) !important;
  color: var(--chat-share-button-icon-color) !important;
}

/* ── Conversation starters ────────────────────────────────────── */
.starters-container {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 8px;
  padding: 4px 0 12px;
  flex-direction: column;
  align-items: flex-end;
}

.starter-chip {
  padding: 8px 18px;
  border-radius: var(--chat-custom-radius);
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: opacity 0.15s ease, transform 0.15s ease;
  text-align: right;
  line-height: 1.4;
  white-space: wrap;
}

.starter-chip:hover {
  opacity: 0.85;
  transform: translateY(-2px);
}

.starter-chip:active {
  transform: translateY(0);
  opacity: 0.7;
}
/* ── Mobile: full-screen, percentage-based height chain ─────────────────── */
@media (max-width: 768px) {
  .chat-widget,
  .chat-widget.is-widget {
    border-radius: 0 !important;
    box-shadow: none !important;
    border: none !important;
    /* Inherit the shrunk height from html→body→#app→.chat-page.
       Do NOT use dvh/vh here — percentage propagates the keyboard-aware
       resize from interactive-widget=resizes-content correctly. */
    height: 100%;
    width: 100%;
  }

  .chat-header {
    border-top-left-radius: 0 !important;
    border-top-right-radius: 0 !important;
  }

  .chat-footer,
  .chat-main--rounded-bottom {
    border-bottom-left-radius: 0 !important;
    border-bottom-right-radius: 0 !important;
  }
}
/* ── Calendar subscription: a link, not a box ─────────────────────── */
.cal { margin-top: 8px; display: flex; flex-direction: column; align-items: flex-start; gap: 4px; }
.cal__link {
  display: inline-flex; align-items: center; gap: 6px; max-width: 100%;
  font-size: 0.875em; font-weight: 600; color: var(--chat-bot-message-text-color);
  text-decoration: underline; text-underline-offset: 2px; opacity: 0.85;
}
.cal__link:hover, .cal__link:focus-visible { opacity: 1; }
</style>
