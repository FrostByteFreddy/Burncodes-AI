<template>
  <div class="container mx-auto px-4 py-4 sm:px-6 sm:py-8">
    <div class="flex items-center gap-3 mb-8">
      <div class="p-3 bg-primary/10 rounded-xl">
        <font-awesome-icon
          :icon="['fas', 'credit-card']"
          class="text-2xl text-primary"
        />
      </div>
      <div>
        <h1 class="text-3xl font-bold text-base-content">
          Billing & Subscription
        </h1>
        <p class="text-base-content/60">
          Manage your balance and view usage statistics
        </p>
      </div>
    </div>

    <div
      v-if="billingStore.loading && !billingStore.balance"
      class="flex justify-center py-12"
    >
      <span class="loading loading-spinner loading-lg text-primary"></span>
    </div>

    <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Balance Card -->
      <div
        class="card bg-base-100 shadow-xl border border-base-200 lg:col-span-2"
      >
        <div class="card-body">
          <div class="flex justify-between items-start">
            <div>
              <h2 class="card-title text-lg opacity-70">Current Balance</h2>
              <div class="text-5xl font-bold text-primary mt-2">
                CHF {{ billingStore.balance?.toFixed(2) }}
              </div>
            </div>
            <button @click="handleManageBilling" class="btn btn-ghost btn-sm">
              Manage Billing
            </button>
          </div>

          <div class="divider my-6"></div>

          <div class="bg-base-200/50 rounded-xl p-6 border border-base-200">
            <h3 class="font-semibold text-lg mb-4 flex items-center gap-2">
              <font-awesome-icon
                :icon="['fas', 'wallet']"
                class="text-primary"
              />
              Add Funds
            </h3>

            <div class="space-y-5">
              <div>
                <label
                  class="text-sm font-medium text-base-content/70 mb-3 block"
                  >Select Amount</label
                >
                <div class="grid grid-cols-3 gap-3">
                  <button
                    v-for="amount in [20, 50, 100]"
                    :key="amount"
                    @click="rechargeAmount = amount"
                    class="btn transition-all duration-200"
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
                  >Custom Amount</label
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
                    placeholder="Enter amount"
                  />
                </div>
                <div class="label pb-0">
                  <span class="label-text-alt text-error" v-if="amountError">{{
                    amountError
                  }}</span>
                  <span class="label-text-alt text-base-content/50" v-else
                    >Minimum deposit is 5 CHF</span
                  >
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
                  <font-awesome-icon :icon="['fas', 'bolt']" />
                  Add CHF
                  {{ rechargeAmount ? rechargeAmount.toFixed(2) : "0.00" }}
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Usage Card -->
      <div class="card bg-base-100 shadow-xl border border-base-200 h-fit">
        <div class="card-body">
          <h2 class="card-title text-lg mb-6 flex items-center gap-2">
            <font-awesome-icon
              :icon="['fas', 'chart-pie']"
              class="text-primary"
            />
            Usage Statistics
          </h2>

          <div class="space-y-4">
            <!-- Total Spent -->
            <div
              class="flex items-center justify-between p-4 bg-base-200/50 rounded-xl border border-base-200"
            >
              <div>
                <p class="text-sm font-medium text-base-content/70">
                  Total Spent
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

            <!-- Tokens Used -->
            <div
              class="flex items-center justify-between p-4 bg-base-200/50 rounded-xl border border-base-200"
            >
              <div>
                <p class="text-sm font-medium text-base-content/70">
                  Tokens Used
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
                    >In:
                    {{
                      billingStore.usage?.input_tokens?.toLocaleString()
                    }}</span
                  >
                  <span>•</span>
                  <span
                    >Out:
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
                <p class="font-medium text-base-content">How billing works</p>
                <p class="mt-1 text-xs opacity-80">
                  You pay a fixed amount to recharge your balance. Each chat
                  message consumes tokens which are deducted from your balance.
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

const billingStore = useBillingStore();
const { addToast } = useToast();

const rechargeAmount = ref(20);

const amountError = computed(() => {
  if (!rechargeAmount.value) return "Amount is required";
  if (rechargeAmount.value < 5) return "Minimum amount is 5 CHF";
  return "";
});

onMounted(async () => {
  // Check for success/cancel query params from Stripe redirect
  const urlParams = new URLSearchParams(window.location.search);
  const sessionId = urlParams.get("session_id");

  if (urlParams.get("success") && sessionId) {
    try {
      await billingStore.verifySession(sessionId);
      addToast(
        "Recharge successful! Your balance has been updated.",
        "success"
      );
    } catch (e) {
      addToast(
        "Payment verification failed. Please contact support if you were charged.",
        "error"
      );
    }
    // Remove query params
    window.history.replaceState({}, document.title, window.location.pathname);
  } else if (urlParams.get("canceled")) {
    addToast("Recharge canceled.", "info");
    window.history.replaceState({}, document.title, window.location.pathname);
  }

  await Promise.all([billingStore.fetchBalance(), billingStore.fetchUsage()]);
});

const handleRecharge = async () => {
  if (amountError.value) return;

  try {
    const url = await billingStore.createCheckoutSession(rechargeAmount.value);
    if (url) {
      window.location.href = url;
    }
  } catch (error) {
    addToast("Failed to initiate recharge.", "error");
  }
};

const handleManageBilling = async () => {
  try {
    const url = await billingStore.getPortalUrl();
    if (url) {
      window.location.href = url;
    }
  } catch (error) {
    addToast(
      "Failed to open billing portal. You may not have a billing account yet.",
      "error"
    );
  }
};
</script>
