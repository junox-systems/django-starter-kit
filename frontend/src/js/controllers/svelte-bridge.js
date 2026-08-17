import { Controller } from "@hotwired/stimulus";
import { mount, unmount } from "svelte";

// All Svelte components, lazy-loaded. Keys are relative to ../svelte/ (no extension),
// e.g. "library/components/Foo" for ../svelte/library/components/Foo.svelte.
const components = import.meta.glob("../svelte/**/*.svelte");

export default class extends Controller {
  static values = {
    component: String,
    props: { type: Object, default: {} },
    // Optional: id of a {{ data|json_script:"..." }} node to read props from.
    // Preferred for server-rendered data — no attribute-escaping hazard.
    propsId: String,
  };

  // Props from a json_script node if given, else the inline attribute.
  get resolvedProps() {
    if (!this.propsIdValue) return this.propsValue;
    const el = document.getElementById(this.propsIdValue);
    if (!el) {
      console.error(`svelte-bridge: no json_script node #${this.propsIdValue}`);
      return this.propsValue;
    }
    return JSON.parse(el.textContent);
  }

  get isPermanent() {
    return this.element.hasAttribute("data-turbo-permanent");
  }

  connect() {
    this.removed = false;
    const name = this.componentValue;
    if (!name) return;

    // Turbo relocates a data-turbo-permanent element into the next page rather
    // than rebuilding it, which makes Stimulus disconnect and reconnect. The
    // existing instance is still valid — adopt it instead of mounting a second
    // copy, so the island never blinks.
    if (this.element.__svelteIsland) {
      this.instance = this.element.__svelteIsland;
      return;
    }

    const loader = components[`../svelte/${name}.svelte`];
    if (!loader) {
      console.error(`svelte-bridge: no component found for ${name}.svelte`);
      return;
    }

    loader()
      .then((mod) => {
        if (this.removed || !this.element.isConnected) return;
        this.instance = mount(mod.default, {
          target: this.element,
          props: this.resolvedProps,
        });
        if (this.isPermanent) this.element.__svelteIsland = this.instance;
      })
      .catch((err) => {
        console.error(`svelte-bridge: failed to load ${name}.svelte`, err);
      });
  }

  disconnect() {
    if (this.isPermanent) {
      // Mid-visit Turbo detaches the element before reattaching it, so absence
      // right now proves nothing. Re-check on the next tick: still detached
      // means it was genuinely discarded (we left the shell) and must be torn
      // down, or its effects and document listeners leak.
      const element = this.element;
      const instance = this.instance;
      setTimeout(() => {
        if (!element.isConnected && instance) {
          unmount(instance);
          element.__svelteIsland = null;
        }
      }, 0);
      return;
    }

    this.removed = true;
    if (this.instance) {
      unmount(this.instance);
      this.instance = null;
    }
  }
}
