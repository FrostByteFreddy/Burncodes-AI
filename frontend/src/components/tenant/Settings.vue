<template>
  <div>
    <div class="inline-flex p-1 space-x-1 bg-base-200 rounded-full mb-6">
      <a
        class="btn border-0 rounded-full hover:cursor-pointer space-x-2"
        :class="{
 '!bg-primary-focus text-primary-content shadow':
 activeTab === 'behavior',
 'btn-ghost text-base-content': activeTab !== 'behavior',
 }"
        @click="activeTab = 'behavior'"
      >
        <font-awesome-icon :icon="['fas', 'fa-brain']" />
        <span>{{ $t("tenant.settings.tabs.behavior") }}</span>
      </a>
      <a
        class="btn border-0 rounded-full hover:cursor-pointer space-x-2"
        :class="{
 '!bg-primary-focus text-primary-content shadow':
 activeTab === 'appearance',
 'btn-ghost text-base-content': activeTab !== 'appearance',
 }"
        @click="activeTab = 'appearance'"
      >
        <font-awesome-icon :icon="['fas', 'fa-palette']" />
        <span>{{ $t("tenant.settings.tabs.appearance") }}</span>
      </a>
      <a
        class="btn border-0 rounded-full hover:cursor-pointer space-x-2"
        :class="{
 '!bg-primary-focus text-primary-content shadow':
 activeTab === 'rules',
 'btn-ghost text-base-content': activeTab !== 'rules',
 }"
        @click="activeTab = 'rules'"
      >
        <font-awesome-icon :icon="['fas', 'wand-magic-sparkles']" />
        <span>{{ $t("tenant.fineTune.title") }}</span>
      </a>
    </div>

    <form @submit.prevent="handleUpdate" class="space-y-6 mt-6">
      <div v-show="activeTab === 'behavior'" class="space-y-8">
        
        <!-- General Information Card -->
        <div class="bg-base-100 p-6 rounded-xl border border-base-200/50 shadow-sm">
          <h3 class="text-xl font-bold text-base-content mb-6 flex items-center">
            <font-awesome-icon :icon="['fas', 'info-circle']" class="mr-3 text-primary" />
            General Information
          </h3>
          <div class="space-y-6">
            <div>
              <label
                for="name"
                class="block text-sm font-medium text-base-content"
                >{{ $t("tenant.settings.behavior.name") }}</label
              >
              <input
                v-model="formData.name"
                type="text"
                id="name"
                required
                class="w-full p-3 mt-1 bg-base-200 border-none rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow"
              />
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label
                  for="doc_language"
                  class="block text-sm font-medium text-base-content"
                  >{{ $t("tenant.settings.behavior.docLanguage") }}</label
                >
                <select
                  v-model="formData.doc_language"
                  id="doc_language"
                  class="w-full p-3 mt-1 bg-base-200 border-none rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow"
                >
                  <option
                    v-for="lang in languageOptions"
                    :key="lang.value"
                    :value="lang.value"
                  >
                    {{ lang.text }}
                  </option>
                </select>
              </div>
              <div>
                <label
                  for="translation_target"
                  class="block text-sm font-medium text-base-content"
                  >{{ $t("tenant.settings.behavior.translationTarget") }}</label
                >
                <select
                  v-model="formData.translation_target"
                  id="translation_target"
                  class="w-full p-3 mt-1 bg-base-200 border-none rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow"
                >
                  <option
                    v-for="lang in languageOptions"
                    :key="lang.value"
                    :value="lang.value"
                  >
                    {{ lang.text }}
                  </option>
                </select>
              </div>
            </div>

            <!-- Crawl Mode -->
            <div class="pt-2">
              <label class="block text-sm font-medium text-base-content mb-2">Crawl Mode</label>
              <p class="text-xs text-base-content/50 mb-3">
                Controls how pages are fetched and processed when you add a URL source.
              </p>
              <div class="inline-flex p-1 bg-base-200 rounded-xl gap-1">
                <button
                  type="button"
                  @click="formData.crawl_mode = 'soup'; handleUpdate()"
                  class="px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200"
                  :class="formData.crawl_mode === 'soup' ? 'bg-success text-success-content shadow-sm' : 'text-base-content/60 hover:text-base-content'"
                >
                  <font-awesome-icon :icon="['fas', 'bolt']" class="mr-2" />
                  Soup
                </button>
                <button
                  type="button"
                  @click="formData.crawl_mode = 'playwright'; handleUpdate()"
                  class="px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200"
                  :class="formData.crawl_mode === 'playwright' ? 'bg-warning text-warning-content shadow-sm' : 'text-base-content/60 hover:text-base-content'"
                >
                  <font-awesome-icon :icon="['fas', 'globe']" class="mr-2" />
                  Playwright
                </button>
                <button
                  type="button"
                  @click="formData.crawl_mode = 'playwright_llm'; handleUpdate()"
                  class="px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200"
                  :class="formData.crawl_mode === 'playwright_llm' ? 'bg-primary text-primary-content shadow-sm' : 'text-base-content/60 hover:text-base-content'"
                >
                  <font-awesome-icon :icon="['fas', 'brain']" class="mr-2" />
                  Playwright + LLM
                </button>
              </div>
              <p class="text-xs text-base-content/40 mt-2">
                <span v-if="formData.crawl_mode === 'soup'">⚡ httpx + trafilatura — fastest, no browser, no tokens. May miss JS-rendered content.</span>
                <span v-else-if="formData.crawl_mode === 'playwright'">🌐 Headless browser, handles JS sites. Raw text splitter, no tokens.</span>
                <span v-else>🧠 Headless browser + LLM cleaning. Best chunk quality, uses tokens.</span>
              </p>
            </div>
          </div>
        </div>

        <!-- AI Persona & Role Card -->
        <div class="bg-base-100 p-6 rounded-xl border border-base-200/50 shadow-sm">
          <h3 class="text-xl font-bold text-base-content mb-6 flex items-center">
            <font-awesome-icon :icon="['fas', 'user-astronaut']" class="mr-3 text-primary" />
            AI Persona & Role
          </h3>
          <div class="space-y-6">
            <div>
              <label
                for="intro_message"
                class="block text-sm font-medium text-base-content"
                >{{ $t("tenant.settings.behavior.introMessage") }}</label
              >
              <AutoGrowTextarea
                v-model="formData.intro_message"
                id="intro_message"
                rows="3"
                class="w-full p-3 mt-1 bg-base-200 border-none rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow resize-none"
              />
            </div>
            <div>
              <label
                for="system_persona"
                class="block text-sm font-medium text-base-content"
                >{{ $t("tenant.settings.behavior.systemPersona") }}</label
              >
              <AutoGrowTextarea
                v-model="formData.system_persona"
                id="system_persona"
                rows="5"
                class="w-full p-3 mt-1 bg-base-200 border-none rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow resize-none"
              />
            </div>
          </div>
        </div>

        <!-- Advanced RAG Configuration Card -->
        <div class="bg-base-100 p-6 rounded-xl border border-base-200/50 shadow-sm">
          <h3 class="text-xl font-bold text-base-content mb-6 flex items-center">
            <font-awesome-icon :icon="['fas', 'brain']" class="mr-3 text-primary" />
            Advanced RAG Configuration
          </h3>
          <div class="space-y-6">
            <div>
              <label
                for="rag_prompt_template"
                class="block text-sm font-medium text-base-content"
                >{{ $t("tenant.settings.behavior.ragPromptTemplate") }}</label
              >
              <AutoGrowTextarea
                v-model="formData.rag_prompt_template"
                id="rag_prompt_template"
                rows="8"
                class="w-full p-3 mt-1 bg-base-200 border-none rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow font-mono text-sm resize-none"
              />
            </div>
          </div>
        </div>
      </div>

      <div v-show="activeTab === 'appearance'" @change="handleUpdate">
        <div class="space-y-8">
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div class="space-y-8">

              <!-- Color Palette — swatch strip -->
              <div class="bg-base-100 p-6 rounded-xl border border-base-200/50 shadow-sm">
                <h3 class="text-xl font-bold text-base-content mb-4 flex items-center">
                  <font-awesome-icon :icon="['fas', 'palette']" class="mr-3 text-primary" />
                  {{ $t('tenant.settings.appearance.colorPalette.title') }}
                </h3>
                <p class="text-sm text-base-content/70 mb-4">
                  {{ $t('tenant.settings.appearance.colorPalette.description') }}
                </p>
                <!-- Swatch grid -->
                <div class="flex flex-wrap gap-3">
                  <div
                    v-for="(color, index) in formData.widget_config.color_palette"
                    :key="color.id"
                    class="relative group flex flex-col items-center gap-1.5"
                  >
                    <!-- Colour swatch — clicking opens native color picker -->
                    <label class="relative cursor-pointer block">
                      <span
                        class="block w-12 h-12 rounded-xl shadow-sm ring-1 ring-black/10 transition-transform group-hover:scale-105"
                        :style="{ backgroundColor: color.value }"
                      />
                      <input
                        v-model="color.value"
                        type="color"
                        class="absolute inset-0 opacity-0 w-full h-full cursor-pointer"
                      />
                      <!-- Delete badge (custom colors only) -->
                      <button
                        v-if="index > 1"
                        type="button"
                        @click.prevent.stop="removeColor(color.id)"
                        class="absolute -top-1.5 -right-1.5 w-4 h-4 bg-error text-white rounded-full hidden group-hover:flex items-center justify-center leading-none"
                        style="font-size:10px;"
                      >×</button>
                    </label>
                    <!-- Editable name beneath swatch -->
                    <input
                      v-model="color.name"
                      type="text"
                      :disabled="index < 2"
                      class="w-12 text-xs text-center bg-transparent border-none focus:outline-none focus:ring-1 focus:ring-primary/50 rounded p-0 disabled:cursor-default"
                    />
                  </div>

                  <!-- Add-new ghost swatch -->
                  <div class="flex flex-col items-center gap-1.5">
                    <button
                      type="button"
                      @click.prevent="addColor"
                      class="w-12 h-12 rounded-xl border-2 border-dashed border-base-300 flex items-center justify-center text-base-content/30 hover:border-primary/50 hover:text-primary/50 transition-colors"
                    >
                      <font-awesome-icon :icon="['fas', 'plus']" />
                    </button>
                    <span class="w-12 text-xs text-center text-base-content/30">Add</span>
                  </div>
                </div>
              </div>

              <!-- Chat Window Card -->
              <div class="bg-base-100 p-6 rounded-xl border border-base-200/50 shadow-sm">
                <h3 class="text-xl font-bold text-base-content mb-6 flex items-center">
                  <font-awesome-icon :icon="['fas', 'comment-dots']" class="mr-3 text-primary" />
                  {{ $t("tenant.settings.appearance.chatWindow.title") }}
                </h3>
                <div class="space-y-4">
                  <div>
                    <label
                      for="chatbot_title"
                      class="block text-sm font-medium text-base-content"
                      >{{
                        $t("tenant.settings.appearance.chatWindow.chatbotTitle")
                      }}</label
                    >
                    <input
                      v-model="formData.widget_config.chatbot_title"
                      type="text"
                      id="chatbot_title"
                      class="w-full p-3 mt-1 bg-base-200 border-none rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow"
                    />
                  </div>
                  <div>
                    <label for="logo" class="block text-sm font-medium text-base-content">{{
                      $t("tenant.settings.appearance.chatWindow.logo")
                    }}</label>
                    <div class="flex items-center space-x-2 mt-1">
                      <input
                        @change="handleFileUpload($event, 'logo')"
                        type="file"
                        id="logo"
                        class="w-full p-2 bg-base-200 border-none rounded-xl file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
                        accept="image/*,.svg"
                      />
                      <button
                        v-if="formData.widget_config.logo"
                        @click.prevent="removeFile('logo')"
                        class="btn btn-square btn-ghost text-error hover:bg-error/10"
                        :title="
                          $t('tenant.settings.appearance.chatWindow.removeLogo')
                        "
                      >
                        <font-awesome-icon :icon="['fas', 'trash']" />
                      </button>
                    </div>
                    <img
                      v-if="formData.widget_config.logo"
                      :src="formData.widget_config.logo"
                      class="mt-4 max-h-20 rounded-lg shadow-sm"
                    />
                  </div>
                  <div class="flex items-center">
                    <input
                      v-model="formData.widget_config.show_reset_button"
                      type="checkbox"
                      id="show_reset_button"
                      class="h-4 w-4 rounded border-base-200 text-primary focus:ring-primary/50 bg-base-200"
                    />
                    <label for="show_reset_button" class="ml-2 block text-sm text-base-content">{{
                      $t(
                        "tenant.settings.appearance.chatWindow.showResetButton"
                      )
                    }}</label>
                  </div>
                  <div>
                    <label
                      for="input_placeholder"
                      class="block text-sm font-medium text-base-content"
                      >{{
                        $t(
                          "tenant.settings.appearance.chatWindow.inputPlaceholder"
                        )
                      }}</label
                    >
                    <input
                      v-model="formData.widget_config.input_placeholder"
                      type="text"
                      id="input_placeholder"
                      class="w-full p-3 mt-1 bg-base-200 border-none rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow"
                    />
                  </div>
                  <div>
                    <label
                      for="thinking_messages"
                      class="block text-sm font-medium text-base-content"
                      >{{
                        $t(
                          "tenant.settings.appearance.chatWindow.thinkingMessages"
                        )
                      }}</label
                    >
                    <AutoGrowTextarea
                      v-model="thinkingMessages"
                      id="thinking_messages"
                      class="w-full p-3 mt-1 bg-base-200 border-none rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow resize-none"
                      rows="3"
                      :placeholder="
                        $t(
                          'tenant.settings.appearance.chatWindow.thinkingPlaceholder'
                        )
                      "
                    />
                  </div>
                </div>
              </div>

              <!-- Component Styles Card -->
              <div class="bg-base-100 p-6 rounded-xl border border-base-200/50 shadow-sm">
                <h3 class="text-xl font-bold text-base-content mb-6 flex items-center">
                  <font-awesome-icon :icon="['fas', 'swatchbook']" class="mr-3 text-primary" />
                  {{ $t("tenant.settings.appearance.componentStyles.title") }}
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
                  <div
                    v-for="(label, key) in filteredComponentStyleLabels"
                    :key="key"
                  >
                    <label :for="key" class="block text-sm font-medium text-base-content">{{
                      label
                    }}</label>
                    <select
                      v-model="formData.widget_config.component_styles[key]"
                      :id="key"
                      class="w-full p-3 mt-1 bg-base-200 border-none rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow"
                    >
                      <option
                        v-for="color in formData.widget_config.color_palette"
                        :key="color.id"
                        :value="color.id"
                      >
                        {{ color.name }}
                      </option>
                    </select>
                  </div>
                </div>
              </div>

              <!-- Launcher Card -->
              <div class="bg-base-100 p-6 rounded-xl border border-base-200/50 shadow-sm">
                <h3 class="text-xl font-bold text-base-content mb-6 flex items-center">
                  <font-awesome-icon :icon="['fas', 'rocket']" class="mr-3 text-primary" />
                  {{ $t("tenant.settings.appearance.launcher.title") }}
                </h3>
                <div class="space-y-6">
                  <div>
                    <label
                      for="launcher_icon"
                      class="block text-sm font-medium text-base-content"
                      >{{
                        $t("tenant.settings.appearance.launcher.icon")
                      }}</label
                    >
                    <div class="flex items-center space-x-2 mt-1">
                      <input
                        @change="handleFileUpload($event, 'launcher_icon')"
                        type="file"
                        id="launcher_icon"
                        class="w-full p-2 bg-base-200 border-none rounded-xl file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
                        accept="image/*,.svg"
                      />
                      <button
                        v-if="formData.widget_config.launcher_icon"
                        @click.prevent="removeFile('launcher_icon')"
                        class="btn btn-square btn-ghost text-error hover:bg-error/10"
                        :title="
                          $t('tenant.settings.appearance.launcher.removeIcon')
                        "
                      >
                        <font-awesome-icon :icon="['fas', 'trash']" />
                      </button>
                    </div>
                    <div
                      v-if="formData.widget_config.launcher_icon"
                      class="mt-4"
                    >
                      <p class="text-xs text-base-content/50 mb-2">
                        {{
                          $t("tenant.settings.appearance.launcher.currentIcon")
                        }}
                      </p>
                      <img
                        :src="formData.widget_config.launcher_icon"
                        class="w-12 h-12 rounded-full object-cover shadow-sm bg-base-200 p-1"
                      />
                    </div>
                  </div>

                  <div>
                    <label
                      for="launcher_background_color"
                      class="block text-sm font-medium text-base-content"
                      >{{
                        $t(
                          "tenant.settings.appearance.launcher.backgroundColor"
                        )
                      }}</label
                    >
                    <select
                      v-model="
                        formData.widget_config.component_styles
                          .launcher_background_color
                      "
                      id="launcher_background_color"
                      class="w-full p-3 mt-1 bg-base-200 border-none rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow"
                    >
                      <option
                        v-for="color in formData.widget_config.color_palette"
                        :key="color.id"
                        :value="color.id"
                      >
                        {{ color.name }}
                      </option>
                    </select>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <div class="lg:sticky top-8 space-y-6">
                <div>
                  <h3 class="text-lg font-bold mb-4">
                    {{ $t("tenant.settings.appearance.preview.title") }}
                  </h3>

                  <div>
                    <h4 class="text-sm font-medium text-base-content/70 mb-2">
                      {{ $t("tenant.settings.appearance.preview.chatWindow") }}
                    </h4>
                    <ChatPreview
                      :tenantId="tenantsStore.currentTenant.id"
                      :key="previewKey"
                    />
                  </div>

                  <div class="mb-4">
                    <h4 class="text-sm font-medium text-base-content/70 mb-2">
                      {{ $t("tenant.settings.appearance.preview.launcher") }}
                    </h4>
                    <LauncherPreview
                      :icon="formData.widget_config.launcher_icon"
                      :background-color="
                        getPaletteColor(
                          formData.widget_config.component_styles
                            .launcher_background_color
                        )
                      "
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ── Installation Script — always at the bottom ── -->
          <div class="bg-base-100 p-6 rounded-xl border border-base-200/50 shadow-sm mt-2">
            <h3 class="text-xl font-bold text-base-content mb-4 flex items-center">
              <font-awesome-icon :icon="['fas', 'code']" class="mr-3 text-primary" />
              {{ $t('tenant.settings.appearance.installation.title') }}
            </h3>
            <p class="text-sm text-base-content/70 mb-4">
              {{ $t('tenant.settings.appearance.installation.instruction') }}
            </p>
            <div class="relative">
              <pre class="bg-base-200/50 p-4 rounded-lg overflow-x-auto text-sm font-mono text-base-content border border-base-200"><code>&lt;script src="{{ apiUrl }}/tenants/widget.js" data-tenant-id="{{ tenantsStore.currentTenant?.id }}"&gt;&lt;/script&gt;</code></pre>
              <button
                @click.prevent="copyScript"
                class="absolute top-2 right-2 btn btn-sm btn-ghost text-primary hover:bg-base-300"
              >
                <font-awesome-icon :icon="['fas', 'copy']" />
                <span class="ml-1">{{ $t('tenant.settings.appearance.installation.copy') }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Rules tab (absorbed from FineTune.vue) ─────────────── -->
      <div v-show="activeTab === 'rules'">
        <div class="flex justify-between items-center mb-8 border-b border-base-200/50 pb-6">
          <h3 class="text-2xl font-bold text-base-content flex items-center">
            <font-awesome-icon :icon="['fas', 'wand-magic-sparkles']" class="mr-3 text-primary" />
            {{ $t("tenant.fineTune.title") }}
          </h3>
          <button type="button" @click="isRulesModalOpen = true" class="btn btn-primary">
            <font-awesome-icon :icon="['fas', 'plus']" />
            {{ $t("tenant.fineTune.addRule") || 'Add Rule' }}
          </button>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div
            v-for="(rule, index) in rules"
            :key="index"
            :class="[
              'p-6 rounded-xl flex flex-col transition-all duration-300 shadow-sm',
              rule.isEditing
                ? 'bg-base-100 ring-2 ring-primary shadow-lg border-transparent relative z-10'
                : 'bg-base-100 border border-base-200/50 hover:shadow-md hover:border-base-300/50',
            ]"
          >
            <div class="flex-grow space-y-4">
              <input
                v-model="rule.trigger"
                type="text"
                :id="`trigger-${index}`"
                :placeholder="$t('tenant.fineTune.trigger.placeholder')"
                :disabled="!rule.isEditing"
                :class="[
                  'w-full p-3 mt-1 rounded-xl text-lg font-bold focus:outline-none transition-shadow',
                  rule.isEditing
                    ? 'bg-base-200 border-none focus:ring-2 focus:ring-primary/50'
                    : 'bg-transparent border-transparent text-base-content px-0',
                ]"
              />
              <div>
                <AutoGrowTextarea
                  v-model="rule.instruction"
                  :id="`instruction-${index}`"
                  rows="1"
                  :placeholder="$t('tenant.fineTune.instruction.placeholder')"
                  :disabled="!rule.isEditing"
                  :class="[
                    'w-full p-3 mt-1 rounded-xl focus:outline-none transition-shadow',
                    rule.isEditing
                      ? 'bg-base-200 border-none focus:ring-2 focus:ring-primary/50'
                      : 'bg-transparent border-transparent text-base-content/70 px-0 resize-none',
                  ]"
                />
              </div>
            </div>
            <div class="flex justify-end items-center pt-3 mt-auto space-x-1">
              <template v-if="rule.isEditing">
                <button type="button" @click="saveEditedRule(rule)" class="btn btn-ghost btn-xs text-success">
                  <font-awesome-icon :icon="['fas', 'check']" class="h-4 w-4" />
                </button>
                <button type="button" @click="cancelEditing(index)" class="btn btn-ghost btn-xs">
                  <font-awesome-icon :icon="['fas', 'xmark']" class="h-4 w-4" />
                </button>
              </template>
              <template v-else>
                <button type="button" @click="startEditing(rule, index)" class="btn btn-ghost btn-xs">
                  <font-awesome-icon :icon="['fas', 'pen']" class="h-4 w-4" />
                </button>
                <button type="button" @click="removeRule(index)" class="btn btn-ghost btn-xs text-error">
                  <font-awesome-icon :icon="['fas', 'trash']" class="h-4 w-4" />
                </button>
              </template>
            </div>
          </div>
        </div>

        <p v-if="rules.length === 0" class="text-base-content/50 text-center py-8">
          {{ $t("tenant.fineTune.noRules") }}
        </p>

        <!-- Add Rule Modal -->
        <Transition name="fade">
          <div
            v-if="isRulesModalOpen"
            class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
            @click="closeRulesModal"
          >
            <div
              class="bg-base-100 rounded-2xl shadow-2xl w-full max-w-md p-6 sm:p-8 m-4 border border-base-200/50"
              @click.stop
            >
              <div class="flex justify-between items-center mb-6 border-b border-base-200/50 pb-4">
                <h3 class="text-xl font-bold text-base-content">{{ $t("tenant.fineTune.addRule") }}</h3>
                <button type="button" @click="closeRulesModal" class="btn btn-ghost btn-circle btn-sm">
                  <font-awesome-icon :icon="['fas', 'xmark']" class="h-4 w-4" />
                </button>
              </div>
              <form @submit.prevent="addRule" class="space-y-6">
                <div>
                  <label for="new-trigger" class="block text-sm font-medium text-base-content mb-2">{{ $t("tenant.fineTune.trigger.label") }}</label>
                  <input v-model="newRule.trigger" type="text" id="new-trigger" :placeholder="$t('tenant.fineTune.trigger.example')" class="w-full p-3 bg-base-200 border-none rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow" />
                </div>
                <div>
                  <label for="new-instruction" class="block text-sm font-medium text-base-content mb-2">{{ $t("tenant.fineTune.instruction.label") }}</label>
                  <AutoGrowTextarea v-model="newRule.instruction" id="new-instruction" rows="3" :placeholder="$t('tenant.fineTune.instruction.example')" class="w-full p-3 bg-base-200 border-none rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 transition-shadow resize-none" />
                </div>
                <div class="flex justify-end pt-4 space-x-3 border-t border-base-200/50 mt-6">
                  <button type="button" @click="closeRulesModal" class="btn btn-ghost">{{ $t("tenant.fineTune.actions.cancel") }}</button>
                  <button type="submit" class="btn btn-primary">{{ $t("tenant.fineTune.actions.add") }}</button>
                </div>
              </form>
            </div>
          </div>
        </Transition>
      </div>

    </form>
  </div>
