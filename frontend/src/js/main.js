// Import Vite modulepreload polyfill [django-vite docs]
import "vite/modulepreload-polyfill";

// import CSS styles
import "../css/styles.css";

// HyperDX — RUM, session replay, and frontend → backend trace linking.
// Skipped if VITE_HYPERDX_URL is not set (e.g., when no clickstack is running).
import HyperDX from "@hyperdx/browser";

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

  HyperDX.init(initConfig);
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
