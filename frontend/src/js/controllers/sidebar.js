import { Controller } from "@hotwired/stimulus";

// Mobile drawer for the Basecoat `.sidebar` component.
//
// All layout comes from Basecoat CSS, which reads two attributes off the
// `.sidebar` element:
//   data-sidebar-initialized — un-hides it below `md` (the no-JS baseline is
//                              `max-md:hidden`, so desktop works without JS)
//   aria-hidden="true"       — slides the nav out and drops the content margin
//
// Desktop keeps the sidebar open permanently, so `aria-hidden` is only ever
// set below `md`. Mounted on a wrapper so the app bar's toggle button — which
// lives outside the sidebar — can reach it.
export default class extends Controller {
  static targets = ["panel"];

  connect() {
    // Tailwind's `md` breakpoint. Keep in sync with the CSS if that changes.
    this.desktop = window.matchMedia("(min-width: 48rem)");
    this.sync = this.sync.bind(this);
    this.desktop.addEventListener("change", this.sync);
  }

  disconnect() {
    this.desktop.removeEventListener("change", this.sync);
  }

  // Initialise from the target callback, NOT connect(): the sidebar is
  // data-turbo-permanent, so on a Turbo visit this controller connects to the
  // new page before Turbo has relocated the sidebar into it. Reading
  // this.panelTarget in connect() throws "Missing target element".
  panelTargetConnected() {
    this.panelTarget.dataset.sidebarInitialized = "";
    this.sync();
  }

  // Open on desktop, closed on mobile — whenever the breakpoint changes.
  sync() {
    if (!this.hasPanelTarget) return;
    if (this.desktop.matches) {
      this.panelTarget.removeAttribute("aria-hidden");
    } else {
      this.panelTarget.setAttribute("aria-hidden", "true");
    }
  }

  close() {
    if (this.hasPanelTarget && !this.desktop.matches) {
      this.panelTarget.setAttribute("aria-hidden", "true");
    }
  }

  toggle() {
    if (!this.hasPanelTarget) return;
    if (this.panelTarget.getAttribute("aria-hidden") === "false") {
      this.close();
    } else {
      this.panelTarget.setAttribute("aria-hidden", "false");
    }
  }

  // The `.sidebar` element is itself the mobile backdrop; `nav` sits inside it.
  backdrop(event) {
    if (event.target === this.panelTarget) this.close();
  }
}