</template>

<script setup>
import { ref, watch, computed } from "vue";
import { useTenantsStore } from "../../stores/tenants";
import { useToast } from "../../composables/useToast";
import AutoGrowTextarea from "../AutoGrowTextarea.vue";
import { v4 as uuidv4 } from "uuid";
import ChatPreview from "./ChatPreview.vue";
import LauncherPreview from "./LauncherPreview.vue";
import { useI18n } from "vue-i18n";

const { t } = useI18n();
const tenantsStore = useTenantsStore();
const { addToast } = useToast();
const activeTab = ref("behavior");
const previewKey = ref(0);

// ── Rules (FineTune) state ───────────────────────────────────────────────────
const isRulesModalOpen = ref(false);
const rules = ref([]);
const newRule = ref({ trigger: '', instruction: '' });
let originalRuleState = null;

watch(
  () => tenantsStore.currentTenant,
  (newTenant) => {
    if (newTenant && newTenant.fine_tune_rules) {
      rules.value = JSON.parse(JSON.stringify(newTenant.fine_tune_rules)).map(
        (rule) => ({ ...rule, isEditing: false })
      );
    } else {
      rules.value = [];
    }
  },
  { immediate: true, deep: true }
);

const startEditing = (rule) => {
  originalRuleState = JSON.parse(JSON.stringify(rule));
  rule.isEditing = true;
};
const cancelEditing = (index) => {
  if (originalRuleState) {
    rules.value[index] = originalRuleState;
    rules.value[index].isEditing = false;
    originalRuleState = null;
  }
};
const saveEditedRule = async (rule) => {
  rule.isEditing = false;
  originalRuleState = null;
  await saveRules();
};
const closeRulesModal = () => {
  isRulesModalOpen.value = false;
  newRule.value = { trigger: '', instruction: '' };
};
const saveRules = async () => {
  if (tenantsStore.currentTenant) {
    const rulesToSave = rules.value.map(({ isEditing, ...rest }) => rest);
    try {
      await tenantsStore.updateTenant(tenantsStore.currentTenant.id, { fine_tune_rules: rulesToSave });
      addToast(t('tenant.fineTune.actions.saveSuccess'), 'success');
      return true;
    } catch {
      addToast(t('tenant.fineTune.actions.saveFailed'), 'error');
      return false;
    }
  }
  return false;
};
const addRule = async () => {
  if (newRule.value.trigger.trim() && newRule.value.instruction.trim()) {
    rules.value.push({ ...newRule.value, isEditing: false });
    const success = await saveRules();
    if (success) closeRulesModal();
    else rules.value.pop();
  }
};
const removeRule = async (index) => {
  const backup = rules.value[index];
  rules.value.splice(index, 1);
  const success = await saveRules();
  if (!success) rules.value.splice(index, 0, backup);
};
// ────────────────────────────────────────────────────────────────────────────

const apiUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

const languageOptions = computed(() => [
  { value: "de", text: "Deutsch" },
  { value: "en", text: "English" },
  { value: "fr", text: "Français" },
]);

const defaultWidgetConfig = () => ({
  chatbot_title: "",
  logo: null,
  launcher_icon: null,
  show_reset_button: true,
  input_placeholder: "Send a message...",
  thinking_messages: [
    "Thinking...",
    "Just a moment...",
    "Let me check that for you...",
  ],
  color_palette: [
    {
      id: "c_white",
      name: t("tenant.settings.defaults.white"),
      value: "#FFFFFF",
    },
    {
      id: "c_black",
      name: t("tenant.settings.defaults.black"),
      value: "#1F2937",
    },
    {
      id: "c_primary",
      name: t("tenant.settings.defaults.primary"),
      value: "#A855F7",
    },
    {
      id: "c_secondary",
      name: t("tenant.settings.defaults.secondary"),
      value: "#F3F4F6",
    },
  ],
  component_styles: {
    header_background_color: "c_secondary",
    header_text_color: "c_black",
    user_message_background_color: "c_primary",
    user_message_text_color: "c_white",
    bot_message_background_color: "c_secondary",
    bot_message_text_color: "c_black",
    send_button_background_color: "c_primary",
    send_button_text_color: "c_white",
    input_background_color: "c_secondary",
    input_text_color: "c_black",
    input_focus_ring_color: "c_primary",
    chat_background_color: "c_white",
    reset_button_color: "c_primary",
    launcher_background_color: "c_primary",
  },
});

