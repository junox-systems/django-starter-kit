import { Controller } from "@hotwired/stimulus";
import { mount, unmount } from "svelte";

export default class extends Controller {
  static values = {
    component: String,
    props: { type: Object, default: {} },
  };

  connect() {
    const name = this.componentValue;
    if (!name) return;

    import(`../svelte/${name}.svelte`)
      .then((mod) => {
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
    if (this.instance) {
      unmount(this.instance);
      this.instance = null;
    }
  }
}
