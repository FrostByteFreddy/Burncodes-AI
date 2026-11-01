# Frontend (`frontend/src/`)

Vue 3.5 (`<script setup>`), Vue Router, Pinia, vue-i18n 9, Tailwind 3 (no
component plugin), Font Awesome 6 solid, axios. Built by Vite; production is a
static bundle behind nginx.

## Addresses

The app is built with `base: '/dashboard/'` and served there. `/chat/:id` and
`/share/:id` keep their root addresses because they are embedded on customer
sites and shared as links: the same `index.html` answers them, and
`router/index.js` picks the router base from the current path. `/` is the
separate landing page (`landing/`, plain HTML without a build step, its own
container, indexed by search engines). The routing is in `nginx/nginx.conf`,
which also redirects the dashboard's old addresses (`/login`, `/tenant/…`) and
`/?onboarding` to `/dashboard/…`. Everything but `/` is `noindex`. Files from
`public/` are under `/dashboard/`: use `import.meta.env.BASE_URL` in dynamic
links. Locally: `:5173/dashboard/`, landing on `:8080` (`landing` service).

## Two looks

- **Login / signup / onboarding**: brand gradient (`components/AuthLayout.vue`,
  `views/Onboarding.vue`; the gradient reaches the left edge, content stays
  centred like the dashboard).
- **Dashboard**: sidebar + content, centred with a max width
  (`App.vue` `.bc-shell`), never pinned to the left on wide screens.
- The chat widget (`components/chat/ChatWidget.vue`, `BaseChat.vue`) keeps its
  own older look on purpose.

## Design system

| File | Role |
|---|---|
| `assets/tokens.css` | colour, type, spacing tokens; light by default, dark via `data-theme` |
| `assets/bc.css` | `bc-*` component classes |
| `assets/design-tokens.css` | aliases for older variable names |
| `assets/legacy.css` | bridge so screens not yet redesigned still fit |
| `components/ui/Bc*.vue` | 33 components (BcButton, BcDialog, BcField, BcPanel, BcTabs, BcStatusBadge, BcMoney, …), exported from `components/ui/index.js` |
| `docs/design/redesign-brief.md` | the brief the design system was made from |

Use Bc components and tokens for new UI. `BcDialog` with `loading` can't be
dismissed while working; `ConfirmationModal` wraps it for "are you sure".

## Routes (`router/index.js`)

| Path | Component |
|---|---|
| `/login`, `/signup` | `views/Login.vue`, `Signup.vue` |
| `/onboarding` | `views/Onboarding.vue`. `?onboarding` on any address marks it pending; it opens after login (`utils/onboarding.js`) |
| `/manage-tenants` | `views/ManageTenants.vue` (all chatbots) |
| `/tenant/:id/overview` | `views/Overview.vue` |
| `/tenant/:id/sources` | `components/tenant/Sources.vue` (knowledge, runs, wizard) |
| `/tenant/:id/sources/crawls/:jobId` | `components/tenant/CrawlDetail.vue` (estimate, model choice, selection, log, report) |
| `/tenant/:id/configure` | `components/tenant/Settings.vue` ("Anpassen": persona, appearance, branding from the website) |
| `/tenant/:id/insights` | `views/Insights.vue` |
| `/tenant/:id/install` | `views/Install.vue` (widget snippet) |
| `/tenant/:id/test-page` | `views/TestPage.vue` (public link, password) |
| `/tenant/:id/settings` | `views/TenantSettings.vue` ("Erweitert": schedule, learning model, exclusion rules, audience) |
| `/settings/:section` | `views/AccountSettings.vue` (profile, security, billing, danger); `/profile`, `/subscription` redirect here |
| `/chat/:tenantId` | `views/Chat.vue` (full page; `?widget` inside the iframe) |
| `/share/:shareId` | `views/ShareView.vue` |

The guard restores the session, sends logged-out users to `/login` and handles
`?onboarding`.

## State and helpers

| File | Does |
|---|---|
| `stores/auth.js` | Supabase session, user, logout, session-expired modal |
| `stores/tenants.js` | chatbots, current chatbot; `wantedId` guards against a slower load overwriting the one in the address |
| `stores/billing.js` | balance, usage |
| `utils/api.js` | axios with the Supabase token; on 401 refreshes once, then logs out |
| `supabase.js` | client (anon key) for auth and Realtime |
| `composables/useCrawl.js` | confirm (with model), stop, resume, remove (repeats while the API answers 202) |
| `composables/useLearningModels.js` | model choices and prices for an estimate |
| `composables/useToast.js` | toasts |
| `utils/format.js` | Swiss numbers and CHF (`1'234.50`), dates |
| `utils/widgetConfig.js` | widget defaults, from tenant, apply branding |
| `utils/chatbotDefaults.js` | audiences, sample conversation per audience |
| `utils/chatProcessor.js` | renders answers (marked + DOMPurify) |

Realtime: `Sources.vue` and `CrawlDetail.vue` subscribe to `crawling_jobs` and
`crawl_job_log` changes (see `database.md` for why only those tables).

## i18n

`locales/de.json` (main), `en.json`, `fr.json`; every key in all three.
German is Swiss: "ss" not "ß", «» quotes, informal where the product speaks to
end users. Write for non-technical customers (municipal staff): no developer
terms in the UI. Check after changes: every `t('…')` key exists in all locales,
and `npx vite build` passes.