const formData = ref({
  name: "",
  intro_message: "",
  system_persona: "",
  rag_prompt_template: "",
  doc_language: "en",
  translation_target: "en",
  crawl_mode: "playwright_llm",
  widget_config: defaultWidgetConfig(),
});

const componentStyleLabels = computed(() => ({
  header_background_color: t(
    "tenant.settings.appearance.componentStyles.labels.header_background_color"
  ),
  header_text_color: t(
    "tenant.settings.appearance.componentStyles.labels.header_text_color"
  ),
  user_message_background_color: t(
    "tenant.settings.appearance.componentStyles.labels.user_message_background_color"
  ),
  user_message_text_color: t(
    "tenant.settings.appearance.componentStyles.labels.user_message_text_color"
  ),
  bot_message_background_color: t(
    "tenant.settings.appearance.componentStyles.labels.bot_message_background_color"
  ),
  bot_message_text_color: t(
    "tenant.settings.appearance.componentStyles.labels.bot_message_text_color"
  ),
  send_button_background_color: t(
    "tenant.settings.appearance.componentStyles.labels.send_button_background_color"
  ),
  send_button_text_color: t(
    "tenant.settings.appearance.componentStyles.labels.send_button_text_color"
  ),
  input_background_color: t(
    "tenant.settings.appearance.componentStyles.labels.input_background_color"
  ),
  input_text_color: t(
    "tenant.settings.appearance.componentStyles.labels.input_text_color"
  ),
  input_focus_ring_color: t(
    "tenant.settings.appearance.componentStyles.labels.input_focus_ring_color"
  ),
  chat_background_color: t(
    "tenant.settings.appearance.componentStyles.labels.chat_background_color"
  ),
  reset_button_color: t(
    "tenant.settings.appearance.componentStyles.labels.reset_button_color"
  ),
  launcher_background_color: t(
    "tenant.settings.appearance.componentStyles.labels.launcher_background_color"
  ),
}));

