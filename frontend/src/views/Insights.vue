<template>
  <div class="ins">
    <div class="page-head">
      <div>
        <h1 class="page-title">{{ $t('insights.title') }}</h1>
        <p class="page-lede">{{ $t('pages.insights') }}</p>
      </div>
    </div>

    <!-- What the review found: the reason to open this page -->
    <BcPanel as="section"  >
      <div class="ins-head">
        <div>
          <h2 class="panel-title">{{ $t('insights.findings.title') }}</h2>
          <p class="panel-sub">{{ $t('insights.findings.sub') }}</p>
        </div>
        <div class="ins-seg" role="group" :aria-label="$t('insights.findings.filter')">
          <button v-for="s in STATUSES" :key="s" type="button" class="ins-seg__btn" :class="{ 'ins-seg__btn--on': status === s }" :aria-pressed="status === s" @click="status = s">
            {{ $t(`insights.findings.status.${s}`) }}<span v-if="counts[s]" class="ins-seg__count">{{ counts[s] }}</span>
          </button>
        </div>
      </div>

      <ul v-if="loadingFindings && !findings.length" class="ins-findings" aria-busy="true">
        <li v-for="n in 3" :key="n" class="ins-finding">
          <span class="ghost ghost--pill"></span>
          <div class="ghost-stack">
            <span class="ghost ghost--title" :style="{ width: `${70 - n * 8}%` }"></span>
            <span class="ghost ghost--line" style="width: 80%"></span>
            <span class="ghost ghost--line" style="width: 55%"></span>
          </div>
          <div class="ins-finding__actions"><span class="ghost ghost--btn"></span><span class="ghost ghost--btn" style="width: 70px"></span></div>
        </li>
      </ul>
      <div v-else-if="!findings.length" class="ins-empty">
        <font-awesome-icon :icon="['fas', 'check']" class="ins-empty__icon" />
        <p>{{ status === 'open' ? (review.enabled ? $t('insights.findings.noneOpen') : $t('insights.findings.reviewOff')) : $t('insights.findings.noneOther') }}</p>
      </div>

      <ul v-else class="ins-findings">
        <li v-for="f in findings" :key="f.id" class="ins-finding">
          <span class="ins-kind" :class="`ins-kind--${f.kind}`">{{ $t(`insights.kinds.${f.kind}`) }}</span>
          <div class="ins-finding__body">
            <p class="ins-finding__question">“{{ f.question }}”</p>
            <p class="ins-finding__problem">{{ f.problem }}</p>
            <p v-if="f.suggestion" class="ins-finding__suggestion">
              <font-awesome-icon :icon="['fas', 'lightbulb']" /> {{ f.suggestion }}
            </p>
            <div class="ins-finding__meta">
              <time :datetime="f.created_at">{{ fmtDateTime(f.created_at) }}</time>
              <button type="button" class="ins-link" @click="openConversation(f.conversation_id, f.log_id)">{{ $t('insights.findings.viewConversation') }}</button>
            </div>
          </div>
          <div class="ins-finding__actions">
            <template v-if="f.status === 'open'">
              <BcButton variant="secondary" type="button"  @click="answerFor = f">
                <font-awesome-icon :icon="['fas', 'plus']" /> {{ $t('insights.findings.addAnswer') }}
              </BcButton>
              <BcButton variant="secondary" type="button"  @click="setStatus(f, 'resolved')">
                <font-awesome-icon :icon="['fas', 'check']" /> {{ $t('insights.findings.done') }}
              </BcButton>
              <BcButton variant="secondary" type="button" class="ins-dismiss" @click="setStatus(f, 'dismissed')">{{ $t('insights.findings.dismiss') }}</BcButton>
            </template>
            <BcButton variant="secondary" v-else type="button"  @click="setStatus(f, 'open')">{{ $t('insights.findings.reopen') }}</BcButton>
          </div>
        </li>
      </ul>

      <!-- How the review runs, and what it costs -->
      <div class="ins-review">
        <p class="meta">
          <template v-if="review.enabled">
            {{ $t(review.interval_days === 7 ? 'insights.review.howWeekly' : 'insights.review.how', { cost: fmtChf(review.est_chf_per_conversation) }) }}
            <template v-if="review.reviewed_30d"> {{ $t('insights.review.stats', { n: review.reviewed_30d, cost: fmtChf(review.cost_30d_chf) }, review.reviewed_30d) }}</template>
          </template>
          <template v-else>{{ $t('insights.review.off') }}</template>
          <router-link :to="{ name: 'TenantSettings', params: { tenantId } }" class="ins-link ins-link--inline">{{ $t('insights.review.change') }}</router-link>
        </p>
        <BcButton variant="secondary" v-if="review.enabled" type="button"  :disabled="reviewQueued" @click="runNow">
          <font-awesome-icon :icon="['fas', 'rotate']" /> {{ reviewQueued ? $t('insights.review.queued') : $t('insights.review.now') }}
        </BcButton>
      </div>
    </BcPanel>

    <!-- Conversations -->
    <BcPanel as="section"  >
      <div class="ins-head">
        <div>
          <h2 class="panel-title">{{ $t('insights.conversations.title') }}</h2>
          <p class="panel-sub">{{ $t('insights.conversations.sub') }}</p>
        </div>
      </div>

      <div v-if="logsLoading && !conversations.length" aria-busy="true">
        <div v-for="n in 5" :key="n" class="ghost-row">
          <div class="ghost-stack" style="flex: 1"><span class="ghost ghost--line" :style="{ width: `${75 - n * 7}%` }"></span><span class="ghost ghost--line" style="width: 22%; height: 10px"></span></div>
          <span class="ghost ghost--line" style="width: 90px"></span>
        </div>
      </div>
      <p v-else-if="logsError" class="meta">{{ logsError }}</p>
      <p v-else-if="!conversations.length" class="meta">{{ $t('insights.conversations.none') }}</p>

      <div v-else class="ins-convos" :class="{ 'ins-convos--open': selected }">
        <ol class="ins-list">
          <li v-for="c in conversations" :key="c.conversation_id">
            <button type="button" class="ins-row" :class="{ 'ins-row--on': selected === c.conversation_id }" @click="openConversation(c.conversation_id)">
              <span class="ins-row__first">{{ c.first_message || $t('chatLogs.noMessage') }}</span>
              <span class="ins-row__meta">
                {{ $t('insights.conversations.questions', { n: c.message_count }, c.message_count) }}, CHF {{ fmtChf(c.total_cost) }}
                <span v-if="flagged.has(c.conversation_id)" class="ins-row__flag">{{ $t('insights.conversations.flagged') }}</span>
              </span>
              <time class="ins-row__time" :datetime="c.last_active">{{ fmtDateTime(c.last_active) }}</time>
            </button>
          </li>
        </ol>

        <!-- Reader -->
        <div v-if="selected" class="ins-reader">
          <div class="ins-reader__head">
            <p class="meta">{{ fmtDateTime(conversationLogs[0]?.created_at) }}</p>
            <button type="button" class="cfg-icon-btn" :aria-label="$t('insights.conversations.close')" @click="selected = null">
              <font-awesome-icon :icon="['fas', 'xmark']" />
            </button>
          </div>
          <div ref="reader" class="ins-reader__scroll">
            <div v-for="log in conversationLogs" :key="log.id" :data-log="log.id" class="ins-turn" :class="{ 'ins-turn--hit': log.id === highlight }">
              <p v-if="log.user_message" class="ins-bubble ins-bubble--user">{{ log.user_message }}</p>
              <div v-if="log.ai_message" class="ins-bubble ins-bubble--bot" v-html="processBotMessage(log.ai_message).html"></div>
            </div>
          </div>
        </div>
      </div>
    </BcPanel>

    <!-- Answer a finding with a custom rule: trigger prefilled, staff write the answer -->
    <AddRuleWizard
      :open="!!answerFor"
      :initial-trigger="answerFor?.topic || answerFor?.question || ''"
      :hint="answerFor?.suggestion || ''"
      @close="answerFor = null"
      @add-rule="saveAnswer"
    />
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { BcButton, BcPanel } from '@/components/ui';
import { computed, nextTick, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import apiClient from '@/utils/api'
import { useTenantsStore } from '@/stores/tenants'
import { useToast } from '@/composables/useToast'
import { processBotMessage } from '@/utils/chatProcessor.js'
import AddRuleWizard from '@/components/tenant/sources/AddRuleWizard.vue'

const { t, locale } = useI18n()
const tenantsStore = useTenantsStore()
const { addToast } = useToast()
const route = useRoute()
const tenantId = computed(() => route.params.tenantId || tenantsStore.currentTenant?.id || '')

const fmtChf = (n) => Number(n || 0).toFixed(2)
const fmtDateTime = (iso) => (iso ? new Date(iso).toLocaleString(locale.value, { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '')

// ── Findings ────────────────────────────────────────────────────────
const STATUSES = ['open', 'resolved', 'dismissed']
const status = ref('open')
const findings = ref([])
const counts = ref({})
const review = ref({ enabled: true })
const loadingFindings = ref(false)
const reviewQueued = ref(false)

const fetchFindings = async () => {
  if (!tenantId.value) return
  loadingFindings.value = true
  try {
    const { data } = await apiClient.get(`/tenants/${tenantId.value}/insights/findings`, { params: { status: status.value } })
    findings.value = data.findings
    counts.value = data.counts
    review.value = data.review
  } catch {
    addToast(t('insights.findings.loadFailed'), 'error')
  } finally { loadingFindings.value = false }
}

const setStatus = async (f, next) => {
  try {
    await apiClient.patch(`/tenants/${tenantId.value}/insights/findings/${f.id}`, { status: next })
    findings.value = findings.value.filter((x) => x.id !== f.id)
    counts.value = { ...counts.value, [f.status]: Math.max(0, (counts.value[f.status] || 1) - 1), [next]: (counts.value[next] || 0) + 1 }
  } catch { addToast(t('tenant.settings.actions.saveFailed'), 'error') }
}

// Answering a finding adds a custom rule and marks the finding done
const answerFor = ref(null)
const saveAnswer = async (rule) => {
  const finding = answerFor.value
  const existing = (tenantsStore.currentTenant?.fine_tune_rules || []).map(({ trigger, instruction }) => ({ trigger, instruction }))
  try {
    await tenantsStore.updateTenant(tenantId.value, { fine_tune_rules: [...existing, rule] })
    addToast(t('insights.findings.answerSaved'), 'success')
    if (finding) await setStatus(finding, 'resolved')
  } catch { addToast(t('tenant.fineTune.actions.saveFailed'), 'error') }
}

const runNow = async () => {
  reviewQueued.value = true
  try {
    await apiClient.post(`/tenants/${tenantId.value}/insights/review`)
    addToast(t('insights.review.started'), 'success')
    // results arrive within a minute or two; refresh once they likely have
    setTimeout(fetchFindings, 45000)
  } catch { addToast(t('insights.review.failed'), 'error'); reviewQueued.value = false }
}

// ── Conversations ───────────────────────────────────────────────────
const conversations = ref([])
const conversationLogs = ref([])
const selected = ref(null)
const highlight = ref(null)
const logsLoading = ref(false)
const logsError = ref(null)
const reader = ref(null)
const flagged = computed(() => new Set(findings.value.map((f) => f.conversation_id)))

const fetchConversations = async () => {
  if (!tenantId.value) return
  logsLoading.value = true
  logsError.value = null
  try {
    conversations.value = (await apiClient.get(`/chat/${tenantId.value}/conversations`)).data
  } catch { logsError.value = t('chatLogs.errors.loadConversations') }
  finally { logsLoading.value = false }
}

const openConversation = async (conversationId, logId = null) => {
  try {
    selected.value = conversationId
    highlight.value = logId
    conversationLogs.value = (await apiClient.get(`/chat/${tenantId.value}/conversation/${conversationId}`)).data
    await nextTick()
    const el = reader.value
    if (!el) return
    const target = logId && el.querySelector(`[data-log="${logId}"]`)
    if (target) target.scrollIntoView({ block: 'center' })
    else el.scrollTop = el.scrollHeight
    el.closest('.panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  } catch {
    addToast(t('chatLogs.errors.loadLogs'), 'error')
    selected.value = null
  }
}

watch(status, fetchFindings)
watch(tenantId, (id) => {
  if (!id) return
  selected.value = null
  status.value = 'open'
  fetchFindings()
  fetchConversations()
}, { immediate: true })
</script>

<style scoped>
.ins { display: flex; flex-direction: column; gap: 20px; }
.ins-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; flex-wrap: wrap; margin-bottom: 18px; }

.ins-seg { display: inline-flex; gap: 2px; padding: 3px; border-radius: var(--radius-pill); background: var(--surface-2); }
.ins-seg__btn { display: inline-flex; align-items: center; gap: 6px; padding: 5px 12px; border: none; border-radius: var(--radius-pill); background: none; cursor: pointer; font: inherit; font-size: var(--text-sm); font-weight: 600; color: var(--surface-muted); }
.ins-seg__btn:hover { color: var(--surface-heading); }
.ins-seg__btn--on { background: var(--surface-3); color: var(--surface-heading); }
.ins-seg__count { font-size: var(--text-xs); padding: 0 6px; border-radius: var(--radius-pill); background: var(--surface-1); }

.ins-empty { display: flex; align-items: center; gap: 10px; font-size: 15px; color: var(--surface-text); }
.ins-empty__icon { color: var(--status-success); }

/* Findings */
.ins-findings { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; }
.ins-finding {
  display: grid; grid-template-columns: 128px minmax(0, 1fr) auto; gap: 16px; align-items: start;
  padding: 16px 0; border-top: 1px solid var(--surface-3);
}
.ins-finding:first-child { border-top: none; padding-top: 0; }
.ins-kind { justify-self: start; margin-top: 2px; padding: 3px 10px; border-radius: var(--radius-pill); font-size: var(--text-xs); font-weight: 700; background: var(--surface-2); color: var(--surface-text); }
.ins-kind--unanswered { background: var(--interactive-soft); color: var(--interactive); }
.ins-kind--wrong { background: var(--status-error-soft, rgba(255, 107, 107, 0.12)); color: var(--status-error); }
.ins-kind--pushback { background: var(--status-warning-soft); color: var(--status-warning); }
.ins-kind--unclear { background: var(--surface-2); color: var(--surface-text); }
.ins-finding__body { min-width: 0; display: flex; flex-direction: column; gap: 4px; max-width: var(--measure); }
.ins-finding__question { font-size: 15px; font-weight: 700; color: var(--surface-heading); overflow-wrap: anywhere; }
.ins-finding__problem { font-size: var(--text-sm); color: var(--surface-text); }
.ins-finding__suggestion { display: flex; gap: 8px; align-items: baseline; font-size: var(--text-sm); color: var(--surface-heading); }
.ins-finding__suggestion svg { color: var(--status-warning); }
.ins-finding__meta { display: flex; gap: 14px; align-items: baseline; margin-top: 2px; font-size: var(--text-xs); color: var(--surface-muted); }
.ins-link { padding: 0; border: none; background: none; cursor: pointer; font: inherit; font-size: var(--text-xs); font-weight: 600; color: var(--interactive); }
.ins-link:hover { text-decoration: underline; }
.ins-finding__actions { display: flex; gap: 6px; flex-wrap: wrap; justify-content: flex-end; }
.ins-dismiss { color: var(--surface-muted); }

.ins-review { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; margin-top: 20px; padding-top: 16px; border-top: 1px solid var(--surface-3); }
.ins-review .meta { flex: 1; min-width: 240px; }
.ins-link--inline { margin-left: 6px; font-size: inherit; text-decoration: none; }

/* Conversations: list, and a reader beside it once one is open */
.ins-convos { display: grid; grid-template-columns: minmax(0, 1fr); gap: 20px; }
.ins-convos--open { grid-template-columns: minmax(0, 2fr) minmax(0, 3fr); }
.ins-list { list-style: none; padding: 0; margin: 0; max-height: 640px; overflow-y: auto; }
.ins-row {
  width: 100%; display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 2px 12px; text-align: left;
  padding: 12px; border: none; border-radius: var(--radius-md); background: none; cursor: pointer; font: inherit;
}
.ins-row:hover { background: var(--surface-2); }
.ins-row--on { background: var(--surface-2); box-shadow: inset 3px 0 0 var(--interactive); }
.ins-row__first { font-size: 15px; font-weight: 600; color: var(--surface-heading); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ins-row__time { grid-column: 2; grid-row: 1; font-size: var(--text-xs); color: var(--surface-muted); white-space: nowrap; }
.ins-row__meta { grid-column: 1 / -1; font-size: var(--text-sm); color: var(--surface-muted); }
.ins-row__flag { margin-left: 8px; padding: 1px 8px; border-radius: var(--radius-pill); font-size: var(--text-xs); font-weight: 700; background: var(--status-warning-soft); color: var(--status-warning); }

.ins-reader { border: 1px solid var(--surface-3); border-radius: var(--radius-lg); background: var(--surface-0); display: flex; flex-direction: column; min-height: 0; }
.ins-reader__head { display: flex; align-items: center; justify-content: space-between; padding: 8px 8px 8px 16px; border-bottom: 1px solid var(--surface-3); }
.ins-reader__scroll { padding: 16px; max-height: 600px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; }
.ins-turn { display: flex; flex-direction: column; gap: 8px; padding: 6px; border-radius: var(--radius-md); }
.ins-turn--hit { background: var(--status-warning-soft); outline: 1px solid var(--status-warning); }
.ins-bubble { max-width: 85%; padding: 10px 14px; border-radius: 14px; font-size: var(--text-sm); line-height: var(--leading-body); overflow-wrap: anywhere; }
.ins-bubble--user { align-self: flex-end; background: var(--interactive-strong); color: #fff; border-bottom-right-radius: 4px; }
.ins-bubble--bot { align-self: flex-start; background: var(--surface-2); color: var(--surface-text); border-bottom-left-radius: 4px; }
.ins-bubble--bot :deep(p) { margin: 0 0 6px; }
.ins-bubble--bot :deep(p:last-child) { margin-bottom: 0; }
.ins-bubble--bot :deep(a) { color: var(--interactive); }

@media (max-width: 900px) {
  .ins-finding { grid-template-columns: minmax(0, 1fr); gap: 8px; }
  .ins-finding__actions { justify-content: flex-start; }
  .ins-convos--open { grid-template-columns: minmax(0, 1fr); }
}
</style>
