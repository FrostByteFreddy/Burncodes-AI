<template>
  <div class="page">
    <div class="page-header">
      <p class="page-label">{{ $t('subscription.title').toUpperCase() }}</p>
    </div>

    <!-- Loading -->
    <div v-if="billingStore.loading && !billingStore.balance" class="skeleton-block" style="height:160px;"></div>

    <div v-else class="billing-grid">
      <!-- ── Balance card ── -->
      <div class="card balance-card">
        <p class="card__eyebrow">{{ $t('subscription.balance') }}</p>
        <p class="balance-amount">CHF {{ billingStore.balance?.toFixed(2) ?? '—' }}</p>
        <button @click="handleManageBilling" class="btn-ghost-pill">
          {{ $t('subscription.manageBilling') }}
        </button>
      </div>

      <!-- ── Usage stats ── -->
      <div class="card stats-card">
        <div class="stat">
          <p class="stat__label">{{ $t('subscription.totalSpent') }}</p>
          <p class="stat__value">CHF {{ billingStore.usage?.total_cost?.toFixed(2) ?? '—' }}</p>
        </div>
        <div class="stat-divider"></div>
        <div class="stat">
          <p class="stat__label">{{ $t('subscription.tokensUsed') }}</p>
          <p class="stat__value">{{ totalTokens.toLocaleString() }}</p>
          <p class="stat__sub">
            {{ $t('subscription.in') }} {{ billingStore.usage?.input_tokens?.toLocaleString() ?? 0 }}
            &nbsp;·&nbsp;
            {{ $t('subscription.out') }} {{ billingStore.usage?.output_tokens?.toLocaleString() ?? 0 }}
          </p>
        </div>
      </div>

      <!-- ── Add Funds ── -->
      <div class="card funds-card">
        <div class="section-header">
          <span class="section-label">{{ $t('subscription.addFunds') }}</span>
          <div class="section-line"></div>
        </div>

        <!-- One-time / Recurring toggle -->
        <div class="type-toggle">
          <button
            @click="isRecurring = false"
            class="type-toggle__btn"
            :class="{ 'type-toggle__btn--active': !isRecurring }"
          >{{ $t('subscription.oneTime') }}</button>
          <button
            @click="isRecurring = true"
            class="type-toggle__btn"
            :class="{ 'type-toggle__btn--active': isRecurring }"
          >{{ $t('subscription.monthly') }}</button>
        </div>

        <!-- Amount preset buttons -->
        <p class="field__label" style="margin-bottom:10px;">
          {{ $t('subscription.selectAmount') }}
          <span v-if="isRecurring"> {{ $t('subscription.monthlySuffix') }}</span>
        </p>
        <div class="amount-grid">
          <button
            v-for="amount in [20, 50, 100]"
            :key="amount"
            @click="rechargeAmount = amount"
            class="amount-btn"
            :class="{ 'amount-btn--active': rechargeAmount === amount }"
          >CHF {{ amount }}</button>
        </div>

        <!-- Custom amount -->
        <div class="field" style="margin-top:14px;">
          <label class="field__label">{{ $t('subscription.customAmount') }}</label>
          <div class="field__input-wrap">
            <span class="field__prefix">CHF</span>
            <input
              v-model.number="rechargeAmount"
              type="number"
              min="5"
              step="5"
              class="field__input field__input--prefixed"
              :placeholder="$t('subscription.enterAmount')"
            />
          </div>
          <p class="field__hint" :class="{ 'field__hint--error': !!amountError }">
            {{ amountError || $t('subscription.minDeposit') }}
          </p>
        </div>

        <button
          @click="handleRecharge"
          :disabled="!!amountError || billingStore.loading"
          class="btn-pay"
        >
          <font-awesome-icon v-if="billingStore.loading" :icon="['fas', 'spinner']" class="spin" />
          <font-awesome-icon v-else :icon="['fas', isRecurring ? 'sync' : 'bolt']" />
          {{ isRecurring ? $t('subscription.subscribe') : $t('subscription.add') }}
          CHF {{ rechargeAmount ? rechargeAmount.toFixed(2) : '0.00' }}
          <span v-if="isRecurring">{{ $t('subscription.perMonth') }}</span>
        </button>

        <div class="info-box">
          <font-awesome-icon :icon="['fas', 'info-circle']" class="info-box__icon" />
          <div>
            <p class="info-box__title">{{ $t('subscription.howItWorks.title') }}</p>
            <p class="info-box__desc">{{ $t('subscription.howItWorks.description') }}</p>
          </div>
        </div>
      </div>

      <!-- ── Billing history ── -->
      <div class="card history-card">
        <div class="section-header">
          <span class="section-label">{{ $t('subscription.history.title') }}</span>
          <div class="section-line"></div>
        </div>

        <div v-if="billingStore.loading && !billingStore.history.length" class="skeleton-block" style="height:120px;"></div>
        <div v-else-if="!billingStore.history.length" class="empty-history">
          <font-awesome-icon :icon="['fas', 'receipt']" />
          <p>{{ $t('subscription.history.noHistory') }}</p>
        </div>
        <table v-else class="history-table">
          <thead>
            <tr>
              <th>{{ $t('subscription.history.date') }}</th>
              <th>{{ $t('subscription.history.description') }}</th>
              <th>{{ $t('subscription.history.amount') }}</th>
              <th>{{ $t('subscription.history.status') }}</th>
              <th>{{ $t('subscription.history.invoice') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in billingStore.history" :key="item.id">
              <td>{{ new Date(item.date * 1000).toLocaleDateString() }}</td>
              <td>{{ item.number || $t('subscription.history.oneTimePayment') }}</td>
              <td class="mono">{{ item.currency }} {{ item.amount.toFixed(2) }}</td>
              <td><span class="status-badge" :class="`status-badge--${item.status}`">{{ item.status }}</span></td>
              <td>
                <a v-if="item.pdf_url" :href="item.pdf_url" target="_blank" class="pdf-link">
                  <font-awesome-icon :icon="['fas', 'file-invoice']" /> PDF
                </a>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref, computed } from 'vue'
import { useBillingStore } from '../stores/billing'
import { useToast } from '../composables/useToast'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const billingStore = useBillingStore()
const { addToast } = useToast()

const rechargeAmount = ref(20)
const isRecurring = ref(false)

const amountError = computed(() => {
  if (!rechargeAmount.value) return t('subscription.errors.amountRequired')
  if (rechargeAmount.value < 5) return t('subscription.errors.minAmount')
  return ''
})

const totalTokens = computed(() =>
  (billingStore.usage?.input_tokens ?? 0) + (billingStore.usage?.output_tokens ?? 0)
)

onMounted(async () => {
  const urlParams = new URLSearchParams(window.location.search)
  const sessionId = urlParams.get('session_id')
  if (urlParams.get('success') && sessionId) {
    try {
      await billingStore.verifySession(sessionId)
      addToast(t('subscription.errors.rechargeSuccess'), 'success')
    } catch {
      addToast(t('subscription.errors.verificationFailed'), 'error')
    }
    window.history.replaceState({}, document.title, window.location.pathname)
  } else if (urlParams.get('canceled')) {
    addToast(t('subscription.errors.rechargeCanceled'), 'info')
    window.history.replaceState({}, document.title, window.location.pathname)
  }
  await Promise.all([billingStore.fetchBalance(), billingStore.fetchUsage(), billingStore.fetchHistory()])
})

const handleRecharge = async () => {
  if (amountError.value) return
  try {
    const url = await billingStore.createCheckoutSession(rechargeAmount.value, isRecurring.value)
    if (url) window.location.href = url
  } catch {
    addToast(t('subscription.errors.initiateFailed'), 'error')
  }
}

const handleManageBilling = async () => {
  try {
    const url = await billingStore.getPortalUrl()
    if (url) window.location.href = url
  } catch {
    addToast(t('subscription.errors.portalFailed'), 'error')
  }
}
</script>

<style scoped>
.page { max-width: 860px; }

.page-header { margin-bottom: 28px; }
.page-label {
  font-size: 11px; font-weight: 700;
  letter-spacing: 0.08em; color: var(--surface-muted);
}

/* Skeleton */
.skeleton-block {
  background: var(--surface-1);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-lg);
  animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.5} }

