<template>
  <div
    v-if="show"
    class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60"
  >
    <div class="bg-base-100 rounded-lg shadow-xl p-8 max-w-md w-full">
      <h2 class="text-2xl font-bold mb-4 flex items-center">
        <font-awesome-icon
          :icon="['fas', 'triangle-exclamation']"
          class="mr-3 text-error"
        />
        {{ title }}
      </h2>
      <p class="text-base-content/70 mb-6">{{ message }}</p>

      <div v-if="confirmationText">
        <label class="block text-sm font-medium text-base-content/70 mb-2">
          {{
            $t("modals.confirmation.typeToConfirm", { text: confirmationText })
          }}
        </label>
        <input
          v-model="userInput"
          type="text"
          class="w-full px-3 py-2 bg-base-200 border border-base-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>

      <div class="flex justify-end mt-8 space-x-4">
        <button @click="onCancel" class="btn btn-secondary">
          <font-awesome-icon :icon="['fas', 'times']" class="mr-2" />
          {{ $t("modals.confirmation.cancel") }}
        </button>
        <button
          @click="onConfirm"
          :disabled="isConfirmDisabled"
          class="btn btn-error"
        >
          <font-awesome-icon :icon="['fas', 'check']" class="mr-2" />
          {{ confirmButtonText || $t("modals.confirmation.confirm") }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, defineProps, defineEmits } from "vue";

const props = defineProps({
  show: Boolean,
  title: {
    type: String,
    required: true,
  },
  message: {
    type: String,
    required: true,
  },
  confirmationText: {
    type: String,
    default: "",
  },
  confirmButtonText: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["confirm", "cancel"]);

const userInput = ref("");

const isConfirmDisabled = computed(() => {
  if (!props.confirmationText) return false;
  return userInput.value !== props.confirmationText;
});

const onConfirm = () => {
  if (!isConfirmDisabled.value) {
    emit("confirm");
  }
};

const onCancel = () => {
  emit("cancel");
};
</script>
