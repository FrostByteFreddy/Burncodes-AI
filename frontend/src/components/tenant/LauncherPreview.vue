<template>
  <div
    class="flex flex-col items-center justify-center p-6 bg-base-200 rounded-lg border border-base-300"
  >
    <div class="relative">
      <!-- Mock Page Corner -->
      <div
        class="w-32 h-32 border-r-2 border-b-2 border-base-300 absolute bottom-0 right-0 pointer-events-none opacity-50"
      ></div>

      <!-- Launcher Button -->
      <div
        class="w-[60px] h-[60px] rounded-full shadow-lg flex items-center justify-center cursor-pointer transition-transform hover:scale-110 relative z-10"
        :style="{ backgroundColor: backgroundColor }"
      >
        <img
          v-if="icon"
          :src="icon"
          class="w-[30px] h-[30px] object-contain"
          alt="Launcher Icon"
        />
        <svg
          v-else
          xmlns="http://www.w3.org/2000/svg"
          width="30"
          height="30"
          viewBox="0 0 24 24"
          fill="none"
          stroke="white"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path
            d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"
          ></path>
        </svg>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  icon: {
    type: String,
    default: null,
  },
  backgroundColor: {
    type: String,
    default: "#A855F7",
  },
});
</script>