const filteredComponentStyleLabels = computed(() => {
  const labels = { ...componentStyleLabels.value };
  delete labels.launcher_background_color;
  return labels;
});

watch(
  () => tenantsStore.currentTenant?.id,
  (newId) => {
    const newTenant = tenantsStore.currentTenant;
    if (newId && newTenant) {
      const newConfig = {
        ...defaultWidgetConfig(),
        ...(newTenant.widget_config || {}),
      };
      newConfig.color_palette =
        newTenant.widget_config?.color_palette ||
        defaultWidgetConfig().color_palette;
      newConfig.component_styles = {
        ...defaultWidgetConfig().component_styles,
        ...(newTenant.widget_config?.component_styles || {}),
      };

      formData.value = {
        name: newTenant.name,
        intro_message: newTenant.intro_message,
        system_persona: newTenant.system_persona,
        rag_prompt_template: newTenant.rag_prompt_template,
        doc_language: newTenant.doc_language,
        translation_target: newTenant.translation_target,
        crawl_mode: newTenant.crawl_mode || 'playwright_llm',
        widget_config: newConfig,
      };
    }
  },
  { immediate: true } // Removed deep: true
);

const thinkingMessages = computed({
  get: () => formData.value.widget_config.thinking_messages.join("\n"),
  set: (value) => {
    formData.value.widget_config.thinking_messages = value
      .split("\n")
      .map((s) => s.trim())
      .filter(Boolean);
  },
});

