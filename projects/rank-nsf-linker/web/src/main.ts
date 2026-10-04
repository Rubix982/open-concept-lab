import { createApp } from "vue";
import App from "./App.vue";
import "./styles.css";

// An earlier version installed an offline service worker that served stale pages and API
// responses; remove it for anyone who still has it.
navigator.serviceWorker?.getRegistrations().then((regs) => regs.forEach((r) => r.unregister()));
caches?.keys().then((keys) => keys.forEach((k) => caches.delete(k)));

createApp(App).mount("#app");
