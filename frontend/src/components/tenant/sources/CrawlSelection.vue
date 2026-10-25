<template>
  <div class="cs">
    <!-- Gemini's suggestions: one click each, with what it saves -->
    <section v-if="suggestions.length" class="cs__block">
      <h3 class="cs__heading">
        <font-awesome-icon :icon="['fas', 'wand-magic-sparkles']" class="cs__heading-icon" />
        {{ $t('knowledge.selection.suggestionsTitle') }}
      </h3>
      <p class="meta">{{ $t('knowledge.selection.suggestionsLede') }}</p>
      <ul class="cs__suggestions">
        <li v-for="s in suggestions" :key="s.folder" class="cs__suggestion" :class="{ 'cs__suggestion--done': s.done }">
          <div class="cs__suggestion-text">
            <p class="cs__suggestion-title">{{ s.label }}</p>
            <p class="cs__suggestion-reason">{{ s.reason }}</p>
            <p class="meta">
              {{ s.done
                ? $t('knowledge.selection.excludedSaves', { cost: fmtChf(s.saves) })
                : $t('knowledge.selection.saves', { n: s.count, cost: fmtChf(s.saves) }) }}
            </p>
          </div>
          <button v-if="s.done" type="button" class="btn-quiet" :disabled="saving" @click="restoreFolder(s.folder)">
            {{ $t('knowledge.selection.undo') }}
          </button>
          <button v-else type="button" class="btn-quiet cs__exclude" :disabled="saving" @click="setFolder(s.folder, false)">
            {{ $t('knowledge.selection.exclude') }}
          </button>
        </li>
      </ul>
    </section>

    <!-- What the sorting step set aside, by reason; each group can come back in -->
    <section v-if="skippedGroups.length" class="cs__block">
      <p>
        <strong>{{ $t('knowledge.estimate.skipped', { n: skippedTotal }) }}</strong>
        <span class="meta"> {{ $t('knowledge.selection.skippedLede') }}</span>
      </p>
      <ul class="cs__reasons">
        <li v-for="g in skippedGroups" :key="g.reason" class="cs__reason">
          <span>{{ $t(`knowledge.skipReasons.${g.reason}`) }} <span class="meta">({{ g.ids.length }})</span></span>
          <button type="button" class="cs__link" :disabled="saving" @click="setIds(g.ids, true)">{{ $t('knowledge.estimate.includeAll') }}</button>
        </li>
      </ul>
    </section>

    <!-- The folder tree: tick and untick folders and single sources -->
    <section class="cs__block">
      <button type="button" class="cs__toggle" :aria-expanded="showTree" @click="showTree = !showTree">
        <font-awesome-icon :icon="['fas', showTree ? 'chevron-down' : 'chevron-right']" />
        {{ $t('knowledge.selection.adjust') }}
      </button>
      <template v-if="showTree">
        <p class="meta">{{ $t('knowledge.selection.adjustLede') }}</p>
        <div class="cs__filter">
          <font-awesome-icon :icon="['fas', 'magnifying-glass']" class="cs__filter-icon" />
          <input v-model.trim="query" type="search" class="cs__filter-input" :placeholder="$t('knowledge.selection.search')" :aria-label="$t('knowledge.selection.search')" />
        </div>

        <div v-if="!items" class="cs__table">
          <div v-for="n in 6" :key="n" class="cs__row"><span class="cs__ghost"></span></div>
        </div>
        <div v-else class="cs__table" role="tree" :aria-label="$t('knowledge.selection.adjust')">
          <div
            v-for="row in rows"
            :key="row.key"
            class="cs__row"
            :class="{ 'cs__row--out': row.state === 'none' }"
            role="treeitem"
            :aria-level="row.depth + 1"
            :aria-expanded="row.hasChildren ? isOpen(row.key) : undefined"
          >
            <div class="cs__name" :style="{ paddingLeft: `${row.depth * 18}px` }">
              <button v-if="row.hasChildren" type="button" class="cs__chevron" :aria-label="row.label" @click="toggleOpen(row.key)">
                <font-awesome-icon :icon="['fas', isOpen(row.key) ? 'chevron-down' : 'chevron-right']" />
              </button>
              <span v-else class="cs__chevron-spacer"></span>
              <input
                type="checkbox"
                class="cs__check"
                :checked="row.state === 'all'"
                :indeterminate="row.state === 'some'"
                :disabled="saving"
                :aria-label="row.label"
                @change="onCheck(row, $event.target.checked)"
              />
              <span class="cs__icon" :class="`cs__icon--${row.kind}`"><font-awesome-icon :icon="['fas', ICONS[row.kind]]" /></span>
              <a v-if="row.url" :href="row.url" target="_blank" rel="noopener noreferrer" class="cs__label" :title="row.url">{{ row.label }}</a>
              <span v-else class="cs__label">{{ row.label }}</span>
              <span v-if="row.count > 1" class="cs__count">{{ row.count }}</span>
              <span v-if="row.reason" class="cs__badge">{{ $t(`knowledge.skipReasons.${row.reason}`) }}</span>
              <span v-else-if="row.indexOnly" class="cs__badge cs__badge--info">{{ $t('knowledge.selection.indexOnly') }}</span>
            </div>
            <span class="cs__cost">{{ row.state === 'none' ? '–' : `CHF ${fmtChf(row.cost)}` }}</span>
          </div>
          <p v-if="query && !rows.length" class="cs__empty">{{ $t('knowledge.content.noMatch', { q: query }) }}</p>
        </div>
      </template>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import apiClient from '@/utils/api';
