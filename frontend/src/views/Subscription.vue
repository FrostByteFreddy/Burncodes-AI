<template>
  <div class="container mx-auto px-4 py-4 sm:px-6 sm:py-8 max-w-7xl">
    <div
      class="flex flex-col sm:flex-row items-start sm:items-center gap-4 mb-8"
    >
      <div class="p-3 bg-primary/10 rounded-xl shrink-0">
        <font-awesome-icon
          :icon="['fas', 'credit-card']"
          class="text-2xl text-primary"
        />
      </div>
      <div>
        <h1 class="text-2xl sm:text-3xl font-bold text-base-content">
          {{ $t("subscription.title") }}
        </h1>
        <p class="text-base-content/60 text-sm sm:text-base">
          {{ $t("subscription.subtitle") }}
        </p>
      </div>
    </div>

    <div
      v-if="billingStore.loading && !billingStore.balance"
      class="flex justify-center py-12"
    >
      <span class="loading loading-spinner loading-lg text-primary"></span>
    </div>

    <div v-else>
      <!-- Balance Card (Always Visible) -->
      <div class="card bg-base-100 shadow-xl border border-base-200 mb-8">
        <div class="card-body p-4 sm:p-6">
          <div
            class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4"
          >
            <div>
              <h2 class="card-title text-lg opacity-70">
                {{ $t("subscription.balance") }}
              </h2>
              <div class="text-4xl sm:text-5xl font-bold text-primary mt-2">
                CHF {{ billingStore.balance?.toFixed(2) }}
              </div>
            </div>
            <button
              @click="handleManageBilling"
              class="btn btn-ghost btn-sm w-full sm:w-auto"
            >
              {{ $t("subscription.manageBilling") }}
            </button>
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="inline-flex p-1 space-x-1 bg-primary/10 rounded-full mb-6">
        <a
          class="btn border-0 rounded-full transition-all duration-300 hover:cursor-pointer space-x-2"
          :class="{
            '!bg-primary text-primary-content shadow': activeTab === 'addFunds',
            'btn-ghost text-base-content': activeTab !== 'addFunds',
          }"
          @click="activeTab = 'addFunds'"
        >
          <font-awesome-icon :icon="['fas', 'wallet']" />
          <span>{{ $t("subscription.tabs.addFunds") }}</span>
        </a>
        <a
          class="btn border-0 rounded-full transition-all duration-300 hover:cursor-pointer space-x-2"
          :class="{
            '!bg-primary text-primary-content shadow':
              activeTab === 'transactions',
            'btn-ghost text-base-content': activeTab !== 'transactions',
          }"
          @click="activeTab = 'transactions'"
        >
          <font-awesome-icon :icon="['fas', 'history']" />
          <span>{{ $t("subscription.tabs.transactions") }}</span>
        </a>
        <a
          class="btn border-0 rounded-full transition-all duration-300 hover:cursor-pointer space-x-2"
          :class="{
            '!bg-primary text-primary-content shadow':
              activeTab === 'costOverview',
            'btn-ghost text-base-content': activeTab !== 'costOverview',
          }"
          @click="activeTab = 'costOverview'"
        >
          <font-awesome-icon :icon="['fas', 'chart-pie']" />
          <span>{{ $t("subscription.tabs.costOverview") }}</span>
        </a>
      </div>

      <!-- Add Funds Tab -->
      <div
        v-if="activeTab === 'addFunds'"
        class="card bg-base-100 shadow-xl border border-base-200"
      >
        <div class="card-body p-4 sm:p-6">
          <h3 class="font-semibold text-lg mb-4 flex items-center gap-2">
            <font-awesome-icon :icon="['fas', 'wallet']" class="text-primary" />
            {{ $t("subscription.addFunds") }}
          </h3>

          <!-- Payment Type Toggle -->
          <div
            class="flex flex-wrap gap-2 mb-6 p-1 bg-base-100 rounded-lg border border-base-200 w-full sm:w-fit"
          >
            <button
              @click="isRecurring = false"
              class="flex-1 sm:flex-none px-4 py-2 rounded-md text-sm font-medium transition-all whitespace-nowrap"
              :class="
                !isRecurring
                  ? 'bg-primary text-primary-content shadow-sm'
                  : 'text-base-content/70 hover:bg-base-200'
              "
            >
              {{ $t("subscription.oneTime") }}
            </button>
            <button
              @click="isRecurring = true"
              class="flex-1 sm:flex-none px-4 py-2 rounded-md text-sm font-medium transition-all whitespace-nowrap"
              :class="
                isRecurring
                  ? 'bg-primary text-primary-content shadow-sm'
                  : 'text-base-content/70 hover:bg-base-200'
              "
            >
              {{ $t("subscription.monthly") }}
            </button>
          </div>

          <div class="space-y-5 max-w-md">
            <div>
              <label class="text-sm font-medium text-base-content/70 mb-3 block"
                >{{ $t("subscription.selectAmount") }}
                {{ isRecurring ? $t("subscription.monthlySuffix") : "" }}</label
              >
              <div class="grid grid-cols-3 gap-3">
                <button
                  v-for="amount in [20, 50, 100]"
                  :key="amount"
                  @click="rechargeAmount = amount"
                  class="btn transition-all duration-200 min-h-[3rem] h-auto py-2"
                  :class="
                    rechargeAmount === amount
                      ? 'btn-primary shadow-md scale-105'
                      : 'btn-outline border-base-300 hover:border-primary hover:bg-primary/5 text-base-content'
                  "
                >
                  CHF {{ amount }}
                </button>
              </div>
            </div>

            <div>
              <label
                class="text-sm font-medium text-base-content/70 mb-2 block"
                >{{ $t("subscription.customAmount") }}</label
              >
              <div class="relative">
                <div
                  class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none"
                >
                  <span class="text-base-content/50 font-semibold text-lg"
                    >CHF</span
                  >
                </div>
                <input
                  v-model.number="rechargeAmount"
                  type="number"
                  min="5"
                  step="5"
                  class="input input-bordered w-full pl-16 pr-4 h-14 text-lg font-semibold bg-base-100 border-2 hover:border-primary/50 focus:border-primary focus:outline-none transition-all"
                  :placeholder="$t('subscription.enterAmount')"
                />
              </div>
              <div class="label pb-0">
                <span class="label-text-alt text-error" v-if="amountError">{{
                  amountError
                }}</span>
                <span class="label-text-alt text-base-content/50" v-else>{{
                  $t("subscription.minDeposit")
                }}</span>
              </div>
            </div>

            <button
              @click="handleRecharge"
              class="btn btn-primary w-full shadow-lg shadow-primary/20 mt-2"
              :disabled="!!amountError || billingStore.loading"
            >
              <span
                v-if="billingStore.loading"
                class="loading loading-spinner loading-sm"
              ></span>
              <span v-else class="flex items-center gap-2">
                <font-awesome-icon
                  :icon="['fas', isRecurring ? 'sync' : 'bolt']"
                />
                {{
                  isRecurring
                    ? $t("subscription.subscribe")
                    : $t("subscription.add")
                }}
                CHF
                {{ rechargeAmount ? rechargeAmount.toFixed(2) : "0.00" }}
                {{ isRecurring ? $t("subscription.perMonth") : "" }}
              </span>
            </button>
          </div>
        </div>
      </div>

      <!-- Transactions Tab -->
      <div
        v-if="activeTab === 'transactions'"
        class="card bg-base-100 shadow-xl border border-base-200"
      >
        <div class="card-body p-4 sm:p-6">
          <h2 class="card-title text-lg mb-4 flex items-center gap-2">
            <font-awesome-icon
              :icon="['fas', 'history']"
              class="text-primary"
            />
            {{ $t("subscription.history.title") }}
          </h2>

          <!-- Desktop Table View -->
          <div
            class="hidden md:block overflow-x-auto rounded-lg border border-base-200"
          >
            <table class="table table-zebra w-full">
              <thead class="bg-base-200/50">
                <tr>
                  <th>{{ $t("subscription.history.date") }}</th>
                  <th>{{ $t("subscription.history.description") }}</th>
                  <th>{{ $t("subscription.history.amount") }}</th>
                  <th>{{ $t("subscription.history.status") }}</th>
                  <th>{{ $t("subscription.history.invoice") }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="billingStore.loading && !billingStore.history.length">
                  <td colspan="5" class="text-center py-8">
                    <span
                      class="loading loading-spinner loading-md text-primary"
                    ></span>
                  </td>
                </tr>
                <tr v-else-if="!billingStore.history.length">
                  <td
                    colspan="5"
                    class="text-center py-12 text-base-content/50"
                  >
                    <div class="flex flex-col items-center gap-2">
                      <font-awesome-icon
                        :icon="['fas', 'receipt']"
                        class="text-2xl opacity-20"
                      />
                      <p>{{ $t("subscription.history.noHistory") }}</p>
                    </div>
                  </td>
                </tr>
                <tr
                  v-for="item in billingStore.history"
                  :key="item.id"
                  class="hover"
                >
                  <td class="font-medium">
                    {{ new Date(item.date * 1000).toLocaleDateString() }}
                  </td>
                  <td>
                    {{
                      item.number || $t("subscription.history.oneTimePayment")
                    }}
                  </td>
                  <td class="font-mono font-semibold">
                    {{ item.currency }} {{ item.amount.toFixed(2) }}
                  </td>
                  <td>
                    <div
                      class="badge badge-sm gap-1 font-medium"
                      :class="{
                        'badge-success text-success-content':
                          item.status === 'paid',
                        'badge-warning text-warning-content':
                          item.status === 'open',
                        'badge-error text-error-content':
                          item.status === 'void' ||
                          item.status === 'uncollectible',
                      }"
                    >
                      {{ item.status }}
                    </div>
                  </td>
                  <td>
                    <a
                      v-if="item.pdf_url"
                      :href="item.pdf_url"
                      target="_blank"
                      class="btn btn-ghost btn-xs gap-1 text-primary"
                    >
                      <font-awesome-icon :icon="['fas', 'file-invoice']" />
                      PDF
                    </a>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Mobile Card View -->
          <div class="md:hidden space-y-4">
            <div
              v-if="billingStore.loading && !billingStore.history.length"
              class="flex justify-center py-8"
            >
              <span
                class="loading loading-spinner loading-md text-primary"
              ></span>
            </div>
            <div
              v-else-if="!billingStore.history.length"
              class="text-center py-12 text-base-content/50 border border-dashed border-base-300 rounded-xl"
            >
              <div class="flex flex-col items-center gap-2">
                <font-awesome-icon
                  :icon="['fas', 'receipt']"
                  class="text-2xl opacity-20"
                />
                <p>{{ $t("subscription.history.noHistory") }}</p>
              </div>
            </div>
            <div
              v-for="item in billingStore.history"
              :key="item.id"
              class="p-4 rounded-xl border border-base-200 bg-base-100 shadow-sm"
            >
              <div class="flex justify-between items-start mb-3">
                <div>
                  <p class="text-xs text-base-content/60 mb-1">
                    {{ new Date(item.date * 1000).toLocaleDateString() }}
                  </p>
                  <p class="font-medium text-sm">
                    {{
                      item.number || $t("subscription.history.oneTimePayment")
                    }}
                  </p>
                </div>
                <div
                  class="badge badge-sm gap-1 font-medium"
                  :class="{
                    'badge-success text-success-content':
                      item.status === 'paid',
                    'badge-warning text-warning-content':
                      item.status === 'open',
                    'badge-error text-error-content':
                      item.status === 'void' || item.status === 'uncollectible',
                  }"
                >
                  {{ item.status }}
                </div>
              </div>

              <div
                class="flex justify-between items-center pt-3 border-t border-base-200"
              >
                <span class="font-mono font-bold text-lg">
                  {{ item.currency }} {{ item.amount.toFixed(2) }}
                </span>
                <a
                  v-if="item.pdf_url"
                  :href="item.pdf_url"
                  target="_blank"
                  class="btn btn-ghost btn-sm gap-2 text-primary"
                >
                  <font-awesome-icon :icon="['fas', 'file-invoice']" />
                  PDF
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Cost Overview Tab -->
      <div
        v-if="activeTab === 'costOverview'"
        class="card bg-base-100 shadow-xl border border-base-200"
      >
        <div class="card-body p-4 sm:p-6">
          <h2 class="card-title text-lg mb-6 flex items-center gap-2">
            <font-awesome-icon
              :icon="['fas', 'chart-pie']"
              class="text-primary"
            />
            {{ $t("subscription.costOverview.title") }}
          </h2>

          <div class="space-y-4">
            <!-- Total Spent -->
            <div
              class="flex items-center justify-between p-4 bg-base-200/50 rounded-xl border border-base-200"
            >
              <div>
                <p class="text-sm font-medium text-base-content/70">
                  {{ $t("subscription.costOverview.totalCost") }}
                </p>
                <p class="text-2xl font-bold text-base-content mt-1">
                  CHF {{ billingStore.usage?.total_cost?.toFixed(2) }}
                </p>
              </div>
              <div
                class="w-10 h-10 flex items-center justify-center bg-primary/10 rounded-lg text-primary"
              >
                <font-awesome-icon :icon="['fas', 'coins']" />
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <!-- Chat Cost -->
              <div
                class="flex items-center justify-between p-4 bg-base-200/50 rounded-xl border border-base-200"
              >
                <div>
                  <p class="text-sm font-medium text-base-content/70">
                    {{ $t("subscription.costOverview.chatCost") }}
                  </p>
                  <p class="text-xl font-bold text-base-content mt-1">
                    CHF {{ (billingStore.usage?.chat_cost || 0).toFixed(2) }}
                  </p>
                </div>
                <div
                  class="w-10 h-10 flex items-center justify-center bg-secondary/10 rounded-lg text-secondary"
                >
                  <font-awesome-icon :icon="['fas', 'comments']" />
                </div>
              </div>

              <!-- Sources Cost -->
              <div
                class="flex items-center justify-between p-4 bg-base-200/50 rounded-xl border border-base-200"
              >
                <div>
                  <p class="text-sm font-medium text-base-content/70">
                    {{ $t("subscription.costOverview.sourcesCost") }}
                  </p>
                  <p class="text-xl font-bold text-base-content mt-1">
                    CHF {{ (billingStore.usage?.sources_cost || 0).toFixed(2) }}
                  </p>
                </div>
                <div
                  class="w-10 h-10 flex items-center justify-center bg-accent/10 rounded-lg text-accent"
                >
                  <font-awesome-icon :icon="['fas', 'database']" />
                </div>
              </div>
            </div>

            <!-- Tokens Used -->
            <div
              class="flex items-center justify-between p-4 bg-base-200/50 rounded-xl border border-base-200"
            >
              <div>
                <p class="text-sm font-medium text-base-content/70">
                  {{ $t("subscription.tokensUsed") }}
                </p>
                <p class="text-2xl font-bold text-base-content mt-1">
                  {{
                    (
                      billingStore.usage?.input_tokens +
                      billingStore.usage?.output_tokens
                    ).toLocaleString()
                  }}
                </p>
                <div class="flex gap-2 text-xs text-base-content/50 mt-1">
                  <span
                    >{{ $t("subscription.in") }}
                    {{
                      billingStore.usage?.input_tokens?.toLocaleString()
                    }}</span
                  >
                  <span>•</span>
                  <span
                    >{{ $t("subscription.out") }}
                    {{
                      billingStore.usage?.output_tokens?.toLocaleString()
                    }}</span
                  >
                </div>
              </div>
              <div
                class="w-10 h-10 flex items-center justify-center bg-secondary/10 rounded-lg text-secondary"
              >
                <font-awesome-icon :icon="['fas', 'robot']" />
              </div>
            </div>
          </div>

          <div class="mt-6 pt-6 border-t border-base-200">
            <div class="flex gap-3 text-sm text-base-content/70">
              <font-awesome-icon
                :icon="['fas', 'info-circle']"
                class="mt-1 text-info"
              />
              <div>
                <p class="font-medium text-base-content">
                  {{ $t("subscription.howItWorks.title") }}
                </p>
                <p class="mt-1 text-xs opacity-80">
                  {{ $t("subscription.howItWorks.description") }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from "vue";
import { useBillingStore } from "../stores/billing";
import { useToast } from "../composables/useToast";
import { useI18n } from "vue-i18n";

const { t } = useI18n();
const billingStore = useBillingStore();
const { addToast } = useToast();

const activeTab = ref("addFunds");
const rechargeAmount = ref(20);
const isRecurring = ref(false);

const amountError = computed(() => {
  if (!rechargeAmount.value) return t("subscription.errors.amountRequired");
  if (rechargeAmount.value < 5) return t("subscription.errors.minAmount");
  return "";
});

onMounted(async () => {
  // Check for success/cancel query params from Stripe redirect
  const urlParams = new URLSearchParams(window.location.search);
  const sessionId = urlParams.get("session_id");

  if (urlParams.get("success") && sessionId) {
    try {
      await billingStore.verifySession(sessionId);
      addToast(t("subscription.errors.rechargeSuccess"), "success");
    } catch (e) {
      addToast(t("subscription.errors.verificationFailed"), "error");
    }
    // Remove query params
    window.history.replaceState({}, document.title, window.location.pathname);
  } else if (urlParams.get("canceled")) {
    addToast(t("subscription.errors.rechargeCanceled"), "info");
    window.history.replaceState({}, document.title, window.location.pathname);
  }

  await Promise.all([
    billingStore.fetchBalance(),
    billingStore.fetchUsage(),
    billingStore.fetchHistory(),
  ]);
});

const handleRecharge = async () => {
  if (amountError.value) return;

  try {
    const url = await billingStore.createCheckoutSession(
      rechargeAmount.value,
      isRecurring.value
    );
    if (url) {
      window.location.href = url;
    }
  } catch (error) {
    addToast(t("subscription.errors.initiateFailed"), "error");
  }
};

const handleManageBilling = async () => {
  try {
    const url = await billingStore.getPortalUrl();
    if (url) {
      window.location.href = url;
    }
  } catch (error) {
    addToast(t("subscription.errors.portalFailed"), "error");
  }
};
</script>
