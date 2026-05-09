# Screen: Billing & Subscription

## What's Wrong Now
- Credit-card icon + heading pattern is generic
- Balance shown in huge primary-color text — feels alarming rather than informative
- "Manage Billing" button is a ghost button that's easy to miss
- Pricing plans rendered as cards but with mismatched padding and unclear hierarchy
- No visual distinction between current plan and alternatives

## New Design

### Layout
Two sections, single column, max-width 640px:
1. Balance card
2. Plan & pricing

### Balance Card

```
┌─────────────────────────────────────────────────────────┐
│  CURRENT BALANCE                                        │
│                                                         │
│  CHF 12.40                      [Top Up →]             │
│                                                         │
│  ████████████████████░░░░  Used CHF 7.60 this month    │
│                                                         │
│  Pay-as-you-go · No subscription required              │
└─────────────────────────────────────────────────────────┘
```

- Card bg: `--surface-1`, border `--surface-3`
- Balance: 36px, 700 weight, `--surface-heading` — NOT primary color
- `[Top Up →]` button: gradient fill, right side of card
- Usage bar: `--brand-indigo` fill on `--surface-2` track
- Sub-caption: 12px `--surface-muted`

### Top Up Flow
Clicking "Top Up" expands an inline section below the card (no modal):

```
Amount:  [CHF 10]  [CHF 25]  [CHF 50]  [Other: ___]

[Pay with Stripe →]
```
- Amount pills: `--surface-2` bg, indigo border when selected
- "Other" shows number input
- Stripe redirect button: gradient, full-width

### Plan Section

```
YOUR PLAN
──────────────────────────────────────────────
● Pay-as-you-go (Current)

  CHF per 1M input tokens   → CHF 0.XX
  CHF per 1M output tokens  → CHF 0.XX
  No monthly fee

──────────────────────────────────────────────
[Manage Stripe Billing ↗]   (subtle link, not button)
```

- Current plan: indigo dot indicator, no box — just clean text
- Pricing table: two rows, grid-aligned
- "Manage Stripe Billing" is a text link with external icon, not a ghost button

### Usage History (future)
- Placeholder section at bottom: "Transaction history coming soon"
- Greyed out, not missing entirely