/* Grid layout */
.billing-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.card {
  background: var(--surface-1);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-lg);
  padding: 24px;
}

/* Balance card */
.balance-card { display: flex; flex-direction: column; gap: 8px; }
.card__eyebrow { font-size: 11px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--surface-muted); }
.balance-amount { font-size: 38px; font-weight: 800; color: var(--surface-heading); line-height: 1; margin: 8px 0; }
.btn-ghost-pill {
  display: inline-flex; align-items: center;
  padding: 6px 14px;
  background: var(--surface-2);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-pill);
  color: var(--surface-muted);
  font-size: 12px; font-weight: 600;
  cursor: pointer; width: fit-content;
  transition: color var(--t-fast), border-color var(--t-fast);
}
.btn-ghost-pill:hover { color: var(--surface-text); border-color: var(--surface-text); }

/* Stats card */
.stats-card { display: flex; flex-direction: column; gap: 16px; }
.stat { }
.stat__label { font-size: 11px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--surface-muted); margin-bottom: 4px; }
.stat__value { font-size: 26px; font-weight: 700; color: var(--surface-heading); }
.stat__sub { font-size: 11px; color: var(--surface-muted); margin-top: 4px; }
.stat-divider { height: 1px; background: var(--surface-3); }

/* Funds card - full width */
.funds-card { grid-column: 1 / -1; }
.history-card { grid-column: 1 / -1; }

