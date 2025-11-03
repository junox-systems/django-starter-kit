import { Controller } from "@hotwired/stimulus";
import { mount } from "svelte";
import { Components as C } from "$lib/components";

export default class extends Controller {
  initialize() {
    console.log("info: 'welcome-svelte' controller initialized.");
  }

  connect() {
    const { Welcome } = C;

    this.component = mount(Welcome, {
      target: this.element,
    });

    console.log("info: 'welcome-svelte' component connected and mounted.");
  }

  disconnect() {
    if (this.component) {
      this.component.$destroy();
    }
  }
}
