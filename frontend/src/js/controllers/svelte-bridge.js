import { Controller } from "@hotwired/stimulus";
import { mount, unmount } from "svelte";

// All Svelte components, lazy-loaded. Keys are relative to ../svelte/ (no extension),
// e.g. "library/components/Welcome" for ../svelte/library/components/Welcome.svelte.
const components = import.meta.glob("../svelte/**/*.svelte");

export default class extends Controller {
  static values = {
    component: String,
    props: { type: Object, default: {} },
  };

  connect() {
    const name = this.componentValue;
    if (!name) return;

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
          props: this.propsValue,
        });
      })
      .catch((err) => {
        console.error(`svelte-bridge: failed to load ${name}.svelte`, err);
      });
  }

  disconnect() {
    this.removed = true;
    if (this.instance) {
      unmount(this.instance);
      this.instance = null;
    }
  }
}