/* Section header */
.section-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
.section-label { font-size: 10px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: var(--surface-muted); white-space: nowrap; }
.section-line { flex: 1; height: 1px; background: var(--surface-3); }

/* Type toggle */
.type-toggle {
  display: inline-flex; padding: 3px;
  background: var(--surface-2);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-pill);
  margin-bottom: 20px;
}
.type-toggle__btn {
  padding: 6px 16px;
  border: none; background: none;
  border-radius: var(--radius-pill);
  font-size: 13px; font-weight: 500;
  color: var(--surface-muted);
  cursor: pointer;
  transition: all var(--t-fast);
}
.type-toggle__btn--active {
  background: var(--gradient-brand);
  color: white; font-weight: 600;
}

/* Amount grid */
.amount-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 4px; }
.amount-btn {
  padding: 10px;
  background: var(--surface-2);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-md);
  color: var(--surface-text);
  font-size: 14px; font-weight: 600;
  cursor: pointer;
  transition: all var(--t-fast);
}
.amount-btn:hover { border-color: var(--brand-indigo); color: var(--brand-indigo); }
.amount-btn--active {
  background: rgba(10,31,171,0.12);
  border-color: var(--brand-indigo);
  color: var(--brand-indigo);
  transform: scale(1.03);
}

/* Field */
.field { display: flex; flex-direction: column; gap: 6px; }
.field__label { font-size: 11px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--surface-muted); }
.field__input {
  padding: 10px 14px;
  background: var(--surface-2);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-md);
  color: var(--surface-text);
  font-size: 14px; outline: none;
  transition: border-color var(--t-fast), box-shadow var(--t-fast);
  width: 100%;
}
.field__input:focus { border-color: var(--brand-indigo); box-shadow: 0 0 0 3px rgba(10,31,171,0.15); }
.field__input--prefixed { padding-left: 52px; }
.field__input-wrap { position: relative; }
.field__prefix {
  position: absolute; left: 14px; top: 50%; transform: translateY(-50%);
  font-size: 13px; font-weight: 700; color: var(--surface-muted);
}
.field__hint { font-size: 11px; color: var(--surface-muted); }
.field__hint--error { color: var(--status-error); }

/* Pay button */
.btn-pay {
  display: flex; align-items: center; gap: 8px;
  margin-top: 16px;
  padding: 11px 20px;
  width: 100%;
  justify-content: center;
  background: var(--gradient-brand);
  color: white; font-size: 14px; font-weight: 700;
  border: none; border-radius: var(--radius-md);
  cursor: pointer;
  transition: opacity var(--t-fast);
}
.btn-pay:hover:not(:disabled) { opacity: 0.9; }
.btn-pay:disabled { opacity: 0.4; cursor: not-allowed; }
.spin { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* Info box */
.info-box {
  display: flex; gap: 10px; align-items: flex-start;
  margin-top: 20px;
  padding: 14px;
  background: var(--surface-2);
  border: 1px solid var(--surface-3);
  border-radius: var(--radius-md);
}
.info-box__icon { color: var(--brand-indigo); flex-shrink: 0; margin-top: 2px; }
.info-box__title { font-size: 13px; font-weight: 600; color: var(--surface-text); margin-bottom: 4px; }
.info-box__desc { font-size: 12px; color: var(--surface-muted); line-height: 1.6; }

/* History table */
.empty-history {
  text-align: center; padding: 32px;
  color: var(--surface-muted);
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  font-size: 24px;
}
.empty-history p { font-size: 13px; }
.history-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.history-table th {
  text-align: left; padding: 8px 12px;
  font-size: 10px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase;
  color: var(--surface-muted);
  border-bottom: 1px solid var(--surface-3);
}
.history-table td { padding: 10px 12px; color: var(--surface-text); border-bottom: 1px solid var(--surface-3); }
.history-table tr:last-child td { border-bottom: none; }
.mono { font-family: monospace; font-weight: 600; }
.status-badge {
  display: inline-block; padding: 2px 8px;
  border-radius: var(--radius-pill);
  font-size: 11px; font-weight: 600;
}
.status-badge--paid { background: rgba(34,197,94,0.15); color: var(--status-success); }
.status-badge--open { background: rgba(251,191,36,0.15); color: #f59e0b; }
.status-badge--void,
.status-badge--uncollectible { background: rgba(255,68,68,0.1); color: var(--status-error); }
.pdf-link {
  display: inline-flex; align-items: center; gap: 5px;
  color: var(--brand-indigo); font-size: 12px; font-weight: 600;
  text-decoration: none;
}
.pdf-link:hover { opacity: 0.8; }

@media (max-width: 600px) {
  .billing-grid { grid-template-columns: 1fr; }
  .amount-grid { grid-template-columns: repeat(3, 1fr); }
}
</style>
