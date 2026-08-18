# Allauth Pages Inside the Dashboard Shell — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render allauth account-management pages inside the authenticated app shell so the sidebar's Account links stop ejecting users into the public layout.

**Architecture:** Purely a Django template-inheritance change. Four existing `templates/account/*.html` pages swap their `{% extends "base.html" %}` for `{% extends "base_app.html" %}` and lose their full-screen centering wrapper. Two new `templates/socialaccount/` overrides (base_manage + connections) bring the sidebar's Connections link into the shell. No URL, settings, JS, or Svelte changes.

**Tech Stack:** Django 5.2 templates, django-allauth, pytest, Tailwind/Basecoat classes (`.card`, `.badge`, `.btn`), Turbo Drive (already scoped to the shell).

## Global Constraints

- **URLs unchanged:** allauth stays mounted at `/accounts/` (`config/urls.py:27`).
- `{% extends %}` must be the file's first tag (AGENTS hard rule 2).
- `{# #}` comments are single-line only; use `{% comment %}` for multi-line (AGENTS hard rule 2).
- No new dependencies, no settings changes, no JS/Svelte changes.
- No component CSS; style only with existing Basecoat classes.
- Tests run via `make test` (`pytest` with `DJANGO_SETTINGS_MODULE=config.settings.test`).
- Frontend verification: `cd frontend && pnpm run build`.

---

### Task 1: Red tests for the shell layout split

**Files:**
- Modify: `apps/users/tests/test_views.py` (class `AllauthPagesTests`)

**Interfaces:**
- Consumes: existing `User` factory pattern in the test file (`User.objects.create_user(email=..., username=..., password=...)`).
- Produces: the shell-chrome assertions that Tasks 2 and 3 must satisfy:
  - management pages contain `data-turbo="true"` and `data-svelte-bridge-component-value="app/Sidebar"`
  - public pages contain neither.

- [ ] **Step 1: Write the failing tests**

Replace `test_public_account_pages_render` and `test_authenticated_management_pages_render` in `apps/users/tests/test_views.py` with:

```python
    def test_public_account_pages_render(self):
        urls = [
            reverse("account_login"),
            reverse("account_signup"),
            reverse("account_reset_password"),
            reverse("account_reset_password_done"),
            reverse("account_email_verification_sent"),
            reverse("account_inactive"),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, 'data-turbo="true"')
                self.assertNotContains(response, "app/Sidebar")

    def test_authenticated_management_pages_render(self):
        self.client.force_login(self.user)
        urls = [
            reverse("account_change_password"),
            reverse("account_email"),
            reverse("account_reauthenticate"),
            reverse("account_set_password"),
            reverse("socialaccount_connections"),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'data-turbo="true"')
                self.assertContains(response, 'data-svelte-bridge-component-value="app/Sidebar"')
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `make test apps/users/tests/test_views.py::AllauthPagesTests -v`
Expected: FAIL in `test_authenticated_management_pages_render` — "Response content did not contain" `data-turbo="true"` (the templates still extend `base.html`; `socialaccount_connections` renders stock allauth markup).

- [ ] **Step 3: Commit the red test**

```bash
git add apps/users/tests/test_views.py
git commit -m "test: assert allauth pages split between shell and public layouts"
```

---

### Task 2: Move four account templates into the shell

**Files:**
- Modify: `templates/account/email.html`
- Modify: `templates/account/password_change.html`
- Modify: `templates/account/password_set.html`
- Modify: `templates/account/reauthenticate.html`

**Interfaces:**
- Consumes: the shell-chrome assertions from Task 1 for `account_email`, `account_change_password`, `account_reauthenticate`, `account_set_password`.
- Produces: the in-shell template pattern (`{% extends "base_app.html" %}` + `{% block page_title %}` + `w-full max-w-2xl space-y-6` wrapper) that Task 3 copies for the Connections page.

- [ ] **Step 1: Rewrite `templates/account/email.html`**

Full new content (first tag must be the extends):

```html
{% extends "base_app.html" %}

{% block page_title %}Email Addresses{% endblock %}

