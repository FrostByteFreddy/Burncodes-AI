// Shared crawl-job helpers for the Knowledge list and the crawl detail page:
// readable activity rows, one-line summaries, and the job actions.
import { useI18n } from 'vue-i18n';
import apiClient from '@/utils/api';
import { useToast } from './useToast';

export const ACTIVE_STATUSES = ['IN_PROGRESS', 'SCANNED', 'INDEXING'];

// Start events are folded into their finishing event so each item is one row
const FINISHES = { scan: ['scanned'], learn_source: ['learned', 'learn_failed'] };
const FINISH_EVENTS = Object.values(FINISHES).flat();

export function useCrawlText() {
  const { t, locale } = useI18n();

  const fmtChf = (v) => Number(v || 0).toFixed(2);
  const fmtDateTime = (iso) => new Date(iso).toLocaleString(locale.value, {
    day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit',
  });
  const fmtTime = (iso) => new Date(iso).toLocaleTimeString(locale.value, { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  // "page" label for a URL: its title, else the most telling part of the path.
  // Many CMSs end URLs in an ID (…/entsorgen.html/299), so bare numbers are skipped.
  const pageLabel = (data = {}) => {
    if (data.title) return data.title;
    try {
      const u = new URL(data.url);
      const parts = u.pathname.split('/').filter(Boolean).map((p) => decodeURIComponent(p));
      const named = [...parts].reverse().find((p) => !/^\d+$/.test(p));
      if (!named) return u.host;
      return named.replace(/\.(html?|php|aspx?)$/i, '').replace(/[-_]+/g, ' ').trim() || u.host;
    } catch { return data.url || ''; }
  };

  const displayUrl = (url) => (url || '').replace(/^https?:\/\//, '').replace(/\/$/, '');

  function formatEntry(e) {
    const d = e.data || {};
    const page = pageLabel(d);
    switch (e.event) {
      case 'job_started':  return t('knowledge.log.job_started');
      case 'scan':         return t('knowledge.log.scan', { page });
      case 'scanned':      return t('knowledge.log.scanned', { page, outcome: t(`knowledge.estimate.${d.outcome}`, d.outcome || '') });
      case 'links_found':  return t('knowledge.log.links_found', { page, count: d.count });
      case 'scan_done':    return t('knowledge.log.scan_done', { n: d.to_learn, cost: fmtChf(d.cost_chf) });
      case 'learn_start':  return t('knowledge.log.learn_start', { n: d.count });
      case 'learn_source': return t('knowledge.log.learn_source', { page });
      case 'learned':      return t('knowledge.log.learned', { page, sections: d.sections, facts: d.facts, dates: d.dates });
      case 'learn_failed': return t('knowledge.log.learn_failed', { page, reason: d.reason });
      case 'job_done':     return t('knowledge.log.job_done', { n: d.learned, cost: fmtChf(d.cost_chf) });
      default:             return e.event;
    }
  }

  // One row per item: running items show their start event, finished items their result
  function foldLog(entries = []) {
    const finished = new Map();
    for (const e of entries) {
      for (const [start, ends] of Object.entries(FINISHES)) {
        if (ends.includes(e.event)) finished.set(`${start}:${e.data?.url}`, e);
      }
    }
    const rows = [];
    for (const e of entries) {
      // link counts read like a jumping progress counter; the pages themselves tell the story
      if (FINISH_EVENTS.includes(e.event) || e.event === 'links_found') continue;
      let entry = e;
      let state = 'info';
      if (FINISHES[e.event]) {
        const end = finished.get(`${e.event}:${e.data?.url}`);
        entry = end || e;
        state = !end ? 'running'
          : end.event === 'learn_failed' || ['error', 'refused'].includes(end.data?.outcome) ? 'failed'
          : 'done';
      } else if (e.event === 'job_done' || e.event === 'scan_done') {
        state = 'done';
      }
      rows.push({ id: e.id, created_at: entry.created_at, state, text: formatEntry(entry) });
    }
    return rows;
  }

  // Title of the page read last. While scanning nobody knows how big the site
  // is, so this shows that something is happening without pretending a total.
  function latestPage(entries = []) {
    const e = [...entries].reverse().find((x) => x.event === 'scanned' && x.data?.outcome !== 'error');
    return e ? pageLabel(e.data) : '';
  }

  // The page being worked on right now; counts like "12 new links" stay in the log
  function currentActivity(entries = []) {
    const running = [...foldLog(entries)].reverse().find((r) => r.state === 'running');
    return running?.text || '';
  }

  // One line describing a job, for the list
  function jobSummary(job) {
    const e = job.estimate || {};
    const r = job.report;
    if (job.status === 'COMPLETED' && r) {
      const c = r.counts || {};
      return t('knowledge.job.summaryDone', { learned: c.learned || 0, unchanged: c.unchanged || 0, cost: fmtChf(r.cost_chf) });
    }
    if (job.status === 'SCANNED') {
      return e.to_learn
        ? t('knowledge.job.summaryScanned', { n: e.to_learn, cost: fmtChf(e.cost_chf) })
        : t('knowledge.estimate.nothing');
    }
    if (job.status === 'FAILED') return t('knowledge.job.summaryStopped');
    return '';
  }

  return { fmtChf, fmtDateTime, fmtTime, pageLabel, displayUrl, formatEntry, foldLog, currentActivity, latestPage, jobSummary };
}

export function useCrawlActions(getTenantId) {
  const { t } = useI18n();
  const { addToast } = useToast();
  const fmtChf = (v) => Number(v || 0).toFixed(2);
  const base = (jobId) => `/tenants/${getTenantId()}/crawling_jobs/${jobId}`;

  async function confirm(job) {
    try {
      await apiClient.post(`${base(job.id)}/confirm`);
      addToast(t('knowledge.estimate.started'), 'success');
      return true;
    } catch (e) {
      if (e.response?.status === 402) {
        const d = e.response.data || {};
        addToast(t('knowledge.estimate.balanceLow', { balance: fmtChf(d.balance_chf), cost: fmtChf(d.estimate_chf) }), 'error');
      } else {
        addToast(e.response?.data?.error || t('knowledge.job.actionFailed'), 'error');
      }
      return false;
    }
  }

  async function stop(job) {
    try {
      await apiClient.post(`${base(job.id)}/cancel`);
      return true;
    } catch {
      addToast(t('knowledge.job.actionFailed'), 'error');
      return false;
    }
  }

  async function remove(job) {
    try {
      await apiClient.delete(base(job.id));
      return true;
    } catch {
      addToast(t('tenant.sources.actions.deleteFailed'), 'error');
      return false;
    }
  }

  return { confirm, stop, remove };
}
