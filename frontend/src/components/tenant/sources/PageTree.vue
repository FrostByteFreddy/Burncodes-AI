<template>
  <div class="pt">
    <div class="pt__filter">
      <font-awesome-icon :icon="['fas', 'magnifying-glass']" class="pt__filter-icon" />
      <input v-model.trim="query" type="search" class="pt__filter-input" :placeholder="$t('knowledge.content.filter')" :aria-label="$t('knowledge.content.filter')" />
    </div>

    <div class="pt__table" role="treegrid" :aria-label="$t('knowledge.content.title')">
      <div class="pt__row pt__row--head" role="row">
        <span role="columnheader">{{ $t('knowledge.tree.page') }}</span>
        <span role="columnheader" class="pt__col">{{ $t('knowledge.tree.chunks') }}</span>
        <span role="columnheader" class="pt__col pt__col--date">{{ $t('knowledge.tree.changed') }}</span>
        <span role="columnheader" class="pt__col pt__col--date">{{ $t('knowledge.tree.crawled') }}</span>
        <span></span>
      </div>

      <div
        v-for="row in visibleRows"
        :key="row.key"
        role="row"
        class="pt__row"
        :class="{ 'pt__row--host': row.depth === 0 }"
        :aria-level="row.depth + 1"
        :aria-expanded="row.children.length ? isOpen(row) : undefined"
      >
        <div class="pt__name" role="gridcell" :style="{ paddingLeft: `${row.depth * 18}px` }">
          <button
            v-if="row.children.length"
            class="pt__chevron"
            :aria-label="row.label"
            @click="toggle(row.key)"
          >
            <font-awesome-icon :icon="['fas', isOpen(row) ? 'chevron-down' : 'chevron-right']" />
          </button>
          <span v-else class="pt__chevron-spacer"></span>

          <span class="pt__icon" :class="`pt__icon--${row.kind}`">
            <font-awesome-icon :icon="['fas', row.icon]" />
          </span>
          <span class="pt__label" :title="row.source?.summary || row.url || row.label">{{ row.display }}</span>
          <span v-if="row.children.length" class="pt__count">{{ row.pageCount }}</span>
          <span
            v-if="row.source && row.source.status !== 'COMPLETED'"
            class="pt__status"
            :class="`pt__status--${row.source.status.toLowerCase()}`"
          >{{ statusLabel(row.source) }}</span>
        </div>

        <span role="gridcell" class="pt__col">{{ row.source ? fmtChunks(row.source.indexed_chunks) : (row.chunkTotal || '–') }}</span>
        <span role="gridcell" class="pt__col pt__col--date">{{ fmtDate(row.source ? row.source.last_changed_at : row.lastChanged) }}</span>
        <span role="gridcell" class="pt__col pt__col--date">{{ fmtDate(row.source ? (row.source.last_seen_at || row.source.created_at) : row.lastCrawled) }}</span>
        <span role="gridcell" class="pt__open-cell">
          <a
            v-if="row.url"
            :href="row.url"
            target="_blank"
            rel="noopener noreferrer"
            class="pt__open"
            :title="$t('knowledge.tree.open')"
            :aria-label="`${$t('knowledge.tree.open')}: ${row.url}`"
          >
            <font-awesome-icon :icon="['fas', 'arrow-up-right-from-square']" />
          </a>
        </span>
      </div>

      <p v-if="query && !visibleRows.length" class="pt__empty">{{ $t('knowledge.content.noMatch', { q: query }) }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

const props = defineProps({
  // URL and FILE_URL sources of the tenant
  sources: { type: Array, default: () => [] },
});
const { t, locale } = useI18n();
const query = ref('');

const FILE_ICONS = {
  pdf: 'file-pdf', doc: 'file-word', docx: 'file-word', xls: 'file-excel', xlsx: 'file-excel',
  ppt: 'file-powerpoint', pptx: 'file-powerpoint', txt: 'file-lines', md: 'file-lines', csv: 'file-csv',
  png: 'file-image', jpg: 'file-image', jpeg: 'file-image', gif: 'file-image', webp: 'file-image', zip: 'file-zipper',
};
const STATUS_RANK = { COMPLETED: 3, PROCESSING: 2, QUEUED: 2, SKIPPED: 2, ERROR: 1, UNSUPPORTED: 1 };

// Older crawls stored the same URL several times; show each URL once,
// preferring the indexed (then newest) row.
const uniqueSources = computed(() => {
  const best = new Map();
  for (const s of props.sources) {
    const cur = best.get(s.source_location);
    const rank = STATUS_RANK[s.status] || 0;
    const curRank = cur ? STATUS_RANK[cur.status] || 0 : -1;
    if (!cur || rank > curRank || (rank === curRank && s.id > cur.id)) best.set(s.source_location, s);
  }
  return [...best.values()];
});

const extOf = (url) => {
  try {
    const last = new URL(url).pathname.split('/').pop() || '';
    return last.includes('.') ? last.split('.').pop().toLowerCase() : '';
  } catch { return ''; }
};
const decode = (seg) => { try { return decodeURIComponent(seg); } catch { return seg; } };
const maxIso = (a, b) => (!a ? b : !b ? a : (a > b ? a : b));

const newNode = (key, label, depth, url) => ({
  key, label, depth, url, source: null, childMap: new Map(), children: [],
  pageCount: 0, chunkTotal: 0, lastChanged: null, lastCrawled: null, matches: true,
});

const roots = computed(() => {
  const hosts = new Map();
  for (const src of uniqueSources.value) {
    let parsed;
    try { parsed = new URL(src.source_location); } catch { continue; }
    const host = parsed.host;
    if (!hosts.has(host)) hosts.set(host, newNode(host, host, 0, `${parsed.protocol}//${host}/`));
    let node = hosts.get(host);
    let path = '';
    parsed.pathname.split('/').filter(Boolean).forEach((seg, i) => {
      path += `/${seg}`;
      const key = host + path;
      if (!node.childMap.has(key)) node.childMap.set(key, newNode(key, decode(seg), i + 1, null));
      node = node.childMap.get(key);
    });
    node.source = src;
    node.url = src.source_location;
  }

  const q = query.value.toLowerCase();
  const finish = (node) => {
    const isFile = node.source?.source_type === 'FILE_URL';
    node.kind = node.depth === 0 ? 'host' : isFile ? 'file' : node.source ? 'page' : 'folder';
    node.icon = node.kind === 'host' ? 'globe'
      : node.kind === 'file' ? (FILE_ICONS[extOf(node.url)] || 'file')
      : node.kind === 'folder' ? 'folder' : 'file-code';
    node.display = node.depth > 0 && node.source?.title ? node.source.title : node.label;

    node.children = [...node.childMap.values()];
    node.children.forEach(finish);
    node.children.sort((a, b) => ((a.kind === 'file') - (b.kind === 'file')) || a.display.localeCompare(b.display, undefined, { numeric: true }));

    let pages = node.source ? 1 : 0;
    let chunks = node.source?.indexed_chunks || 0;
    let changed = node.source?.last_changed_at || null;
    let crawled = node.source ? (node.source.last_seen_at || node.source.created_at) : null;
    let childMatch = false;
    for (const c of node.children) {
      pages += c.pageCount;
      chunks += c.chunkTotal;
      changed = maxIso(changed, c.lastChanged);
      crawled = maxIso(crawled, c.lastCrawled);
      childMatch = childMatch || c.matches;
    }
    const selfMatch = !q || `${node.display} ${node.label} ${node.url || ''}`.toLowerCase().includes(q);
    Object.assign(node, {
      pageCount: pages, chunkTotal: chunks, lastChanged: changed, lastCrawled: crawled,
      matches: selfMatch || childMatch, childMatch,
    });
  };
  const list = [...hosts.values()].sort((a, b) => a.label.localeCompare(b.label));
  list.forEach(finish);
  return list;
});

// Hosts start open, deeper levels closed. While filtering, every level that
// leads to a match is open.
const expanded = ref(new Set());
watch(roots, (r) => {
  if (!expanded.value.size) expanded.value = new Set(r.map((h) => h.key));
}, { immediate: true });
const isOpen = (row) => (query.value ? row.childMatch : expanded.value.has(row.key));
const toggle = (key) => {
  const next = new Set(expanded.value);
  next.has(key) ? next.delete(key) : next.add(key);
  expanded.value = next;
};

const visibleRows = computed(() => {
  const out = [];
  const walk = (node) => {
    if (!node.matches) return;
    out.push(node);
    if (isOpen(node)) node.children.forEach(walk);
  };
  roots.value.forEach(walk);
  return out;
});

const statusLabel = (s) => t(`knowledge.tree.status.${s.status}`) + (s.status === 'ERROR' && s.status_code ? ` ${s.status_code}` : '');
const fmtChunks = (n) => (n === null || n === undefined ? '–' : n);
const fmtDate = (iso) => (iso ? new Date(iso).toLocaleDateString(locale.value, { day: '2-digit', month: '2-digit', year: 'numeric' }) : '–');
</script>

<style scoped>
.pt { display: flex; flex-direction: column; gap: 12px; }

.pt__filter { position: relative; max-width: 320px; }
.pt__filter-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); font-size: 12px; color: var(--surface-muted); }
.pt__filter-input {
  width: 100%; padding: 8px 12px 8px 32px; border-radius: var(--radius-md);
  border: 1px solid var(--surface-3); background: var(--surface-2);
  font-size: 14px; color: var(--surface-text); outline: none;
  transition: border-color var(--t-fast);
}
.pt__filter-input:focus { border-color: var(--brand-indigo); }