{% block content %}
<div class="w-full max-w-2xl space-y-6">
  <div class="card">
    <header class="p-5">
      <h2 class="text-3xl font-bold">Email Addresses</h2>
      <p class="text-muted-foreground mt-2 text-sm">The following email addresses are associated with your account:</p>
    </header>
    <section class="p-5">
      {% if emailaddresses %}
        <form method="post" action="{% url 'account_email' %}" class="space-y-4" data-controller="email-confirm" data-action="submit->email-confirm#submit">
          {% csrf_token %}
          <div class="space-y-2">
            {% for radio in emailaddress_radios %}
              {% with emailaddress=radio.emailaddress %}
                <label class="hover:bg-muted flex cursor-pointer items-center gap-3 rounded-md px-3 py-2 transition-colors">
                  <input type="radio" name="email" value="{{ emailaddress.email }}" id="{{ radio.id }}" class="size-4 accent-primary"{% if radio.checked %} checked{% endif %}>
                  <span class="flex flex-1 flex-wrap items-center gap-2 text-sm">
                    {{ emailaddress.email }}
                    {% if emailaddress.verified %}
                      <span class="badge" data-variant="secondary">Verified</span>
                    {% else %}
                      <span class="badge" data-variant="outline">Unverified</span>
                    {% endif %}
                    {% if emailaddress.primary %}
                      <span class="badge">Primary</span>
                    {% endif %}
                  </span>
                </label>
              {% endwith %}
            {% endfor %}
          </div>
          <div class="flex flex-wrap gap-2">
            <button class="btn" type="submit" name="action_primary">Make Primary</button>
            <button class="btn" type="submit" name="action_send" data-variant="secondary">Re-send Verification</button>
            <button class="btn" type="submit" name="action_remove" data-variant="destructive">Remove</button>
          </div>
        </form>
      {% else %}
        {% include "account/snippets/warn_no_email.html" %}
      {% endif %}

      {% if can_add_email %}
        <div class="mt-6 border-t pt-6">
          <h3 class="mb-3 text-lg font-bold">Add Email Address</h3>
          <form method="post" action="{% url 'account_email' %}" class="space-y-4">
            {% csrf_token %}
            {% include "account/_form_fields.html" %}
            <button class="btn w-full" name="action_add" type="submit">Add Email</button>
          </form>
        </div>
      {% endif %}
    </section>
  </div>
  <p class="text-muted-foreground text-sm">
    <a href="{% url 'profile' %}" class="underline-offset-4 hover:underline">Back to profile</a>
  </p>
</div>
{% endblock %}
```

- [ ] **Step 2: Rewrite `templates/account/password_change.html`**

```html
{% extends "base_app.html" %}

{% block page_title %}Change Password{% endblock %}

{% block content %}
<div class="w-full max-w-2xl space-y-6">
  <div class="card">
    <header class="p-5">
      <h2 class="text-3xl font-bold">Change Password</h2>
      <p class="text-muted-foreground mt-2 text-sm">Keep your account secure.</p>
    </header>
    <section class="p-5">
      <form method="post" action="{% url 'account_change_password' %}" class="space-y-4">
        {% csrf_token %}
        {{ redirect_field }}
        {% include "account/_form_fields.html" %}
        <button class="btn w-full" type="submit">Change Password</button>
      </form>
      <a href="{% url 'account_reset_password' %}" class="text-muted-foreground hover:text-foreground mt-4 block text-center text-sm underline-offset-4 hover:underline">Forgot Password?</a>
    </section>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 3: Rewrite `templates/account/password_set.html`**

```html
{% extends "base_app.html" %}

{% block page_title %}Set Password{% endblock %}

{% block content %}
<div class="w-full max-w-2xl space-y-6">
  <div class="card">
    <header class="p-5">
      <h2 class="text-3xl font-bold">Set Password</h2>
      <p class="text-muted-foreground mt-2 text-sm">Add a password to your account.</p>
    </header>
    <section class="p-5">
      <form method="post" action="{% url 'account_set_password' %}" class="space-y-4">
        {% csrf_token %}
        {{ redirect_field }}
        {% include "account/_form_fields.html" %}
        <button class="btn w-full" type="submit" name="action">Set Password</button>
      </form>
    </section>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 4: Rewrite `templates/account/reauthenticate.html`**

```html
{% extends "base_app.html" %}

{% block page_title %}Re-authenticate{% endblock %}

{% block content %}
<div class="w-full max-w-2xl space-y-6">
  <div class="card">
    <header class="p-5">
      <h2 class="text-3xl font-bold">Re-authenticate</h2>
      <p class="text-muted-foreground mt-2 text-sm">Enter your password to continue.</p>
    </header>
    <section class="p-5">
      <form method="post" action="{% url 'account_reauthenticate' %}" class="space-y-4">
        {% csrf_token %}
        {{ redirect_field }}
        {% include "account/_form_fields.html" %}
        <button class="btn w-full" type="submit">Confirm</button>
      </form>
    </section>
  </div>
