<template>
  <!-- Balance and spending -->
  <BcPanel as="section"  >
    <div v-if="billing.balance === null && billing.loading" class="ghost-stack" aria-busy="true">
      <span class="ghost ghost--line" style="width: 100px"></span>
      <span class="ghost" style="width: 200px; height: 38px"></span>
      <span class="ghost ghost--line" style="width: 60%"></span>
    </div>
    <template v-else>
      <div class="bil-head">
        <div>
          <p class="meta">{{ $t('settings.billing.balance') }}</p>
          <p class="bil-balance" :class="{ 'bil-balance--low': (billing.balance ?? 0) < 5 }">CHF {{ fmt(billing.balance) }}</p>
        </div>
        <BcButton variant="secondary" type="button"  @click="openPortal">
          <font-awesome-icon :icon="['fas', 'arrow-up-right-from-square']" /> {{ $t('settings.billing.portal') }}
        </BcButton>
      </div>
      <dl class="bil-spent">
        <div><dt>{{ $t('settings.billing.answers') }}</dt><dd>CHF {{ fmt(billing.usage?.chat_cost) }}</dd></div>
        <div><dt>{{ $t('settings.billing.learning') }}</dt><dd>CHF {{ fmt(billing.usage?.sources_cost) }}</dd></div>
        <div><dt>{{ $t('settings.billing.reviews') }}</dt><dd>CHF {{ fmt(billing.usage?.review_cost) }}</dd></div>
        <div><dt>{{ $t('settings.billing.total') }}</dt><dd>CHF {{ fmt(billing.usage?.total_cost) }}</dd></div>
      </dl>
      <p class="field-hint">{{ $t('settings.billing.spentHint') }}</p>
    </template>
  </BcPanel>

  <!-- Top up -->
  <BcPanel as="section"  >
    <h2 class="panel-title">{{ $t('settings.billing.topUpTitle') }}</h2>
    <p class="panel-sub">{{ $t('settings.billing.topUpSub') }}</p>
    <div class="cfg-fields">
      <div class="bil-seg" role="group" :aria-label="$t('settings.billing.topUpTitle')">
        <button type="button" class="bil-seg__btn" :class="{ 'bil-seg__btn--on': !recurring }" :aria-pressed="!recurring" @click="recurring = false">{{ $t('settings.billing.once') }}</button>
        <button type="button" class="bil-seg__btn" :class="{ 'bil-seg__btn--on': recurring }" :aria-pressed="recurring" @click="recurring = true">{{ $t('settings.billing.monthly') }}</button>
      </div>
      <div class="bil-amounts">
        <button v-for="a in [20, 50, 100]" :key="a" type="button" class="bil-amount" :class="{ 'bil-amount--on': amount === a }" @click="amount = a">CHF {{ a }}</button>
        <div class="bil-custom">
          <label for="b-amount" class="sr-only">{{ $t('settings.billing.custom') }}</label>
          <span>CHF</span>
          <input id="b-amount" v-model.number="amount" type="number" min="5" step="5" :placeholder="$t('settings.billing.custom')" />
        </div>
      </div>
      <p class="field-hint" :class="{ 'field-hint--warn': !!amountError }">{{ amountError || (recurring ? $t('settings.billing.monthlyHint') : $t('settings.billing.onceHint')) }}</p>
      <div class="page-actions">
        <BcButton variant="primary" type="button"  :disabled="!!amountError || billing.loading" @click="checkout">
          <font-awesome-icon v-if="billing.loading" :icon="['fas', 'spinner']" class="animate-spin" />
          {{ recurring ? $t('settings.billing.payMonthly', { amount: fmt(amount) }) : $t('settings.billing.pay', { amount: fmt(amount) }) }}
        </BcButton>
      </div>
    </div>
  </BcPanel>

  <!-- Payments -->
  <BcPanel as="section"  >
    <h2 class="panel-title">{{ $t('settings.billing.historyTitle') }}</h2>
    <div v-if="billing.loading && !billing.history.length" style="margin-top: 16px" aria-busy="true">
      <div v-for="n in 3" :key="n" class="ghost-row"><span class="ghost ghost--line" style="width: 90px"></span><span class="ghost ghost--line" style="flex: 1"></span><span class="ghost ghost--line" style="width: 80px"></span></div>
    </div>
    <p v-else-if="!billing.history.length" class="meta" style="margin-top: 12px">{{ $t('settings.billing.noHistory') }}</p>
    <table v-else class="bil-table">
      <thead>
        <tr><th>{{ $t('subscription.history.date') }}</th><th>{{ $t('subscription.history.description') }}</th><th class="num">{{ $t('subscription.history.amount') }}</th><th>{{ $t('subscription.history.status') }}</th><th></th></tr>
      </thead>
      <tbody>
        <tr v-for="item in billing.history" :key="item.id">
          <td>{{ new Date(item.date * 1000).toLocaleDateString(locale) }}</td>
          <td>{{ item.number || $t('subscription.history.oneTimePayment') }}</td>
          <td class="num">{{ item.currency }} {{ item.amount.toFixed(2) }}</td>
          <td><span class="bil-status" :class="`bil-status--${item.status}`">{{ $te(`subscription.history.statuses.${item.status}`) ? $t(`subscription.history.statuses.${item.status}`) : item.status }}</span></td>
          <td><a v-if="item.pdf_url" :href="item.pdf_url" target="_blank" rel="noopener" class="bil-pdf">{{ $t('settings.billing.invoice') }}</a></td>
        </tr>
      </tbody>
    </table>
  </BcPanel>
