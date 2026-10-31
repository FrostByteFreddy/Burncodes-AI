// The learning models a customer can pick when confirming an estimate, each
// with its price for this crawl (estimate.costs, computed by the backend).
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { formatCHF } from '@/utils/format';

export const LEARNING_MODELS = ['argon', 'lite'];

// getDefault: the chatbot's default model (its advanced settings), preselected
export function useLearningModels(getEstimate, getDefault = () => null) {
  const { t } = useI18n();
  const model = ref(LEARNING_MODELS.includes(getDefault()) ? getDefault() : 'argon');
  const costs = computed(() => getEstimate()?.costs || null);
  // estimates computed before the choice existed have one price only
  watch(costs, (c) => { if (c && !(model.value in c)) model.value = Object.keys(c)[0]; }, { immediate: true });

  const options = computed(() => (costs.value ? LEARNING_MODELS.filter((k) => k in costs.value).map((k) => ({
    value: k,
    title: t(`knowledge.models.${k}.title`),
    description: t(`knowledge.models.${k}.desc`),
    badge: `${t('ui.ca')} ${formatCHF(costs.value[k])}`,
  })) : []));
  const cost = computed(() => Number(costs.value?.[model.value] ?? getEstimate()?.cost_chf ?? 0));
  return { model, options, cost };
}
