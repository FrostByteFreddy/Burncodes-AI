# Screen: My Chatbots (ManageTenants)

## What's Wrong Now
- Giant `text-4xl` heading dominates the page for no reason
- Tenant cards are plain white boxes with no personality
- Empty state uses a generic folder icon
- "New Tenant" button is hidden next to a heading — easy to miss
- No indication of what a "tenant" actually is to new users

## New Design

### Page Header
- No giant H1 — sidebar active state already provides context
- Small section label: `MY CHATBOTS` in 11px uppercase tracking-widest, `--surface-muted`
- Inline `+ New Chatbot` button sits to the right of the label, pill-shaped, gradient fill

### Tenant Cards
Full-width cards in a single column (max-w 680px centered):

```
┌─────────────────────────────────────────────────────┐
│  ● [Indigo dot — online indicator]                  │
│  Name of Chatbot                    [Open ↗] [···]  │
│  ai.burn.codes/chat/uuid            [Configure →]   │
│  3 sources · Last crawled 2h ago                    │
│  ████████░░  72% knowledge indexed                  │
└─────────────────────────────────────────────────────┘
```

- Card bg: `--surface-1`, border `--surface-3` 1px
- Hover: subtle glow `0 0 0 1px #0A1FAB40, 0 8px 32px #0A1FAB18`
- Three-dot menu (···): Delete option (red), Rename
- `Open ↗` button: ghost, opens `/chat/:id` in new tab
- `Configure →` button: ghost, navigates to tenant configure screen
- Progress bar for indexing: `--brand-indigo` fill on `--surface-2` track, only shown when sources exist
- Status dot: green (`--status-success`) if has ≥1 completed source, else muted

### Empty State
Centered, no icon — just clean text + CTA:

```
No chatbots yet.
Create your first one to start building your AI knowledge base.

[+ Create Chatbot]   ← gradient pill button
```

### Loading State
- 2 ghost skeleton cards, `--surface-2` animated shimmer

### Micro-interactions
- New card appears from bottom with `opacity 0 → 1` + `translateY(8px → 0)`
- Delete: card collapses with height transition before removal
- Hover on card: `translateY(-2px)` lift
