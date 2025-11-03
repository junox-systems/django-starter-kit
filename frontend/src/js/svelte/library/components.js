// --- auto-import all Svelte components in ./components ---
// Each .svelte file becomes available as a named export by filename.
// Example: ./components/Button.svelte → export { Button }

const modules = import.meta.glob("./components/*.svelte", { eager: true });

// Build a single Components object (safe in ESM)
export const Components = Object.fromEntries(
  Object.entries(modules).map(([path, mod]) => [
    path.split("/").pop().replace(".svelte", ""),
    mod.default,
  ])
);