const addColor = () => {
  formData.value.widget_config.color_palette.push({
    id: uuidv4(),
    name: t("tenant.settings.defaults.newColor"),
    value: "#000000",
  });
};

const removeColor = (idToRemove) => {
  const palette = formData.value.widget_config.color_palette;
  if (palette.length <= 2) {
    addToast(
      t("tenant.settings.appearance.colorPalette.removeBaseColorError"),
      "warning"
    );
    return;
  }
  formData.value.widget_config.color_palette = palette.filter(
    (c) => c.id !== idToRemove
  );
};

// New function to clear images
const removeFile = (field) => {
  formData.value.widget_config[field] = null;
  // Reset the HTML input value so the same file can be selected again if needed
  const inputEl = document.getElementById(field);
  if (inputEl) inputEl.value = "";
  addToast(t("tenant.settings.actions.imageRemoved"), "success");
};

// Encodes a file as a base64 string
const encodeFileAsBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = (error) => reject(error);
    reader.readAsDataURL(file);
  });
};

const handleFileUpload = async (event, field) => {
  const file = event.target.files[0];
  if (!file) return;

  try {
    const base64String = await encodeFileAsBase64(file);
    formData.value.widget_config[field] = base64String;
    addToast(t("tenant.settings.actions.imageUpdated"), "success");
  } catch (error) {
    console.error("File reading error:", error);
    addToast(t("tenant.settings.actions.readFailed"), "error");
  }
};

const handleUpdate = async () => {
  if (tenantsStore.currentTenant && !tenantsStore.loading) {
    try {
      await tenantsStore.updateTenant(
        tenantsStore.currentTenant.id,
        formData.value
      );
      addToast(t("tenant.settings.actions.savedSuccess"), "success");
      previewKey.value++;
    } catch (error) {
      addToast(t("tenant.settings.actions.saveFailed"), "error");
    }
  }
};

const getPaletteColor = (colorId) => {
  const color = formData.value.widget_config.color_palette.find(
    (c) => c.id === colorId
  );
  return color ? color.value : colorId;
};

const copyScript = () => {
  const script = `<script src="${apiUrl}/tenants/widget.js" data-tenant-id="${tenantsStore.currentTenant?.id}"><\/script>`;
  navigator.clipboard
    .writeText(script)
    .then(() => {
      addToast(t("tenant.settings.actions.scriptCopied"), "success");
    })
    .catch(() => {
      addToast(t("tenant.settings.actions.copyFailed"), "error");
    });
};
</script>