</template>

<script setup>
import { BcButton, BcPanel } from '@/components/ui';
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useBillingStore } from '@/stores/billing';
import { useToast } from '@/composables/useToast';

const billing = useBillingStore();
const { addToast } = useToast();
const { t, locale } = useI18n();
const amount = ref(20);
const recurring = ref(false);
const fmt = (n) => Number(n || 0).toFixed(2);

const amountError = computed(() => {
  if (!amount.value) return t('subscription.errors.amountRequired');
  if (amount.value < 5) return t('subscription.errors.minAmount');
  return '';
});

onMounted(async () => {
  // Back from Stripe checkout
  const params = new URLSearchParams(window.location.search);
  if (params.get('success') && params.get('session_id')) {
    try {
      await billing.verifySession(params.get('session_id'));
      addToast(t('subscription.errors.rechargeSuccess'), 'success');
    } catch { addToast(t('subscription.errors.verificationFailed'), 'error'); }
    window.history.replaceState({}, document.title, window.location.pathname);
  } else if (params.get('canceled')) {
    addToast(t('subscription.errors.rechargeCanceled'), 'info');
    window.history.replaceState({}, document.title, window.location.pathname);
  }
  await Promise.all([billing.fetchBalance(), billing.fetchUsage(), billing.fetchHistory()]);
});

const checkout = async () => {
  if (amountError.value) return;
  try {
    const url = await billing.createCheckoutSession(amount.value, recurring.value);
    if (url) window.location.href = url;
  } catch { addToast(t('subscription.errors.initiateFailed'), 'error'); }
};
const openPortal = async () => {
  try {
    const url = await billing.getPortalUrl();
    if (url) window.location.href = url;
  } catch { addToast(t('subscription.errors.portalFailed'), 'error'); }
};
</script>

<style scoped>
.bil-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.bil-balance { font-size: 40px; font-weight: 800; letter-spacing: -0.02em; color: var(--surface-heading); line-height: 1.1; }
.bil-balance--low { color: var(--status-warning); }
.bil-spent { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px 20px; margin: 20px 0 0; padding-top: 16px; border-top: 1px solid var(--surface-3); }
.bil-spent dt { font-size: var(--text-sm); color: var(--surface-muted); }
.bil-spent dd { margin: 2px 0 0; font-size: var(--text-lg); font-weight: 700; color: var(--surface-heading); }

.bil-seg { display: inline-flex; align-self: flex-start; gap: 2px; padding: 3px; border-radius: var(--radius-pill); background: var(--surface-2); }
.bil-seg__btn { padding: 6px 14px; border: none; border-radius: var(--radius-pill); background: none; cursor: pointer; font: inherit; font-size: var(--text-sm); font-weight: 600; color: var(--surface-muted); }
.bil-seg__btn--on { background: var(--surface-3); color: var(--surface-heading); }
.bil-amounts { display: flex; flex-wrap: wrap; gap: 8px; }
.bil-amount {
  padding: 10px 18px; border-radius: var(--radius-md); cursor: pointer; font: inherit; font-weight: 700;
  background: var(--surface-2); border: 1px solid var(--surface-3); color: var(--surface-heading);
}
.bil-amount:hover { border-color: var(--surface-muted); }
.bil-amount--on { border-color: var(--interactive); background: var(--interactive-soft); }
.bil-custom { display: flex; align-items: center; gap: 8px; padding: 0 12px; border-radius: var(--radius-md); background: var(--surface-2); border: 1px solid var(--surface-3); color: var(--surface-muted); }
.bil-custom:focus-within { border-color: var(--interactive); }
.bil-custom input { width: 110px; padding: 10px 0; border: none; background: none; color: var(--surface-heading); font: inherit; font-weight: 700; outline: none; }

.bil-table { width: 100%; margin-top: 16px; border-collapse: collapse; font-size: var(--text-sm); }
.bil-table th { text-align: left; font-weight: 600; color: var(--surface-muted); padding: 0 8px 8px 0; border-bottom: 1px solid var(--surface-3); }
.bil-table td { padding: 10px 8px 10px 0; border-bottom: 1px solid var(--surface-3); color: var(--surface-text); }
.bil-table tr:last-child td { border-bottom: none; }
.bil-table .num { text-align: right; padding-right: 16px; }
.bil-status { padding: 2px 8px; border-radius: var(--radius-pill); font-size: var(--text-xs); font-weight: 700; background: var(--surface-2); }
.bil-status--paid { background: var(--status-success-soft); color: var(--status-success); }
.bil-pdf { color: var(--interactive); font-weight: 600; text-decoration: none; }
.bil-pdf:hover { text-decoration: underline; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }

@media (max-width: 760px) {
  .bil-spent { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