import { useToast } from '@/composables/useToast';
import { useCrawlText } from '@/composables/useCrawl';

const props = defineProps({
  base: { type: String, required: true },          // /tenants/<id>/crawling_jobs/<id>
  host: { type: String, default: '' },
});
const emit = defineEmits(['estimate']);
const { t, locale } = useI18n();
const { addToast } = useToast();
const { fmtChf, pageLabel } = useCrawlText();

const ICONS = { folder: 'folder', page: 'file-lines', file: 'file-pdf' };
const SKIP_ORDER = ['archive_finance', 'old_minutes', 'outdated', 'older_version', 'internal', 'manual', 'other'];

const items = ref(null);
const recommendations = ref([]);
const saving = ref(false);
const showTree = ref(false);
const query = ref('');
const open = reactive(new Set(['/']));

onMounted(async () => {
  try {
    const { data } = await apiClient.get(`${props.base}/selection`);
    items.value = data.items;
    recommendations.value = data.recommendations || [];
  } catch { items.value = []; }
});

// ── Folders: '/a/b' lies under '/a'; other hosts start with '//host' ──
const under = (folder, path) => folder === path || folder.startsWith(`${path.replace(/\/$/, '')}/`);
const parentOf = (path) => {
  if (path === '/') return null;
  const cut = path.lastIndexOf('/');
  if (path.startsWith('//')) return cut <= 1 ? null : path.slice(0, cut);
  return cut <= 0 ? '/' : path.slice(0, cut);
};
const segmentLabel = (path) => {
  const seg = decodeURIComponent(path.split('/').filter(Boolean).pop() || '');
  const words = seg.replace(/\.(html?|php|aspx?)$/i, '').replace(/[-_]+/g, ' ').trim() || seg;
  return words.charAt(0).toUpperCase() + words.slice(1);
};

const tree = computed(() => {
  const nodes = new Map();
  const node = (path) => {
    if (nodes.has(path)) return nodes.get(path);
    const n = { key: path, path, page: null, leaves: [], children: [], items: [] };
    nodes.set(path, n);
    const parent = parentOf(path);
    if (parent !== null) node(parent).children.push(n);
    return n;
  };
  node('/');
  for (const it of items.value || []) {
    const n = node(it.folder);
    if (it.kind === 'page' && !n.page) n.page = it;
    else n.leaves.push(it);
  }
  // totals bottom-up: every source below a folder, and what its selected part costs
  const sum = (n) => {
    n.items = [...(n.page ? [n.page] : []), ...n.leaves];
    for (const c of n.children) n.items.push(...sum(c));
    n.total = n.items.reduce((a, i) => a + i.cost, 0);
    n.children.sort((a, b) => b.total - a.total);
    n.leaves.sort((a, b) => b.cost - a.cost);
    return n.items;
  };
  sum(nodes.get('/'));
  const roots = [nodes.get('/'), ...[...nodes.values()].filter((n) => n.path.startsWith('//') && parentOf(n.path) === null)];
  return { nodes, roots: roots.filter((r) => r.items.length) };
});

const stateOf = (list) => {
  const n = list.filter((i) => i.selected).length;
  return n === 0 ? 'none' : n === list.length ? 'all' : 'some';
};
const costOf = (list) => list.reduce((a, i) => a + (i.selected ? i.cost : 0), 0);
const reasonOf = (list) => {
  const reasons = new Set(list.map((i) => (i.selected ? null : i.reason || 'other')));
  return reasons.size === 1 && !reasons.has(null) ? [...reasons][0] : null;
};

const leafRow = (it, depth) => ({
  key: `s${it.id}`, depth, kind: it.kind, ids: [it.id], item: it, url: it.url, hasChildren: false, count: 1,
  label: it.title || pageLabel({ url: it.url }),
  state: it.selected ? 'all' : 'none', cost: it.selected ? it.cost : 0,
  reason: it.selected ? null : it.reason || 'other', indexOnly: it.index_only,
});

