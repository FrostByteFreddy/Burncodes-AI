# Screen: Sidebar Navigation

## What's Wrong Now
- Top navbar wastes vertical space and forces horizontal cramming
- Active state on nav links is barely visible
- User menu hidden in a tiny avatar dropdown
- No visual hierarchy between tenant-level nav and account-level nav
- Logo competes with navigation for attention

## New Design

### Layout
- **Fixed left sidebar**, 240px wide on desktop
- Collapses to icon-only rail (60px) on tablet, full-screen drawer on mobile
- Background: `--surface-1` (`#13162B`) with a subtle right border `--surface-3`

### Structure (top to bottom)

```
┌────────────────────────┐
│  [BURN logo, 36px]     │  → links to /manage-tenants
│                        │
│  ┌──────────────────┐  │
│  │ Tenant name    ▾ │  │  → pill dropdown to switch tenants, surface-2 bg
│  └──────────────────┘  │
│                        │
│  ── WORKSPACE ──────── │  section label: 10px / uppercase / muted
│                        │
│  ◈  Knowledge          │  icon + label, 14px medium
│  ⚙  Configure          │
│  ◉  Insights           │
│  ↗  Open Chatbot       │  opens in new tab, subtle external icon
│                        │
│  ── ACCOUNT ─────────  │
│                        │
│  ⊞  My Chatbots        │  → /manage-tenants
│                        │
│  ────────────────────  │  spacer pushes footer to bottom
│                        │
│  [Avatar initials]     │  24px circle, brand gradient fill
│  Name / email          │  truncated
│  ⚙ Settings           │  → /profile
│  💳 Billing            │  → /subscription
│  → Logout              │  text-error on hover
└────────────────────────┘
```

### Active State
- Active nav item: `--brand-indigo` left border (3px), `--gradient-brand-soft` background pill
- Text goes from `--surface-muted` → `--surface-heading`, weight 600
- Icon color transitions from muted to `--brand-cyan`

### Tenant Switcher Pill
- Small pill below logo, `--surface-2` bg
- Shows current tenant name, truncated at 18 chars
- Dropdown on click — lists all tenants, hoverable rows, current marked with indigo dot
- "＋ New Chatbot" at bottom of dropdown

### Micro-interactions
- Sidebar items: `transform: translateX(2px)` on hover (subtle nudge)
- Active indicator bar slides vertically with CSS transition when switching routes
- Tenant dropdown: fade + slight translateY(−4px) entrance

## What Stays the Same
- Router links and active-class logic (just restyled)
- Mobile menu concept (becomes bottom sheet drawer)
- Tenant watching/switching logic
