# Burncodes AI — complete redesign brief

## 1. The ask

Redesign the **entire web app** of Burncodes AI (ai.burn.codes): every dashboard screen, the setup flows, the
login, and the chat widget that our customers put on their websites. The current interface works, but it
looks generic and machine-made: a dark navy dashboard where everything is a bordered card, emoji used as
icons, every element at the same visual weight, monospace text for things that aren't code, and no clear
hierarchy. It doesn't look like a product a Swiss municipality would trust with its residents.

We want a design that feels **calm, precise, trustworthy and quietly confident**: closer to a well-made
Swiss public-sector or banking tool than to a startup AI demo. It should be obvious at a glance what state
things are in, what something costs, and what the one next step is.

Please deliver a design system plus every screen listed in section 8, in their important states.

---

## 2. Brand assets (public URLs, fetch these)

| Asset | URL | Notes |
|---|---|---|
| Logo, gradient (SVG) | https://ai.burn.codes/logo.svg | 475 × 294, "BURN .CODES" stacked wordmark, filled with the brand gradient |
| Logo, gradient (PNG) | https://ai.burn.codes/logo.png | 760 × 470 |
| Logo, white (SVG) | https://ai.burn.codes/logo_white.svg | for dark or photo backgrounds |
| Logo, white (PNG) | https://ai.burn.codes/logo_white.png | 760 × 470 |
| App icon | https://ai.burn.codes/android-chrome-512x512.png | also 192 px, apple-touch-icon.png, favicon.ico |

**Brand gradient** (exactly as in logo.svg, diagonal from bottom-right to top-left):

| Stop | Colour | Name |
|---|---|---|
| 11 % | `#50D3FC` | cyan |
| 42 % | `#0A1FAB` | indigo |
| 87 % | `#FF2095` | magenta |

**Brand colours** in use today: indigo `#0A1FAB`, violet `#3B1FA8`, magenta `#FF2095`, cyan `#7FD8F5`
(the logo uses `#50D3FC`).

Current rules worth keeping or deliberately replacing:
- The gradient belongs to the logo. The UI itself shouldn't be drenched in it.
- Magenta marks things the AI does (learning, answering). Nothing else is magenta.
- Status colours: green = current/OK, amber = check this, red = broken.

Current typeface: **Atkinson Hyperlegible Next**, chosen for legibility. You may propose something else,
but legibility for non-technical and older users is the priority, and it must cover German and French
characters (ä ö ü é è à ç « »).

---

## 3. The product in one paragraph

Burncodes AI gives an organisation a chatbot that answers visitors' questions from the organisation's own
website and documents. The customer enters their website address; we **read** (crawl) the site for free,
then show an **estimate** of what **learning** it costs. After they confirm, an AI (Google Gemini) learns
each page: it splits pages into sections, extracts facts and dates (e.g. waste collection days), and flags
problems (expired info, contradictions). The customer styles the chat window, pastes one line of code into
their website, and a chat button appears there. Visitors (residents, customers) ask questions and get
answers with links to the source pages. Afterwards the customer sees what people asked and where the
chatbot couldn't help, and the site is re-read on a schedule so the knowledge stays current.

**Money is prepaid**: the customer tops up a balance in CHF (min. CHF 5, once or monthly). It pays for
answers (per question), learning (per page, shown before confirming) and conversation reviews (per
conversation). Nothing is ever charged without being shown first. This transparency is a core trust
feature and must be designed in, not bolted on.

---

## 4. Who uses it

**Primary: the customer's staff, non-technical.**
- Swiss municipalities (Gemeinden): administration staff, often 40–65, use Windows laptops with a
  1366–1920 px screen, Outlook, the municipality's CMS. They don't know what a "crawl" or "token" is and
  shouldn't need to. They need to feel in control and never surprised by a cost.
- Small and mid-sized organisations ("Allgemein"): course platforms, shops, schools, clubs. Slightly more
  web-savvy, still not developers.
- Often someone else (an agency or webmaster) installs the code snippet. The design must make it easy to
  hand that task off.

**Secondary: visitors using the chat widget** on the customer's website: residents asking "When is the
next paper collection?", course buyers asking "Which course suits me?". Any age, mostly on phones.

**Internal: we (Burncodes)** run the onboarding with customers, sometimes on a call or screen-share. The
guided setup (section 8.3) must work as a "play it through together" experience.

---

## 5. What's wrong today (avoid these)

