# Screen: Knowledge (Sources)

## What's Kept
- The "Add Knowledge" slide-in sidebar wizard — this stays as-is
- The source type icons and status chips

## What's Wrong Now
- Heading + sub-heading pattern is generic
- Source list rows are flat with no visual hierarchy
- Status pills are too small and hard to read
- No at-a-glance summary of indexing health
- Chunk count and cost are buried / not shown

## New Design

### Top Bar (replaces page heading)
A slim stats bar below the sidebar active label:

```
3 sources   ·   142 chunks   ·   CHF 0.04 spent    [+ Add Knowledge]
```
- Stats in `--surface-muted`, values in `--surface-text` medium weight
- `+ Add Knowledge` button: gradient pill, right-aligned, opens existing wizard sidebar

### Knowledge List

Each source is a row card:

```
┌───────────────────────────────────────────────────────────────────┐
│  [🌐]  https://docs.example.com          ● COMPLETED   48 chunks  │
│        Last indexed: 2h ago · Cost CHF 0.01             [···]     │
└───────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────┐
│  [📄]  product-manual.pdf               ◌ PROCESSING             │
│        Uploading...                     ████████░░  [···]        │
└───────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────┐
│  [🌐]  https://broken-page.com          ✕ ERROR  404             │
│        Failed to fetch                             [Retry] [···] │
└───────────────────────────────────────────────────────────────────┘
```

- Row bg: `--surface-1`, border `--surface-3` 1px, 10px radius
- Icon: 36px square, `--surface-2` bg, source-type icon in brand-cyan
- Status chip: pill, 22px height
  - COMPLETED: `--status-success` tinted bg, green text
  - PROCESSING: `--status-warning` tinted bg, amber text + spinner
  - ERROR: `--status-error` tinted bg, red text
  - QUEUED: `--surface-2` bg, muted text
- Chunk count: right-aligned badge, `--surface-2` bg
- Three-dot menu: Re-index, Delete
- Retry button: only shows on ERROR status
- Progress bar replaces chunk count while PROCESSING

### Crawling Job Progress
- Keep the existing `CrawlingJobProgress` component
- Restyle: use `--surface-2` card, indigo progress bar, no box shadows

### Empty State
```
No knowledge sources yet.
Add URLs, PDFs, or files to start building your chatbot's knowledge base.

[+ Add Knowledge]
```

### Sorting / Filtering (future)
- Filter pills at top: All · URLs · Files — placeholder for now (grayed out, tooltip "Coming soon")
