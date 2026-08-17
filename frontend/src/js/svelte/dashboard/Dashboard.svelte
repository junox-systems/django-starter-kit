<script>
  import AccountStatus from "./AccountStatus.svelte";
  import ActivityFeed from "./ActivityFeed.svelte";

  // The one Svelte root on the dashboard. Django mounts this via svelte-bridge
  // with the whole payload as props (see templates/dashboard/index.html).
  // It owns the layout grid and any state shared across panels; children get
  // props and callbacks, never their own stores or context.
  let { activity, account, urls } = $props();

  // Server-rendered entries are shown until a refresh replaces them.
  let refreshed = $state(null);
  let refreshing = $state(false);
  let error = $state("");

  const entries = $derived(refreshed ?? activity.entries);

  async function refreshActivity() {
    refreshing = true;
    error = "";
    try {
      // GET only, so no CSRF token is needed. A panel that POSTs would have to
      // solve CSRF exposure first — nothing provides it to JS yet.
      const res = await fetch(urls.activity, { credentials: "same-origin" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      refreshed = await res.json();
    } catch (err) {
      error = "Could not refresh activity. Please try again.";
      console.error("dashboard: activity refresh failed", err);
    } finally {
      refreshing = false;
    }
  }
</script>

<div class="grid gap-6 lg:grid-cols-2">
  <ActivityFeed {entries} {refreshing} {error} onrefresh={refreshActivity} />
  <AccountStatus checks={account.checks} lastLogin={account.last_login} />
</div>