- Everything is a bordered rounded card on a navy background; cards inside cards; no rhythm.
- Emoji as icons (🌐 📄 ⚡) in the setup wizard.
- Monospace font for options and labels that aren't code.
- Same weight everywhere: titles, labels and helper text barely differ; long grey helper texts under every field.
- Status is buried in text; costs appear in different formats in different places.
- Generic "AI SaaS" patterns: gradient buttons, sparkle icons, glow.
- Dark-only. Municipal staff in bright offices often find dark dashboards hard to read.

Please don't replace this with a different set of clichés: no glassmorphism, no purple-gradient hero, no
3D blobs, no oversized marketing typography inside the app, no AI sparkle overload.

---

## 6. Design principles

1. **Status first.** Every screen answers "Is it working? Is anything wrong?" before anything else.
2. **Money is always visible and never a surprise.** Costs before actions, in CHF, with the balance
   nearby. Use one consistent money format: `CHF 12.40`.
3. **One primary action per screen.** Secondary actions are clearly secondary.
4. **Plain language, no jargon.** "Read your website", not "crawl". "Learn", not "index". "Pages", not
   "sources/chunks" (advanced details can exist behind a disclosure).
5. **Progressive disclosure.** Recommended defaults visible; advanced settings folded away.
6. **Show the real thing.** The chat preview is the real widget; the estimate lists real pages.
7. **Calm motion.** Progress is shown honestly (counts, not fake spinners); respect reduced motion.
8. **Accessible.** WCAG 2.2 AA contrast, visible focus, keyboard reachable, 16 px minimum body text,
   44 px touch targets in the widget.

---

## 7. Constraints

- **Stack:** Vue 3, Tailwind CSS 3, some DaisyUI classes, CSS custom properties as design tokens
  (`--surface-*`, `--interactive`, `--status-*`, `--radius-*`, `--text-*`). Please deliver tokens we can
  drop into CSS variables: colour roles, type scale, spacing scale, radii, shadows, motion.
- **Themes:** deliver **light as the default** and a **dark** variant from the same tokens.
- **Languages:** German (primary, Swiss spelling: "ss" instead of "ß", «guillemets»), English, French.
  German strings run ~30 % longer than English. Design with the German copy given below.
- **Widths:** dashboard at 1280–1920 px wide, still usable at 1024 px and on a tablet. The chat widget and
  the public chat page must be excellent on phones (360 px).
- **Icons:** we use Font Awesome 6 (solid). Propose a consistent set, or another single library.
- **Customer theming:** the chat widget is styled by each customer with their own brand colours (any
  colours, any logo). Our app chrome must never clash with it, and the widget must stay readable with any
  palette (we check text contrast automatically, see 8.6).

---

## 8. Every screen

Copy shown is the current German (EN in brackets where helpful). Feel free to improve wording, but keep
the meaning. Numbers in examples are illustrative.

### 8.1 Global shell

- **Sidebar** (per chatbot): logo; chatbot switcher (current chatbot name with a green/grey dot for
  on/off); section "Arbeitsbereich" with **Übersicht** (Overview), **Wissen** (Knowledge), **Anpassen**
  (Configure), **Auswertung** (Insights), **Einbinden** (Install), **Öffentliche Testseite** (Public test
  page, with a copy-link action); section "Konto" with **Meine Chatbots**; bottom: user name + email,
  **Einstellungen** (Settings), **Abmelden** (Log out).
- Mobile/tablet: top bar with menu button and logo.
- **Toasts** for confirmations and errors; **confirmation dialog** for destructive actions (delete crawl,
  switch chatbot off, delete account).
- **Session expired** dialog.
- Empty, loading (skeleton) and error states for every page.

### 8.2 Login and sign-up

- **Login:** email, password, "Anmelden"; link to sign-up. Left half: brand panel with the tagline
  "Der Chatbot, der Ihre Website und Ihre Dokumente kennt." and "Powered by Burncodes AI".
- **Sign-up:** first name, last name, email, password, dashboard language (DE/EN/FR). Then an email
  confirmation notice.

### 8.3 Guided setup (onboarding) — new, highest priority

Full-screen, no sidebar. Started by a link with `?onboarding` (we send it to new customers, or click
through it with them on a call). Progress survives reloads; "Später fortsetzen" (Continue later) leaves
without losing anything. Each step has a short title, one sentence of explanation, the inputs, and a
small "Gut zu wissen" (Good to know) box with 1–2 reassuring facts. Steps:

1. **Willkommen** (Welcome): "Willkommen! Richten wir Ihren Chatbot ein." Five steps previewed: create
   the chatbot · read the website (free) · choose the look (taken from your website) · let it learn (you
   see the cost first) · install (or email it to your webmaster). Button "Los geht's".
