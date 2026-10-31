# Billing

Prepaid: customers top up a CHF balance with Stripe; answers, learning and
reviews are charged from it. All code: `backend/shared/billing/services.py`
(`BillingService`), routes in `backend/services/api/app/billing/`.

## Prices (`backend/shared/ai_models.py`)

| Kind | Price |
|---|---|
| answer | tokens × `RATES["chat"]` (CHF 8 / 17.5 per 1M in/out, `CHAT_RATE_*`) |
| review | tokens × `RATES["review"]` (same defaults) |
| learning | Google's list price of the chosen model (`LEARNING_MODELS`, dated prices) × `LEARNING_PRICE_FACTOR` (5) × `USD_TO_CHF` (0.80), plus embedding tokens at `EMBEDDING_USD_PER_1M` × the same factor |

Learning models: `lite` (gemini-3.1-flash-lite) and `argon` (gemini-4-argon,
price doubles from 2026-12-01). A chatbot has a default (`tenants.learning_model`);
each run stores the one confirmed (`crawling_jobs.learning_model`).

## Charging

`BillingService.charge(user_id, amount_chf, kind, tenant_id, ref)`:
rounds to 4 decimals (0 → nothing charged), calls the SQL function
`public.charge`, which subtracts from `user_billing.balance_chf` **and** inserts
a `billing_ledger` row in one step. Never raises (a billing hiccup must not
fail an answer); returns what was charged. Helpers: `deduct_cost(user, role,
in, out, tenant)` (role → kind: chat→answer, review→review,
indexing/extraction→learning), `deduct_amount` (learning, already in CHF).

## Ledger (`billing_ledger`)

One row per top-up (`topup`, positive) and charge (`answer`, `learning`,
`review`, negative); `opening` rows from the backfill made the sum equal the
balance when the ledger started. `tenant_name` is kept when a chatbot is
deleted. The dashboard overview (`tenants/routes.get_tenant_overview`) and
`/api/billing/usage` both read spend from here, so they agree.

Check: `sum(amount_chf) per user == user_billing.balance_chf`.

## Gates

- Chat: owner balance > 0, else 402 (`chat/routes.handle_chat`).
- Reading a website: free, no gate.
- Learning: `confirm` needs balance ≥ the chosen model's estimate; each learn
  task needs balance > 0; resume after learning needs balance > 0; uploads need
  balance > 0. Scheduled re-crawls auto-confirm only below
  `RECRAWL_AUTO_CONFIRM_MAX_CHF` and when the balance covers them.

## Stripe

- Checkout: `create-checkout-session` (one-time, min CHF 5, or monthly
  subscription), `client_reference_id` = user id.
- Crediting goes only through SQL `apply_payment(source_id, user, amount)`:
  records the Stripe object in `processed_payments` and credits at most once
  (+ ledger `topup`). Sources: `checkout:<session>` for one-time payments
  (webhook `checkout.session.completed` or `verify-session` on the success
  redirect, fresh sessions only), `invoice:<id>` for subscription invoices
  (`billing_reason` starting with `subscription`).
- Portal: `POST /api/billing/portal`; invoices: `GET /api/billing/history`.
