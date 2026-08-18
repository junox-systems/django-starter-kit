# Allauth Pages Inside the Dashboard Shell — Design

Date: 2026-08-18
Status: Approved by user (design sections confirmed)

## Goal

Render allauth account-management pages inside the authenticated app shell
(`base_app.html`), so the sidebar's existing "Account" links (Email, Password,
Connections) no longer eject the user into the public marketing layout.

## Decision

**Option A: layout-only.** Keep the `/accounts/*` URL prefix untouched; change
only the template chrome. Re-mounting allauth under `/dashboard/account/` was
rejected: it would drag pre-auth pages (login, signup, password reset) under an
app-gated path, and break existing links without redirects for no UI gain.

The shell is Django templates (`base_app.html`) with a Svelte sidebar island;
this is purely a template-inheritance change, no Svelte work.

## Two page families

| Family | Pages | Layout |
|---|---|---|
| Account management (needs a user) | `email`, `password_change`, `password_set`, `reauthenticate`, `socialaccount/connections` | `base_app.html` (in shell) |
| Pre-auth funnel | `login`, `signup`, `logout`, `password_reset`, `password_reset_done`, `password_reset_from_key`, `password_reset_from_key_done`, `email_confirm`, `verification_sent`, `verified_email_required`, `account_inactive`, social login/cancel/error | `base.html` (unchanged) |

`email_confirm` stays public: it is opened from an email link, often while
signed out. `app_nav` already returns `{}` for anonymous users, so the shell
must never be reached pre-auth; allauth's own login redirects cover that.

## Changes

1. **`templates/account/email.html`, `password_change.html`, `password_set.html`,
   `reauthenticate.html`**: swap `{% extends "base.html" %}` →
   `{% extends "base_app.html" %}` and replace the full-screen wrapper
   (`min-h-dvh flex items-center justify-center`) with a plain constrained
   container (`mx-auto w-full max-w-2xl`), matching `templates/users/profile.html`.
   Forms and cards otherwise untouched.
2. **`templates/socialaccount/base_manage.html`** (new): extends
   `base_app.html`, keeps the stock manage-chain intact for future pages.
3. **`templates/socialaccount/connections.html`** (new): extends
   `base_manage.html`, stock content restyled to the card pattern. Currently
   this page renders unaudited allauth markup.
4. **Tests** (`apps/users/tests/test_views.py`): extend
   `test_authenticated_management_pages_render` to assert shell chrome
   (`data-turbo="true"`, sidebar mount, `app-nav-data` payload); extend
   `test_public_account_pages_render` to assert no shell chrome.

## Behavior notes

- Forms stay browser-native (`Turbo.config.forms.mode = "off"`); an invalid
  form re-renders as HTTP 200 on a full load inside the shell, which is fine.
- Sidebar needs no changes: it already links `account_email`,
  `account_change_password`, `socialaccount_connections`, and active-state is
  derived from `location.pathname` on `turbo:load`, so `/accounts/email`
  highlights correctly.
- No new dependencies, no URL changes, no settings changes.

## Verification

- `make test` (pytest, `DJANGO_SETTINGS_MODULE=config.settings.test`)
- `cd frontend && pnpm run build`

## Out of scope

- URL restructuring (`/dashboard/account/...`)
- A dedicated settings hub page — the sidebar already surfaces these pages
- 2FA/passkey templates until they are enabled