2. **Grundlagen** (Basics): chatbot name; website address; **"Wen er berät"** (Who it answers): two
   choices, **Gemeinde** (residents asking about services, fees, collection dates, opening hours) or
   **Allgemein** (visitors of a company, shop, school or club asking about offers, prices, dates).
3. **Website lesen** (Read the website): whole website vs. this page only; three recommended options, on
   by default: **Seiten aus der Sitemap** (also read pages the site lists in its sitemap, e.g. landing
   pages no menu links to) · **Nur eine Sprache** (skip other language versions like /en/, /fr/; the bot
   answers in every language anyway) · **Danke- und Werbeseiten überspringen** (skip thank-you,
   confirmation, error, ad-copy, cart and login pages). Folded away: "Bereiche auslassen" (paths or
   subdomains to skip) and "Gründlich" read mode. Button "Einlesen starten".
4. **Aussehen** (Look): we automatically take brand colour, logo and site name from their website and say
   so ("Farben und Logo Ihrer Website sind übernommen."). Tone: **Höflich und formell** / **Freundlich** /
   **Kurz und sachlich**. Greeting text. Next to it, the live, clickable chat preview (8.6). Reading
   continues in the background; show that quietly.
5. **Lernen** (Learn): states in order:
   - Reading: progress "1'125 von 1'375 Seiten gelesen".
   - Calculating: "Wir berechnen, was das Lernen kostet …"
   - Estimate: "1'250 Seiten und Dokumente lernen · ca. CHF 18.40", balance "Ihr Guthaben: CHF 25.00",
     primary "Lernen starten (CHF 18.40)", secondary "Auswahl anpassen".
   - Balance too low: warning plus "Guthaben aufladen" (opens billing) and "Guthaben neu prüfen".
   - Learning: progress "640 von 1'250 gelernt".
   - Done: "Fertig gelernt! Ihr Chatbot kennt jetzt Ihre Website."
   - Stopped: link to details.
   The user can continue to the next steps while it learns ("Weiter, während er lernt").
6. **Ausprobieren** (Try it): the real chat; note if it's still learning.
7. **Einbauen** (Install): code snippet with copy button; how-to per website builder; "send to your
   webmaster" email button (see 8.9).
8. **Fertig** (Done): where to find Wissen, Anpassen, Auswertung; "Zum Dashboard".

### 8.4 Meine Chatbots (chatbot list)

List of the account's chatbots: name, on/off state, number of sources ("506 Quellen"), short public link.
Actions per row: open, configure, delete. Primary: "Neuer Chatbot" opens a dialog with name and "Wen er
berät" (Gemeinde/Allgemein). Empty state for new accounts should point to the guided setup.

### 8.5 Übersicht (Overview, per chatbot)

- **Status:** "Ihr Chatbot ist eingeschaltet" with on/off switch (switching off asks for confirmation;
  explain the chatbot disappears everywhere at once). Variants: on, on but button hidden on the website,
  off.
- **Usage for a period** (7/30/90 days): conversations, questions answered, spent (split answers vs.
  learning), balance with "Aufladen", a small daily chart, comparison with the previous period.
- **Knowledge at a glance:** pages, files, last read, warnings to look at.
- **Runs automatically:** "Websites auf Änderungen prüfen" (off / weekly / every 2 weeks / monthly; only
  changed pages cost anything) and "Gespräche auswerten" (off / nightly / weekly, a few centimes per conversation),
  each with last and next run.

### 8.6 Anpassen (Configure)

Two columns: settings left, live preview right (sticky).
- **Grundlagen:** name (only shown in the dashboard); "Wen er berät" (Gemeinde/Allgemein).
- **Tonalität:** three tone presets as starting points, then a free text "Persönlichkeit und Anweisungen"
  (e.g. "Verweise bei Baugesuchen an die Bauverwaltung."), "Wartetexte" (one per line, shown while it
  thinks).
- **Erweitert** (folded): the full instruction template for experts.
- Button **"Aussehen meiner Website übernehmen"**: takes colour, logo and name from their website.
- **Preview** with three views: **Start** (greeting + suggested questions), **Gespräch** (sample
  conversation), **Chat-Knopf** (the launcher button on a mock website). In "Aussehen bearbeiten" mode
  every part is clickable and opens a small popover: chat background, header (logo, title), bot messages
  (greeting text + colours), visitor messages, input field, send button, restart button, close button,
  suggested questions (text, add/remove, colours), launcher (colour, custom icon, show on website on/off).
  "Ausprobieren" mode = the real chat.
- Colour picking: a small palette (Primary, Secondary, Black, White + custom colours added to it) with
  swatches; custom colour picker.