</div>
{% endblock %}
```

- [ ] **Step 5: Run tests to verify the four account pages turn green**

Run: `make test apps/users/tests/test_views.py::AllauthPagesTests -v`
Expected: `test_authenticated_management_pages_render` still FAILS, but only on the `socialaccount_connections` subtest ("`account_change_password`, `account_email`, `account_reauthenticate`, `account_set_password`" now contain the shell chrome). Public pages still pass.

- [ ] **Step 6: Commit**

```bash
git add templates/account/email.html templates/account/password_change.html templates/account/password_set.html templates/account/reauthenticate.html
git commit -m "feat: render account management pages inside the app shell"
```

---

### Task 3: Social account connections inside the shell

**Files:**
- Create: `templates/socialaccount/base_manage.html`
- Create: `templates/socialaccount/connections.html`

**Interfaces:**
- Consumes: the in-shell pattern from Task 2 (`{% extends "base_app.html" %}` + `{% block page_title %}` + `w-full max-w-2xl space-y-6` wrapper); the Task 1 assertion for `socialaccount_connections`.
- Produces: nothing consumed by later tasks. Stock chain is preserved: `connections.html` extends `base_manage.html` (which now extends `base_app.html`), so future manage pages inherit the shell automatically. Pre-auth social pages (`signup`, `login`, `login_cancelled`, `authentication_error`) still extend `socialaccount/base_entrance.html` and stay public.

- [ ] **Step 1: Create `templates/socialaccount/base_manage.html`**

```html
{% extends "base_app.html" %}
```

- [ ] **Step 2: Create `templates/socialaccount/connections.html`**

Full content (first tag must be the extends):

```html
{% extends "socialaccount/base_manage.html" %}
{% load i18n %}

{% block page_title %}Account Connections{% endblock %}

{% block content %}
<div class="w-full max-w-2xl space-y-6">
  <div class="card">
    <header class="p-5">
      <h2 class="text-3xl font-bold">Account Connections</h2>
      <p class="text-muted-foreground mt-2 text-sm">You can sign in to your account using any of the following third-party accounts.</p>
    </header>
    <section class="p-5">
      {% if form.accounts %}
        <form method="post" action="{% url 'socialaccount_connections' %}" class="space-y-4">
          {% csrf_token %}
          <div class="space-y-2">
            {% for acc in form.fields.account.choices %}
              {% with account=acc.0.instance.get_provider_account %}
                <label class="hover:bg-muted flex cursor-pointer items-center gap-3 rounded-md px-3 py-2 transition-colors">
                  <input type="radio" name="account" value="{{ account.account.pk }}" class="size-4 accent-primary">
                  <span class="flex flex-1 flex-wrap items-center gap-2 text-sm">
                    {{ account }}
                    <span class="badge" data-variant="secondary">{{ account.get_brand.name }}</span>
                  </span>
                </label>
              {% endwith %}
            {% endfor %}
          </div>
          <button class="btn" type="submit" data-variant="destructive">Remove</button>
        </form>
      {% else %}
        <p class="text-muted-foreground text-sm">
          You currently have no third-party accounts connected to this account.
        </p>
      {% endif %}

      <div class="mt-6 border-t pt-6">
        <h3 class="mb-3 text-lg font-bold">Add a Third-Party Account</h3>
        {% include "socialaccount/snippets/provider_list.html" with process="connect" %}
        {% include "socialaccount/snippets/login_extra.html" %}
      </div>
    </section>
  </div>
  <p class="text-muted-foreground text-sm">
    <a href="{% url 'profile' %}" class="underline-offset-4 hover:underline">Back to profile</a>
  </p>
</div>
{% endblock %}
```

- [ ] **Step 3: Run tests to verify all green**

Run: `make test apps/users/tests/test_views.py::AllauthPagesTests -v`
Expected: PASS for both tests. `socialaccount_connections` now renders the shell chrome; public pages still assert it is absent.

- [ ] **Step 4: Commit**

```bash
git add templates/socialaccount/base_manage.html templates/socialaccount/connections.html
git commit -m "feat: render social account connections inside the app shell"
```

---

### Task 4: Full verification

**Files:** none (verification only; fix anything that surfaces).

- [ ] **Step 1: Run the full test suite**

Run: `make test`
Expected: all green.

- [ ] **Step 2: Check for template lint regressions**

Run: `cd frontend && pnpm run build`
Expected: builds clean. (Template changes cannot affect the JS build; this guards against accidental frontend edits and confirms the shell's CSS classes used by the new templates exist in the built `dist/assets/main-*.css` — grep for `.card` if in doubt, per AGENTS hard rule 1.)

- [ ] **Step 3: Manual smoke (optional but recommended)**

Run the dev server, log in, and click Email / Password / Connections in the sidebar: each page renders inside the shell with the sidebar persisting (Turbo), and the active nav item highlights. Submit an invalid password-change form: it re-renders the same page with errors, no navigation glitch.

- [ ] **Step 4: Commit any incidental fixes**

Only if a step above forced a change:

```bash
git add -A
git commit -m "fix: [describe the fix]"
```