const folderRow = (n, depth) => {
  const hasChildren = n.children.length > 0 || n.leaves.length > 0;
  return {
    key: n.path, depth, kind: n.page ? 'page' : 'folder', folder: n.path, hasChildren, count: n.items.length,
    url: n.page?.url, item: !hasChildren ? n.page : null,
    label: n.path === '/' ? (n.page?.title || props.host || t('knowledge.selection.start'))
      : n.path.startsWith('//') && parentOf(n.path) === null ? n.path.slice(2)
      : n.page?.title || segmentLabel(n.path),
    state: stateOf(n.items), cost: costOf(n.items), reason: reasonOf(n.items),
    indexOnly: !hasChildren && n.page?.index_only,
  };
};

const isOpen = (key) => open.has(key);
const toggleOpen = (key) => (open.has(key) ? open.delete(key) : open.add(key));

const rows = computed(() => {
  if (!items.value) return [];
  const q = query.value.toLowerCase();
  if (q) {
    // searching: a flat list of matches, most expensive first
    return items.value
      .filter((i) => (i.title || '').toLowerCase().includes(q) || i.url.toLowerCase().includes(q))
      .sort((a, b) => b.cost - a.cost).slice(0, 200).map((i) => leafRow(i, 0));
  }
  const out = [];
  const walk = (n, depth) => {
    out.push(folderRow(n, depth));
    if (!open.has(n.path)) return;
    for (const c of n.children) walk(c, depth + 1);
    for (const it of n.leaves) out.push(leafRow(it, depth + 1));
  };
  for (const r of tree.value.roots) walk(r, 0);
  return out;
});

// ── Suggestions ──
const suggestions = computed(() => {
  if (!items.value) return [];
  return recommendations.value.map((r) => {
    const list = (items.value || []).filter((i) => under(i.folder, r.folder));
    const done = list.length > 0 && list.every((i) => !i.selected);
    return {
      folder: r.folder, done, count: list.filter((i) => i.selected).length,
      saves: list.reduce((a, i) => a + (done || i.selected ? i.cost : 0), 0),
      label: r.title || segmentLabel(r.folder),
      reason: r.reason?.[locale.value] || r.reason?.en || '',
    };
  }).filter((s) => s.done || s.count > 0);
});

// ── Sorted out by reason ──
const skippedGroups = computed(() => {
  const groups = {};
  for (const i of items.value || []) if (!i.selected) (groups[i.reason || 'other'] ||= []).push(i.id);
  return SKIP_ORDER.filter((r) => groups[r]).map((reason) => ({ reason, ids: groups[reason] }));
});
const skippedTotal = computed(() => skippedGroups.value.reduce((a, g) => a + g.ids.length, 0));

// ── Saving: optimistic, one change at a time ──
const save = async (body, apply) => {
  const before = items.value.map((i) => ({ selected: i.selected, reason: i.reason }));
  apply();
  saving.value = true;
  try {
    const { data } = await apiClient.post(`${props.base}/selection`, body);
    emit('estimate', data.estimate);
  } catch {
    items.value.forEach((i, k) => Object.assign(i, before[k]));
    addToast(t('knowledge.selection.saveFailed'), 'error');
  } finally {
    saving.value = false;
  }
};
const mark = (list, selected) => {
  for (const i of list) {
    i.selected = selected;
    i.reason = selected ? null : 'manual';
  }
};
const setFolder = (folder, selected) => save(
  selected ? { include_folders: [folder] } : { exclude_folders: [folder] },
  () => mark(items.value.filter((i) => under(i.folder, folder)), selected),
);
const restoreFolder = (folder) => save(
  { restore_folders: [folder] },
  () => mark(items.value.filter((i) => under(i.folder, folder) && i.reason === 'manual'), true),
);
const setIds = (ids, selected) => {
  const set = new Set(ids);
  return save(selected ? { include: ids } : { exclude: ids }, () => mark(items.value.filter((i) => set.has(i.id)), selected));
};
const onCheck = (row, checked) => (row.folder && row.hasChildren ? setFolder(row.folder, checked) : setIds(row.ids || [row.item.id], checked));
</script>

<style scoped>
.cs { display: flex; flex-direction: column; gap: 18px; border-top: 1px solid var(--surface-3); padding-top: 16px; }
.cs__block { display: flex; flex-direction: column; gap: 10px; }
.cs__heading { display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 700; color: var(--surface-heading); }
.cs__heading-icon { color: var(--ai); }