- **Readability warning** when a text/background pair falls under 4.5:1 contrast, naming the parts
  ("Schwer lesbar: Besucher-Nachrichten, Senden-Knopf").
- **Unsaved changes bar** (sticky): "Sie haben ungespeicherte Änderungen" · Verwerfen · Änderungen speichern.

**The chat widget itself** (designed by us, coloured by the customer): header with logo + title + restart
and close; messages with Markdown (bold, lists, links); **source chips** under answers linking to the
pages used; a "subscribe to these dates in your calendar" button when dates are given; optional share
button; input with placeholder "Stell mir eine Frage…"; thinking state with rotating texts; launcher
button (round, customer colour or custom icon). Special states: switched off ("Dieser Chatbot ist
ausgeschaltet"), password-protected (password entry before chatting), shared conversation (read-only),
error/retry. Please design our default widget theme and show it with two very different customer palettes
(e.g. magenta `#E6007E` on white for a course platform; dark red `#E3302C` for a municipality).

### 8.7 Wissen (Knowledge)

The busiest area. Sections:
- **Summary:** "1'373 Quellen, 4'912 Abschnitte. Zuletzt gelesen am 29. Oktober."
- **Termine, die Ihr Chatbot kennt:** verified dates for the next 14 days (series name, zone, date,
  "verschoben" marker), or a notice that published calendars have ended ("Ihr Chatbot kann nicht sagen,
  wann die nächste ist. Veröffentlichen Sie den neuen Kalender.").
- **Kalender abonnieren:** residents can subscribe to date series in their calendar app; on/off, list of
  calendars with copy-link.
- **Kontakt und Öffnungszeiten:** address, phone, email, opening hours read from the website footer.
- **Durchläufe** (Crawls): list of reading runs: website, date, status badge (**Scannt** / **Wird
  vorbereitet** / **Bereit zum Lernen** / **Lernt** / **Abgeschlossen** / **Angehalten**), one-line summary
  ("1'250 zu lernen · ca. CHF 18.40" or "62 gelernt, 1'300 unverändert · CHF 0.85"), current activity while
  running ("Wird gelesen: Mentoren"). "Prüft alle 7 Tage auf Änderungen · Ändern". Primary: **"Wissen
  hinzufügen"**.
- **Hochgeladene Dateien:** PDF/TXT/CSV uploads.
- **Eigene Antworten:** fixed answers for specific questions ("wer für Baugesuche zuständig ist").
- **Ausgelassen:** folders/pages the customer excluded, which stay excluded in every future read, with
  "Wieder lernen".

**Add knowledge wizard** (side panel, 4 steps): type (website / document) → address + whole site or single
page → options (the same three switches as onboarding, left-out paths as chips, read mode Schnell/Gründlich)
→ confirm summary → "Einlesen starten". Document path: type → file drop zone → confirm.

### 8.8 Crawl detail (one reading run)

Header: website, date, status, actions (stop, continue a stopped run, delete with confirmation).
By status:
- **Scanning:** live activity log ("Scanne Mentoren", "Sitemap gelesen: 1'343 weitere Seiten", "{Seite} —
  neu"), page counts. Many pages share the same title on some sites, so log rows need the path visible.
- **Ready to learn (estimate):** "Scan abgeschlossen", what will happen ("Gemini liest 1'250 neue oder
  geänderte Quellen …"), new/changed/unchanged counts, cost and balance, primary "Jetzt lernen · ca. CHF
  18.40". **Set aside automatically** before learning, with reasons (old budgets and accounts, old minutes,
  outdated, older version, thin pages, internal, other), each list expandable with "Wieder aufnehmen".
  **"Sparmöglichkeiten"**: AI-suggested folders to leave out ("Archiv · 214 Quellen, spart CHF 3.10",
  "Auslassen"/"Rückgängig"). **"Auswählen, was gelernt wird"**: a searchable tree of folders, pages and the
  files linked from them, with checkboxes, cost per item, "nur durchsuchbar" badge for very long documents.
- **Learning:** progress, per-page log ("Mentoren gelernt: 6 Abschnitte · 4 Fakten · 0 Termine").
- **Completed report:** learned / unchanged / removed / errors / cost; dates found (series, zone);
  "Zu prüfen" issues per page (contradiction, expired, dates rejected, not readable) with a hint; most
  important content (very important / important).
- **Website content:** every page and file of the run with what became of it, filterable.

### 8.9 Einbinden (Install)

Three numbered steps: 1. copy the one-line snippet (code block + copy button); 2. add it to your website,
with expandable how-tos for WordPress, Wix, Squarespace, Webflow, other, plus "Lassen Sie es jemanden
erledigen?" with a ready-made email to the webmaster; 3. check it appears (cache, cookie-consent notes).
Notices if the chatbot is off, the button is hidden, or a password is set. Link to an example page.

### 8.10 Öffentliche Testseite (Public test page)

The public link anyone can use to try the chatbot (copy, open). Optional password while in development
(set/change/remove, show/hide), with notes: send link and password separately; the website button asks for
it too, so turn it off when going live.

### 8.11 Auswertung (Insights)

- **"Zum Anschauen"** (To look at): questions the chatbot couldn't answer well, found by an AI review of
  finished conversations. Kinds: Nicht beantwortet, Möglicherweise falsch, Widerspruch des Nutzers,
  Missverstanden. Filter open / resolved / dismissed. Actions: view conversation, add an answer
  ("Antwort hinzufügen", saved as a fixed answer), add knowledge, done, dismiss, reopen.
- **Review settings:** on/off, nightly/weekly, cost per conversation, "Jetzt auswerten", last-30-days stats.
- **Gespräche:** everything people asked, newest first; conversation viewer (side panel) with flagged
  questions highlighted.

### 8.12 Account settings

Sections: **Profil** (name, email read-only, dashboard language) · **Sicherheit** (password, "Überall
abmelden") · **Abrechnung** (balance; spent split into answers / learning / reviews; top up once or monthly
with preset amounts + custom, min. CHF 5; Stripe portal for payment methods and invoices; payment history
with invoices) · **Zeitpläne** (automatic re-reading and reviews across all chatbots) · **Konto löschen**
(type your email to confirm; lists what gets deleted).

### 8.13 Public pages

- **Public chat page** `/chat/<id>`: the chat full-screen with the customer's branding.
- **Shared conversation** `/share/<id>`: read-only conversation snapshot, expired/not-found states.
- **Example page** showing the launcher on a dummy website.

---

## 9. Component inventory

App shell and sidebar · chatbot switcher · page header (title, one-line lede, actions) · section/panel ·
key figure (big number + label + delta) · small bar chart · status badge (the six crawl states + on/off) ·
progress bar with honest counts · activity log row (running/done/failed) · money display (CHF, estimate
vs. actual) · balance chip · primary/secondary/quiet/destructive buttons · icon button · text input,
textarea, select, URL input with validation · radio cards (choice with title + one-line description) ·
checkbox row with title + description · switch · segmented control · path chips with remove · searchable
tree with checkboxes and per-row cost · disclosure ("Weitere Einstellungen") · tabs · side panel/wizard
with step indicator · modal/confirmation dialog · toast · inline notice (info/success/warning/error) ·
empty state · skeleton · code block with copy · colour swatch picker + popover editor · contrast warning ·
date list (series/zone/date) · conversation viewer · the chat widget and its parts · stepper for the guided
setup.

---

## 10. Realistic content for mock-ups

- Chatbots: **Gemeinde Brittnau** (506 sources, municipality, red `#E3302C`), **Zofingen.ch**,
  **reichenbach.ch** (red `#FF0000`), **Younity** (course platform for spiritual mentors, magenta
  `#E6007E`, informal "du").
- Younity crawl: sitemap listed 2'150 pages; after one-language and funnel filters, 1'375 to read. For the
  estimate, use illustrative figures such as 1'250 to learn, ca. CHF 18.40, balance CHF 25.00.
- Dates: "Papiersammlung · Zone Nord · Di, 3. November"; "Grüngut · alle Zonen · Fr, 6. November".
- Questions: "Wann ist die nächste Papiersammlung?", "Was kostet eine Hundemarke?", "Welcher Kurs passt zu
  mir?", "Welche Events stehen bald an?".
- Numbers: Swiss formatting, apostrophe thousands separator (1'375), CHF with two decimals, dates
  "29. Oktober 2026", times "01:41".

---

## 11. Deliverables

1. **Design system:** colour roles (light + dark), brand use rules, type scale, spacing, radii, elevation,
   motion, iconography, and all components from section 9 with states (default, hover, focus, disabled,
   loading, error).
2. **Screens** for everything in section 8, at 1440 px wide, in light theme, German copy, including:
   empty/first-use, normal, loading, error, and the crawl states (scanning, estimate, low balance,
   learning, completed with issues, stopped).
3. **Guided setup** (8.3), all 8 steps, desktop and phone width.
4. **Chat widget** in our default theme plus two customer palettes, on phone and desktop, including the
   launcher, sources, calendar button, thinking, switched-off and password states.
5. A few **dark-theme** versions of key screens (Overview, Knowledge, Configure) to prove the tokens.
6. Short notes on any copy or structure you changed and why.
