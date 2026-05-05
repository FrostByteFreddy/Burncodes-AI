# Screen: Insights

## What's Wrong Now
- Analytics page has a line chart but no at-a-glance KPIs
- Timeframe selector is a clunky set of buttons
- Chat logs tab is completely separate — adds navigation complexity
- No empty state when there are zero chats

## New Design

### Layout
Full-width, single scrollable column. No tabs.

### KPI Row (top)
Four stat cards in a row (2×2 on mobile):

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ 1,284       │  │ 47          │  │ CHF 2.14    │  │ 98ms        │
│ Total chats │  │ Today       │  │ Total cost  │  │ Avg latency │
└─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘
```

- Card bg: `--surface-1`, border `--surface-3`
- Value: 28px, 700 weight, `--surface-heading`
- Label: 12px, `--surface-muted`
- Trend indicator (↑ +12% vs last week) in small chip below value

### Chart Section
- Line chart using existing data / `analytics_time_buckets` RPC
- Timeframe selector: clean segmented pill — `24h · 7d · 30d · 90d`
  - Sits inside the chart card header, right-aligned
- Chart: indigo line with magenta area fill (gradient from `#FF209530` → transparent)
- Grid lines: `--surface-3`, no axis borders
- Tooltip: `--surface-1` bg, rounded, brand-indigo accent

### Recent Conversations (replaces separate Chat Logs tab)
A scrollable table below the chart:

```
┌─────────────────────────────────────────────────────────────────┐
│  RECENT CONVERSATIONS                                    [→ All] │
├───────────────┬──────────────────────────────┬──────────────────┤
│  Time         │  First message               │  Turns / Cost    │
├───────────────┼──────────────────────────────┼──────────────────┤
│  2h ago       │  "What are your pricing…"    │  4 · CHF 0.002   │
│  4h ago       │  "How do I integrate the…"  │  7 · CHF 0.005   │
└───────────────┴──────────────────────────────┴──────────────────┘
```

- Row hover: `--surface-2` bg
- Clicking a row expands it inline to show full conversation thread
- `[→ All]` button at top right shows all (paginated, same view expanded)

### Empty State
```
No conversations yet.
Share your chatbot link to start collecting insights.

[Copy chatbot link]   [Open chatbot ↗]
```