.cs__suggestions { list-style: none; padding: 0; display: flex; flex-direction: column; gap: 8px; }
.cs__suggestion {
  display: flex; align-items: center; gap: 16px; justify-content: space-between;
  padding: 12px 14px; border-radius: var(--radius-md);
  background: var(--ai-soft); border: 1px solid transparent;
}
.cs__suggestion--done { background: var(--surface-2); border-color: var(--surface-3); }
.cs__suggestion--done .cs__suggestion-title { color: var(--surface-muted); text-decoration: line-through; }
.cs__suggestion-text { min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.cs__suggestion-title { font-weight: 600; color: var(--surface-heading); overflow-wrap: anywhere; }
.cs__suggestion-reason { font-size: 14px; color: var(--surface-text); max-width: var(--measure); }
.cs__exclude { flex-shrink: 0; }

.cs__reasons { list-style: none; padding: 0; display: flex; flex-wrap: wrap; gap: 8px 20px; font-size: 14px; }
.cs__reason { display: inline-flex; gap: 10px; align-items: baseline; }
.cs__link { background: none; border: none; padding: 0; cursor: pointer; font-size: 13px; font-weight: 600; color: var(--interactive); }
.cs__link:hover:not(:disabled) { text-decoration: underline; }
.cs__link:disabled { opacity: 0.5; cursor: default; }

.cs__toggle {
  align-self: flex-start; display: inline-flex; align-items: center; gap: 8px;
  background: none; border: none; padding: 0; cursor: pointer;
  font-size: 15px; font-weight: 700; color: var(--surface-heading);
}
.cs__toggle svg { font-size: 11px; color: var(--surface-muted); }

.cs__filter { position: relative; max-width: 320px; }
.cs__filter-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); font-size: 12px; color: var(--surface-muted); }
.cs__filter-input {
  width: 100%; padding: 9px 12px 9px 34px; border-radius: var(--radius-md);
  border: 1px solid var(--surface-3); background: var(--surface-2);
  font-size: 13px; color: var(--surface-text); outline: none;
}
.cs__filter-input:focus { border-color: var(--brand-indigo); }

.cs__table { border: 1px solid var(--surface-3); border-radius: var(--radius-md); max-height: 520px; overflow-y: auto; }
.cs__row {
  display: grid; grid-template-columns: minmax(0, 1fr) 96px; align-items: center; gap: 12px;
  min-height: 40px; padding: 4px 12px; border-top: 1px solid var(--surface-3);
  font-size: 13px; color: var(--surface-text);
}
.cs__row:first-child { border-top: none; }
.cs__row:hover { background: var(--surface-2); }
.cs__row--out .cs__label { color: var(--surface-muted); }
.cs__name { display: flex; align-items: center; gap: 8px; min-width: 0; }
.cs__chevron {
  width: 22px; height: 22px; flex-shrink: 0; padding: 0;
  display: inline-flex; align-items: center; justify-content: center;
  border: none; border-radius: var(--radius-sm); background: none; cursor: pointer;
  font-size: 10px; color: var(--surface-muted);
}
.cs__chevron:hover { color: var(--surface-heading); background: var(--surface-3); }
.cs__chevron-spacer { width: 22px; flex-shrink: 0; }
.cs__check { width: 16px; height: 16px; flex-shrink: 0; accent-color: var(--interactive); cursor: pointer; }
.cs__icon {
  width: 24px; height: 24px; flex-shrink: 0; border-radius: var(--radius-sm);
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 11px; background: var(--surface-3); color: var(--surface-muted);
}
.cs__icon--file { background: rgba(255, 32, 149, 0.12); color: var(--brand-magenta); }
.cs__label { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: inherit; text-decoration: none; }
a.cs__label:hover { color: var(--interactive); text-decoration: underline; }
.cs__count { flex-shrink: 0; font-size: 11px; padding: 1px 8px; border-radius: var(--radius-pill); background: var(--surface-3); color: var(--surface-muted); }
.cs__badge { flex-shrink: 0; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: var(--radius-pill); background: var(--surface-3); color: var(--surface-muted); }
.cs__badge--info { background: var(--interactive-soft); color: var(--interactive); }
.cs__cost { text-align: right; color: var(--surface-muted); font-variant-numeric: tabular-nums; white-space: nowrap; }
.cs__empty { padding: 16px; font-size: 13px; color: var(--surface-muted); }
.cs__ghost { display: block; height: 12px; width: 60%; border-radius: var(--radius-sm); background: var(--surface-3); }

@media (max-width: 760px) {
  .cs__suggestion { flex-direction: column; align-items: stretch; }
  .cs__filter { max-width: none; }
  .cs__row { grid-template-columns: minmax(0, 1fr) 72px; }
}
</style>
