# Design System — SwiftAnswer Dashboard

## Brand Colors (from Login Screen)

```
Login gradient: #0A1FAB → #3B1FA8 → #FF2095
Logo gradient:  #50D3FC → #0A1FAB → #FF2095
CTA button:     #0A1FAB → #FF2095
```

## New Dashboard Palette

Derived from the login screen's indigo-to-magenta language, extended for a full product.

### Core Tokens

| Token | Hex | Usage |
|---|---|---|
| `--brand-indigo` | `#0A1FAB` | Primary actions, active states |
| `--brand-violet` | `#3B1FA8` | Gradient midpoint, hover states |
| `--brand-magenta` | `#FF2095` | Accents, destructive, badges |
| `--brand-cyan` | `#50D3FC` | Secondary highlights, tag chips |

### Surface Scale (Dark-tinted neutral, not generic grey)

| Token | Value | Usage |
|---|---|---|
| `--surface-0` | `#0D0F1A` | App background — deep navy-black |
| `--surface-1` | `#13162B` | Cards, panels |
| `--surface-2` | `#1C2040` | Input fields, hover rows |
| `--surface-3` | `#252A52` | Borders, dividers |
| `--surface-muted` | `#4A4F7A` | Placeholder text, captions |
| `--surface-text` | `#E8EAF6` | Body text |
| `--surface-heading` | `#FFFFFF` | Headings |

### Functional

| Token | Value | Usage |
|---|---|---|
| `--status-success` | `#00C9A7` | Completed, online |
| `--status-warning` | `#F59E0B` | In progress |
| `--status-error` | `#FF4444` | Error, failed |
| `--status-pending` | `#4A4F7A` | Queued, idle |

### Gradient Presets

```css
--gradient-brand: linear-gradient(135deg, #0A1FAB 0%, #FF2095 100%);
--gradient-brand-soft: linear-gradient(135deg, #0A1FAB22 0%, #FF209522 100%);
--gradient-surface: linear-gradient(180deg, #13162B 0%, #0D0F1A 100%);
--gradient-card-glow: linear-gradient(135deg, #0A1FAB15 0%, #FF209508 100%);
```

## Typography

**Font:** `Inter` (Google Fonts) — already very fitting for AI SaaS products

| Role | Size | Weight | Usage |
|---|---|---|---|
| Screen title | 20px | 600 | Page identifier in nav |
| Section label | 11px | 700 | Uppercase tracking, category separators |
| Card heading | 16px | 600 | Cards, list items |
| Body | 14px | 400 | Default prose |
| Caption | 12px | 400 | Metadata, timestamps |

**No more giant `text-4xl` headings on every page.** Navigation context replaces them.

## Layout Architecture

```
┌─────────────────────────────────────────────────────────┐
│  SIDEBAR (260px fixed, collapsible to 60px on mobile)   │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Logo                                           │   │
│  │  [Tenant selector pill]                         │   │
│  │  ─────────────────                              │   │
│  │  ○ Knowledge      (icon + label)                │   │
│  │  ○ Configure      (icon + label)                │   │
│  │  ○ Insights       (icon + label)                │   │
│  │  ─────────────────                              │   │
│  │  ○ My Chatbots                                  │   │
│  │  ─────────────────                              │   │
│  │  [Avatar] Name            ↗ Profile/Billing    │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  MAIN CONTENT AREA (flex-1, scrollable)                 │
│  ┌─────────────────────────────────────────────────┐   │
│  │  [Contextual page content — no big H1]          │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**Replace the top navbar with a left sidebar.** This is the standard for SaaS dashboards and solves the heading+tab hierarchy problem entirely. The sidebar carries the navigation context so pages don't need screaming H1s.

## Component Rules

- **No pill tabs** inside content pages — navigation lives in the sidebar
- **No page-level H1** — the sidebar active item IS the heading
- **Cards** use `--surface-1` background, 1px `--surface-3` border, 12px border-radius
- **Inputs** use `--surface-2` fill, `--surface-3` border, focus ring `--brand-indigo`
- **All primary buttons** use `--gradient-brand`, white text, no border
- **Status chips** are small (24px height), pill-shaped, color from `--status-*`
- **Section separators** are `--surface-3` lines, never bold headings
- **Subtle glow** on interactive cards on hover: `box-shadow: 0 0 0 1px #0A1FAB40, 0 8px 32px #0A1FAB18`
