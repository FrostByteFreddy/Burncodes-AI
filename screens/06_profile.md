# Screen: Profile & Security

## What's Wrong Now
- Pill tabs at top of page (Profile / Security) — redundant navigation layer
- Icon + giant heading is noisy
- Form fields look generic with heavy icon prefix on every input
- Password section is a separate visual context but feels tacked on

## New Design

### Layout
Single vertical form, no tabs. Profile info and security live on the same scrollable page, separated by a thin section divider. Max-width 560px.

```
ACCOUNT DETAILS
─────────────────────────────
[First name]  [Last name]

[Email — disabled, read-only chip style]

[Phone number — optional]

[Language — select]

[Save Changes]


─────────────────────────────
CHANGE PASSWORD
─────────────────────────────
[Current password]
[New password]
[Confirm password]

[Update Password]


─────────────────────────────
DANGER ZONE
─────────────────────────────
[Delete account — outlined red button]
```

### Field Styling
- No icon prefix on every field — clean inputs only
- Label: 12px, uppercase, tracking-wide, `--surface-muted`
- Input: `--surface-2` bg, `--surface-3` border, 10px radius, `--surface-text` text
- Focus: `--brand-indigo` 2px ring, no border color change
- Disabled email field: distinct `--surface-0` bg + lock icon on the right only

### Section Headers
- 11px / uppercase / letter-spacing-wide / `--surface-muted`
- Followed by a 1px `--surface-3` divider line
- NOT a big H2

### Avatar Area
At top of page — circular avatar (48px), shows user initials with brand gradient bg.
"Change photo" link beneath (future — greyed out with tooltip for now).

### Save Button UX
- Per-section save buttons (not one global save)
- Disabled when no changes made in that section
- Inline loading spinner replaces button text while saving
- On success: `✓ Saved` text for 2 seconds, then reverts

### Danger Zone
- Collapsible by default (click to expand)
- "Delete account" button is outlined red, NOT filled — requires a secondary confirmation modal
