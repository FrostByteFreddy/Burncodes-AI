# Industry profiles

Status: decided, not built yet (2026-10-25)

## Decision

Every chatbot has an **industry**, chosen once with a single select box in the
onboarding. The industry tailors what the chatbot learns, how it answers and
which parts of the dashboard it shows.

- We ship **one industry for now: "Municipality / public administration"**.
  All existing chatbots get it.
- Internally an industry is a **bundle of modules** plus wording. A new
  industry is mostly a new combination of existing modules and new texts;
  code is only needed for a module that doesn't exist yet.
- **Modules are not a customer-facing concept.** Customers pick an industry;
  we market outcomes ("collection dates in residents' calendars", "answers
  with the official document linked"), never "modules".

## Why

Today the municipal logic is spread across prompts, date validation, the
chat, calendars and the UI ("residents", waste calendars, old budgets in the
sorting step). An IT agency or a shop has no collection calendar but has
other structured data (services, references, products). Without a clear
boundary, every new kind of customer would mean `if municipality` branches
everywhere.

## Modules

| Module | What it covers | Municipality | Later, e.g. agency |
|---|---|---|---|
| `dates` | schedules and events extracted from documents, PDF cross-check, calendar feeds, date strip, "published calendar has ended" warning | on | off |
| `contacts` | departments, people, phone, email | on | on |
| `opening_hours` | structured hours (enables "open now?") | on | optional |
| `fees` | amounts with validity | on | off |
| `services` | name, description, audience, price model, link | later | on |
| `references` | projects / case studies, technologies | off | on |

## What a profile defines

One file per industry in `backend/shared/profiles/` (e.g. `municipality.py`).
Profiles live in code, not in the database: they change together with prompts
and extraction logic and belong under the same tests.

1. **Modules** that are on.
2. **Learning prompt:** who the users are ("residents" vs "customers"), what
   counts as important, which structured data to extract. The extraction
   schema is assembled from the active modules.
3. **Sorting step** (`knowledge/triage.py`): what's typically not worth
   learning. Municipality: old budgets and accounts, old minutes. Agency:
   old blog posts, closed job ads, legal pages.
4. **Chat context:** what is added to the instructions besides document
   search. Municipality: verified dates. Agency: the list of services.
5. **Conversation review:** who the users are, what counts as unanswered.
6. **Defaults for new chatbots:** tone presets, welcome text, suggested
   questions, sample conversation in the Configure preview.
7. **Wording in the dashboard:** e.g. "Einwohnerinnen und Einwohner" vs
   "Kundinnen und Kunden" — locale keys with a per-profile variant that falls
   back to neutral wording.

## Data model

- `tenants.industry TEXT NOT NULL DEFAULT 'municipality'`.
- `tenants.modules TEXT[]` — the active modules, initialised from the
  industry's defaults (allows switching one off without changing industry).
- `tenant_sources.learned_modules TEXT[]` — the modules a source was learned
  with, so it's known exactly what's missing after a module is switched on.
- `tenant_events` stays as it is (module `dates`).
- New, generic `tenant_entities` (`kind`, `name`, `data JSONB`, `valid_from`,
  `valid_to`, `source_id`) for services, references, opening hours and the
  like — no new table per industry. Only built when the second module that
  needs it is built.

## Switching modules after the start

Learning extracts the structured data, so modules are effectively fixed once
knowledge exists. Changing them is asymmetric:

- **Switching a module off** is instant and free. Its data is kept but no
  longer used (chat, calendars, dashboard). Switching it back on before
  anything was re-learned costs nothing.
- **Switching a module on** needs a **module pass**, not a full rescan: a
  small extraction for just that module over existing sources. Page text is
  already stored; only PDFs are downloaded again. The sorting step picks the
  sources worth it. It runs through the usual flow — estimate → confirm →
  report — so the cost is shown before anything is billed.
- New and changed sources are always learned with all modules active at that
  moment; re-crawls fill in sources that miss a newly activated module.

## Frontend

The UI switches on **modules, never on the industry**:
`GET /tenants/<id>` returns `profile: { industry, modules }`.

- Date strip, calendar section and "calendar has ended" warnings: only with
  `dates`.
- A "Services" list on the Knowledge page: only with `services`.

A new industry then doesn't touch any page.

**Onboarding:** one select box "Industry" next to the name when creating a
chatbot. Today it offers only "Municipality / public administration". The
recommended modules come from the industry; there's no module picker in the
onboarding. Under "Anpassen" the industry is visible; changing it explains
that structured data needs a module pass and offers to start it.

## Plan

1. **Wiring, no visible change:** `tenants.industry`, `tenants.modules`,
   `tenant_sources.learned_modules`, the profile registry and
   `profiles/municipality.py` holding today's behaviour. Tests show that
   learning, sorting, chat and review produce the same instructions as before.
2. **Modularise:** dates, calendars, PDF cross-check, date strip and the
   "calendar has ended" warning become module `dates`; the frontend reads
   `profile.modules`; remaining municipal wording becomes per-profile texts;
   the industry select box goes into the create-chatbot dialog.
3. **`tenant_entities` and the module pass** — only once a second module
   needs them.
4. **A second industry** (e.g. "Service provider / agency" with `services`,
   `references`, `contacts`) — only when the municipal product has paying
   customers or a concrete customer from another industry asks for it.

Steps 1 and 2 are worth doing now: they're cheap and keep the code clean.
Steps 3 and 4 wait for demand.

## Open questions

- **Default industry for sign-ups** once there are several: "Municipality" or
  a neutral "General" profile (contacts, opening hours, services, no dates)?
  Leaning towards adding "General" together with step 4.
- **Prices per industry?** Possible — rates are per billing role
  (`shared/ai_models.py`) and could become per profile.
- **Expert mode** that lets customers combine modules freely: not planned;
  revisit if customers ask.
