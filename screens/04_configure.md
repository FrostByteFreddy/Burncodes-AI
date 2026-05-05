# Screen: Configure (Settings)

## What's Wrong Now
- Three tabs (Appearance, Behavior, Rules) rendered as pill tabs inside the page — noisy
- Giant heading with gear icon is unnecessary decoration
- Appearance tab has a live chat preview embedded — too cramped
- Rules tab (fine-tune) has no explanation of what rules do
- No save state feedback beyond a toast

## New Design

### Layout
Two-column on desktop (settings | preview), single column stacked on mobile:

```
┌───────────────────────────────┬──────────────────────────────┐
│  SETTINGS PANEL (480px)       │  LIVE PREVIEW                │
│                               │  (chat widget preview,       │
│  [Left-side vertical nav]     │   updates in real-time)      │
│  ─ Appearance                 │                              │
│  ─ Behavior                   │                              │
│  ─ Rules                      │                              │
│  ─ Advanced                   │                              │
│                               │                              │
│  [Section content below]      │                              │
└───────────────────────────────┴──────────────────────────────┘
```

- Settings panel: scrollable, sticky preview column
- Section navigation: **left-aligned vertical list** (not pill tabs), 14px, active = indigo left border, no background fill
- Preview: `--surface-0` bg, 375px max-width mock phone frame, or just floating widget

### Appearance Section
Groups, not just a list of fields:

**Identity**
- Chatbot name (text input)
- Intro message (textarea, 3 rows)

**Visual**
- Primary color (color picker + hex input)
- Widget position (left/right toggle pill)
- Avatar (upload or initials fallback)

**Crawl Mode**  ← replaces confusing "indexing mode" label
- Pill toggle: `Standard (Playwright)` / `Fast (No AI)` / `Full AI`
- Small description under each option

### Behavior Section
- System persona (large textarea, monospace hint, 200 char counter)
- RAG prompt template (large textarea, with placeholder showing variables like `{{context}}`)
- Response language (select: Auto / DE / EN / FR)
- Translation target (select: none / DE / EN / FR)

### Rules Section
- Replaces "fine-tune rules" label with **"Response Rules"**
- Each rule shown as a card:

```
┌──────────────────────────────────────────────────┐
│  If user says:  "pricing"                        │
│  Always reply:  "Please contact our sales team…" │
│                                          [Edit] [✕] │
└──────────────────────────────────────────────────┘
```
- `+ Add Rule` button at bottom, expands an inline form (no modal)
- Rule explanation at top: "Rules override the AI's default behavior for specific triggers."

### Save Button
- Sticky at bottom of settings panel
- Disabled + greyed when no changes
- Shows spinner inline during save
- On success: brief green checkmark animation, reverts to normal
