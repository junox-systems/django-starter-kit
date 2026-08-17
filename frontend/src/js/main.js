// Import Vite modulepreload polyfill [django-vite docs]
import "vite/modulepreload-polyfill";

// import CSS styles
import "../css/styles.css";

// Turbo Drive — persistent navigation for the authenticated app shell.
// Importing the package calls Turbo.start() for us.
import * as Turbo from "@hotwired/turbo";

// Opt-in, NOT global: only subtrees marked data-turbo="true" use Drive — i.e.
// the app shell in templates/base_app.html. Marketing pages keep plain page
// loads (their Three.js island is heavy and has its own lifecycle), and only
// the shell benefits from a persistent sidebar.
Turbo.config.drive.enabled = false;

// Forms stay browser-native. Django re-renders an invalid form as HTTP 200,
// which Turbo Drive rejects ("form responses must redirect"). Django forms +
// full page loads are the primary pattern here, so leave them alone.
Turbo.config.forms.mode = "off";

// HyperDX — RUM, session replay, and frontend → backend trace linking. Opt-in.
//
// Imported DYNAMICALLY on purpose. It pulls in rrweb + OpenTelemetry (~650 kB),
// and VITE_HYPERDX_URL ships empty, so a static import made every page parse all
// of it and then never call it. `import.meta.env.VITE_*` is inlined at build
// time, so with the var unset this whole branch — and the chunk — is dropped.
//
// Consequence: enabling HyperDX requires a rebuild (already true, it is a
// build-time var), and init lands one microtask later, so the very earliest
// console/network events are not captured.
const hyperdxUrl = import.meta.env.VITE_HYPERDX_URL;
if (hyperdxUrl) {
  const initConfig = {
    service:
      import.meta.env.VITE_HYPERDX_SERVICE || "django-starter-kit-frontend",
    url: hyperdxUrl,
    consoleCapture: true,
    tracePropagationTargets: [/\/api\/v1\//i],
    otelResourceAttributes: {
      "deployment.environment": import.meta.env.MODE || "development",
    },
  };

  // Only add apiKey if explicitly set (omit for self-hosted ClickStack)
  const apiKey = import.meta.env.VITE_HYPERDX_API_KEY;
  if (apiKey) {
    initConfig.apiKey = apiKey;
  }

  import("@hyperdx/browser")
    .then(({ default: HyperDX }) => HyperDX.init(initConfig))
    .catch((err) => console.error("HyperDX failed to load", err));
}

// Import GSAP
import { gsap } from "gsap";

// Import Stimulus
import { Application } from "@hotwired/stimulus";

// Start Stimulus application
const app = Application.start();

// Auto-register Stimulus controllers
const modules = import.meta.glob("./controllers/**/*.js", { eager: true });

Object.entries(modules).forEach(([filename, module]) => {
  // Convert the filename to a controller name
  const controllerName = filename
    // Remove the leading "./" and "controllers/"
    .replace(/^\.\//, "")
    .replace(/^controllers\//, "")
    // Remove the ".js" extension
    .replace(/\.js$/, "")
    // Replace underscores with dashes
    .replace(/_/g, "-")
    // Replace slashes with double dashes
    .replace(/\//g, "--");

  // Register the controller with the Stimulus application
  app.register(controllerName, module.default);
});

// Expose Stimulus application globally
window.Stimulus = app;
