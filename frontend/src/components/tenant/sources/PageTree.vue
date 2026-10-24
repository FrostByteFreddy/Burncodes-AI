<template>
  <div class="pt">
    <div class="pt__head">
      <span>Page</span>
      <span class="pt__col">Chunks</span>
      <span class="pt__col">Last changed</span>
      <span class="pt__col">Last crawled</span>
      <span class="pt__col-link"></span>
    </div>

    <div
      v-for="row in visibleRows"
      :key="row.key"
      class="pt__row"
      :class="{ 'pt__row--folder': row.children.length, 'pt__row--host': row.depth === 0 }"
      :style="{ '--depth': row.depth }"
    >
      <div class="pt__name">
        <button
          v-if="row.children.length"
          class="pt__chevron"
          :aria-expanded="expanded.has(row.key)"
          :aria-label="(expanded.has(row.key) ? 'Collapse ' : 'Expand ') + row.label"
          @click="toggle(row.key)"
        >
          <font-awesome-icon :icon="['fas', expanded.has(row.key) ? 'chevron-down' : 'chevron-right']" />
        </button>
        <span v-else class="pt__chevron-spacer"></span>

        <font-awesome-icon :icon="['fas', iconFor(row)]" class="pt__icon" :class="`pt__icon--${kindOf(row)}`" />
        <span
          v-if="row.source"
          class="status-dot pt__dot"
          :class="statusClass(row.source)"
          :title="statusTitle(row.source)"
        ></span>
        <span class="pt__label" :title="row.source?.summary || row.url">
          {{ row.source?.title && row.depth > 0 ? row.source.title : row.label }}
        </span>
        <span v-if="row.children.length" class="pt__count">{{ row.pageCount }}</span>
      </div>

      <span class="pt__col" :title="row.source ? '' : 'Total for this level'">
        {{ row.source ? fmtChunks(row.source.indexed_chunks) : (row.chunkTotal || '–') }}
      </span>
      <span class="pt__col">{{ fmtDate(row.source ? row.source.last_changed_at : row.lastChanged) }}</span>
      <span class="pt__col">{{ fmtDate(row.source ? (row.source.last_seen_at || row.source.created_at) : row.lastCrawled) }}</span>
      <span class="pt__col-link">
        <a
          v-if="row.url"
          :href="row.url"
          target="_blank"
          rel="noopener noreferrer"
          class="pt__open"
          :title="`Open ${row.url}`"
          :aria-label="`Open ${row.url} in a new tab`"
        >
          <font-awesome-icon :icon="['fas', 'arrow-up-right-from-square']" />
        </a>
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';

const props = defineProps({
  // URL and FILE_URL sources of the tenant
  sources: { type: Array, default: () => [] },
});

const FILE_ICONS = {
  pdf: 'file-pdf', doc: 'file-word', docx: 'file-word', xls: 'file-excel', xlsx: 'file-excel',
  ppt: 'file-powerpoint', pptx: 'file-powerpoint', txt: 'file-lines', md: 'file-lines', csv: 'file-csv',
  png: 'file-image', jpg: 'file-image', jpeg: 'file-image', gif: 'file-image', webp: 'file-image', zip: 'file-zipper',
};
const STATUS_RANK = { COMPLETED: 3, PROCESSING: 2, QUEUED: 2, ERROR: 1, UNSUPPORTED: 1 };

// Older crawls stored the same URL several times; show each URL once,
// preferring the indexed (then newest) row.
const uniqueSources = computed(() => {
  const best = new Map();
  for (const s of props.sources) {
    const cur = best.get(s.source_location);
    if (!cur
      || (STATUS_RANK[s.status] || 0) > (STATUS_RANK[cur.status] || 0)
      || ((STATUS_RANK[s.status] || 0) === (STATUS_RANK[cur.status] || 0) && s.id > cur.id)) {
      best.set(s.source_location, s);
    }
  }
  return [...best.values()];
});

const newNode = (key, label, depth, url) => ({
  key, label, depth, url, source: null, childMap: new Map(), children: [],
  pageCount: 0, chunkTotal: 0, lastChanged: null, lastCrawled: null,
});

const maxIso = (a, b) => (!a ? b : !b ? a : (a > b ? a : b));

const roots = computed(() => {
  const hosts = new Map();
  for (const src of uniqueSources.value) {
    let parsed;
    try { parsed = new URL(src.source_location); } catch { continue; }
    const host = parsed.host;
    if (!hosts.has(host)) hosts.set(host, newNode(host, host, 0, `${parsed.protocol}//${host}/`));
    let node = hosts.get(host);
    const segments = parsed.pathname.split('/').filter(Boolean);
    let path = '';
    segments.forEach((seg, i) => {
      path += `/${seg}`;
      const key = host + path;
      if (!node.childMap.has(key)) {
        let label = seg;
        try { label = decodeURIComponent(seg); } catch { /* keep raw */ }
        node.childMap.set(key, newNode(key, label, i + 1, null));
      }
      node = node.childMap.get(key);
    });
    node.source = src;
    node.url = src.source_location;
  }

  // Finalise: sort children (folders/pages first, files last) and aggregate stats
  const finish = (node) => {
    node.children = [...node.childMap.values()].sort((a, b) => {
      const fa = kindOf(a) === 'file', fb = kindOf(b) === 'file';
      if (fa !== fb) return fa ? 1 : -1;
      return a.label.localeCompare(b.label, undefined, { numeric: true });
    });
    let pages = node.source ? 1 : 0;
    let chunks = node.source?.indexed_chunks || 0;
    let changed = node.source?.last_changed_at || null;
    let crawled = node.source ? (node.source.last_seen_at || node.source.created_at) : null;
    for (const child of node.children) {
      finish(child);
      pages += child.pageCount;
      chunks += child.chunkTotal;
      changed = maxIso(changed, child.lastChanged);
      crawled = maxIso(crawled, child.lastCrawled);
    }
    Object.assign(node, { pageCount: pages, chunkTotal: chunks, lastChanged: changed, lastCrawled: crawled });
  };
  const list = [...hosts.values()].sort((a, b) => a.label.localeCompare(b.label));
  list.forEach(finish);
  return list;
});