.pt__table { border: 1px solid var(--surface-3); border-radius: var(--radius-md); overflow: hidden; }
.pt__row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 72px 112px 112px 36px;
  align-items: center; gap: 12px;
  min-height: 40px; padding: 4px 12px;
  border-top: 1px solid var(--surface-3);
  font-size: 14px; color: var(--surface-text);
  transition: background var(--t-fast);
}
.pt__row:first-child { border-top: none; }
.pt__row:not(.pt__row--head):hover { background: var(--surface-2); }
.pt__row--head {
  min-height: 36px; background: var(--surface-2);
  font-size: 10px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--surface-muted);
}
.pt__row--host { font-weight: 600; color: var(--surface-heading); }

.pt__name { display: flex; align-items: center; gap: 8px; min-width: 0; }
.pt__chevron {
  width: 22px; height: 22px; flex-shrink: 0; padding: 0;
  display: inline-flex; align-items: center; justify-content: center;
  border: none; border-radius: var(--radius-sm); background: none; cursor: pointer;
  font-size: 10px; color: var(--surface-muted); transition: background var(--t-fast), color var(--t-fast);
}
.pt__chevron:hover { color: var(--surface-heading); background: var(--surface-3); }
.pt__chevron-spacer { width: 22px; flex-shrink: 0; }
.pt__icon {
  width: 26px; height: 26px; flex-shrink: 0; border-radius: var(--radius-sm);
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 12px; background: var(--surface-3); color: var(--surface-muted);
}
.pt__icon--host { background: rgba(10, 31, 171, 0.18); color: var(--brand-cyan); }
.pt__icon--file { background: rgba(255, 32, 149, 0.12); color: var(--brand-magenta); }
.pt__icon--page { color: var(--surface-text); }
.pt__label { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.pt__count {
  flex-shrink: 0; font-size: 11px; padding: 1px 8px; border-radius: var(--radius-pill);
  background: var(--surface-3); color: var(--surface-muted);
}
.pt__status {
  flex-shrink: 0; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: var(--radius-pill);
  background: var(--surface-3); color: var(--surface-muted);
}
.pt__status--error, .pt__status--unsupported { background: rgba(245, 158, 11, 0.12); color: var(--status-warning); }
.pt__status--processing, .pt__status--queued { background: rgba(10, 31, 171, 0.2); color: var(--brand-cyan); }

.pt__col { text-align: right; color: var(--surface-muted); font-variant-numeric: tabular-nums; white-space: nowrap; }
.pt__open-cell { display: flex; justify-content: center; }
.pt__open {
  width: 30px; height: 30px; border-radius: var(--radius-md);
  display: inline-flex; align-items: center; justify-content: center;
  color: var(--surface-muted); font-size: 12px; transition: color var(--t-fast), background var(--t-fast);
}
.pt__open:hover { color: var(--brand-cyan); background: var(--surface-3); }
.pt__empty { padding: 16px; font-size: 14px; color: var(--surface-muted); }

@media (max-width: 760px) {
  .pt__row { grid-template-columns: minmax(0, 1fr) 56px 36px; }
  .pt__col--date { display: none; }
  .pt__filter { max-width: none; }
}
</style>
