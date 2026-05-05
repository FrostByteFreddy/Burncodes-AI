<template>
  <div class="space-y-6">

    <!-- Header -->
    <div>
      <h2 class="text-2xl font-bold text-base-content">Manage</h2>
      <p class="text-base-content/50 text-sm mt-1">Operational settings for this assistant — how it fetches and indexes content.</p>
    </div>

    <!-- Crawl Mode Card -->
    <div class="bg-base-100 p-6 rounded-2xl border border-base-200/50 shadow-sm space-y-5">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-secondary/10 flex items-center justify-center text-secondary">
          <font-awesome-icon :icon="['fas', 'spider']" />
        </div>
        <div>
          <h3 class="font-bold text-base-content leading-tight">Crawl Mode</h3>
          <p class="text-xs text-base-content/50">Controls how pages are fetched and chunked when you add a URL source.</p>
        </div>
      </div>

      <!-- 3-mode toggle (segmented control) -->
      <div class="inline-flex p-1 bg-base-200 rounded-xl gap-1">
        <button
          v-for="mode in crawlModes"
          :key="mode.value"
          type="button"
          @click="selectedMode = mode.value"
          class="btn btn-sm"
          :class="selectedMode === mode.value ? mode.activeClass : 'btn-ghost text-base-content/60'"
        >
          <font-awesome-icon :icon="['fas', mode.icon]" />
          {{ mode.label }}
        </button>
      </div>


      <!-- Description for selected mode -->
      <div class="text-sm text-base-content/60 bg-base-200/40 rounded-xl p-4 space-y-1">
        <p class="font-semibold text-base-content">{{ activeMode.label }}</p>
        <p>{{ activeMode.description }}</p>
        <div class="flex flex-wrap gap-2 pt-1">
          <span
            v-for="tag in activeMode.tags"
            :key="tag.text"
            class="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium"
            :class="tag.class"
          >
            <font-awesome-icon :icon="['fas', tag.icon]" class="w-2.5 h-2.5" />
            {{ tag.text }}
          </span>
        </div>
      </div>

      <!-- Save -->
      <div class="flex items-center gap-3 pt-1">
        <button
          @click="saveCrawlMode"
          :disabled="saving || selectedMode === currentSavedMode"
          class="btn btn-primary btn-sm"
        >
          <font-awesome-icon v-if="saving" :icon="['fas', 'spinner']" class="animate-spin mr-1" />
          <font-awesome-icon v-else :icon="['fas', 'floppy-disk']" class="mr-1" />
          {{ saving ? 'Saving…' : 'Save' }}
        </button>
        <span v-if="saved" class="text-success text-sm flex items-center gap-1">
          <font-awesome-icon :icon="['fas', 'check']" /> Saved
        </span>
        <span
          v-if="selectedMode !== currentSavedMode && !saved"
          class="text-xs text-base-content/40"
        >Unsaved changes</span>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useTenantsStore } from '../../stores/tenants'
import apiClient from '../../utils/api'


const tenantsStore = useTenantsStore()

const crawlModes = [
  {
    value: 'soup',
    label: 'Soup',
    icon: 'bolt',
    activeClass: 'bg-success text-success-content',
    description: 'Fetches pages with a plain HTTP request (no browser). Uses trafilatura to strip navbars, ads and boilerplate, then splits into chunks. Fast, token-free, zero Chrome overhead.',
    tags: [
      { text: 'Fastest', icon: 'bolt', class: 'bg-success/10 text-success' },
      { text: 'No tokens', icon: 'coins', class: 'bg-success/10 text-success' },
      { text: 'May miss JS content', icon: 'triangle-exclamation', class: 'bg-warning/10 text-warning' },
    ],
  },
  {
    value: 'playwright',
    label: 'Playwright',
    icon: 'globe',
    activeClass: 'bg-warning text-warning-content',
    description: 'Launches a headless Chromium browser to render JavaScript-heavy pages. Content is split with a recursive text splitter — no LLM, no tokens.',
    tags: [
      { text: 'Handles JS', icon: 'check', class: 'bg-success/10 text-success' },
      { text: 'No tokens', icon: 'coins', class: 'bg-success/10 text-success' },
      { text: 'Slower start', icon: 'clock', class: 'bg-warning/10 text-warning' },
    ],
  },
  {
    value: 'playwright_llm',
    label: 'Playwright + LLM',
    icon: 'brain',
    activeClass: 'bg-primary text-primary-content',
    description: 'Full pipeline: headless browser rendering + LLM-powered chunk cleaning. Produces the highest-quality semantic chunks. Recommended for customer-facing assistants.',
    tags: [
      { text: 'Best quality', icon: 'star', class: 'bg-primary/10 text-primary' },
      { text: 'Handles JS', icon: 'check', class: 'bg-success/10 text-success' },
      { text: 'Uses tokens', icon: 'coins', class: 'bg-error/10 text-error' },
    ],
  },
]

const selectedMode = ref(tenantsStore.currentTenant?.crawl_mode || 'playwright_llm')
const currentSavedMode = ref(tenantsStore.currentTenant?.crawl_mode || 'playwright_llm')
const saving = ref(false)
const saved = ref(false)

// Sync when tenant changes
watch(() => tenantsStore.currentTenant?.crawl_mode, (val) => {
  if (val) {
    selectedMode.value = val
    currentSavedMode.value = val
  }
})

const activeMode = computed(() => crawlModes.find(m => m.value === selectedMode.value) ?? crawlModes[2])

const saveCrawlMode = async () => {
  if (!tenantsStore.currentTenant) return
  saving.value = true
  saved.value = false
  try {
    await apiClient.put(`/tenants/${tenantsStore.currentTenant.id}`, {
      crawl_mode: selectedMode.value,
    })
    currentSavedMode.value = selectedMode.value
    tenantsStore.currentTenant.crawl_mode = selectedMode.value
    saved.value = true
    setTimeout(() => { saved.value = false }, 2500)
  } catch (e) {
    console.error('Failed to save crawl_mode', e)
  } finally {
    saving.value = false
  }
}
</script>