// Expansion state: hosts start open, everything below starts closed
const expanded = ref(new Set());
watch(roots, (r) => {
  for (const host of r) if (!expanded.value.has(host.key)) expanded.value.add(host.key);
}, { immediate: true });

const toggle = (key) => {
  const next = new Set(expanded.value);
  next.has(key) ? next.delete(key) : next.add(key);
  expanded.value = next;
};

// Only rows whose ancestors are all expanded are rendered
const visibleRows = computed(() => {
  const out = [];
  const walk = (node) => {
    out.push(node);
    if (expanded.value.has(node.key)) node.children.forEach(walk);
  };
  roots.value.forEach(walk);
  return out;
});

const extOf = (row) => {
  const loc = row.source?.source_location || row.url || '';
  try {
    const last = new URL(loc).pathname.split('/').pop() || '';
    return last.includes('.') ? last.split('.').pop().toLowerCase() : '';
  } catch { return ''; }
};
function kindOf(row) {
  if (row.depth === 0) return 'host';
  if (row.source?.source_type === 'FILE_URL') return 'file';
  return row.children?.length && !row.source ? 'folder' : 'page';
}
const iconFor = (row) => {
  const kind = kindOf(row);
  if (kind === 'host') return 'globe';
  if (kind === 'file') return FILE_ICONS[extOf(row)] || 'file';
  if (kind === 'folder') return 'folder';
  return 'file-code';
};

const statusClass = (s) =>
  s.status === 'COMPLETED' ? 'status-dot--success'
  : s.status === 'ERROR' || s.status === 'UNSUPPORTED' ? 'status-dot--error'
  : 'status-dot--processing';
const statusTitle = (s) =>
  s.status === 'ERROR' ? `Error${s.status_code ? ` ${s.status_code}` : ''}`
  : s.status === 'UNSUPPORTED' ? 'File type not supported'
  : s.status === 'COMPLETED' ? 'Indexed'
  : 'Waiting to be learned';

const fmtChunks = (n) => (n === null || n === undefined ? '–' : n);
const fmtDate = (iso) => (iso
  ? new Date(iso).toLocaleDateString([], { day: '2-digit', month: '2-digit', year: '2-digit' })
  : '–');
</script>

<style scoped>
.pt { font-size: 12px; }
.pt__head, .pt__row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 56px 82px 82px 28px;
  align-items: center;
  gap: 8px;
  padding: 5px 8px;
}
.pt__head {
  font-size: 10px; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase;
  color: var(--surface-muted); border-bottom: 1px solid var(--surface-3);
}
.pt__row { border-radius: var(--radius-sm); transition: background var(--t-fast); }
.pt__row:hover { background: var(--surface-2); }
.pt__row--host { font-weight: 600; color: var(--surface-heading); }

.pt__name {
  display: flex; align-items: center; gap: 6px; min-width: 0;
  padding-left: calc(var(--depth) * 16px);
}
.pt__chevron {
  width: 18px; height: 18px; flex-shrink: 0;
  display: inline-flex; align-items: center; justify-content: center;
  border: none; background: none; cursor: pointer; padding: 0;
  font-size: 10px; color: var(--surface-muted); border-radius: var(--radius-sm);
}
.pt__chevron:hover { color: var(--surface-heading); background: var(--surface-3); }
.pt__chevron-spacer { width: 18px; flex-shrink: 0; }
.pt__icon { flex-shrink: 0; width: 13px; color: var(--surface-muted); }
.pt__icon--host { color: var(--brand-cyan); }
.pt__icon--file { color: var(--brand-magenta); }
.pt__dot { flex-shrink: 0; }
.pt__label {
  min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  color: var(--surface-text);
}
.pt__row--host .pt__label { color: var(--surface-heading); }
.pt__count {
  flex-shrink: 0; font-size: 10px; padding: 0 6px; border-radius: var(--radius-pill);
  background: var(--surface-2); color: var(--surface-muted);
}
.pt__col { text-align: right; color: var(--surface-muted); font-variant-numeric: tabular-nums; white-space: nowrap; }
.pt__col-link { display: flex; justify-content: center; }
.pt__open {
  width: 24px; height: 24px; display: inline-flex; align-items: center; justify-content: center;
  border-radius: var(--radius-sm); color: var(--surface-muted); font-size: 11px;
}
.pt__open:hover { color: var(--brand-cyan); background: var(--surface-3); }

/* Narrow screens: keep name, chunks and link */
@media (max-width: 640px) {
  .pt__head, .pt__row { grid-template-columns: minmax(0, 1fr) 44px 28px; }
  .pt__head > :nth-child(3), .pt__head > :nth-child(4),
  .pt__row > :nth-child(3), .pt__row > :nth-child(4) { display: none; }
}
</style>
