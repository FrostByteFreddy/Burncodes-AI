// The interface font, served from our own domain rather than Google's
import "@fontsource/atkinson-hyperlegible-next/400.css";
import "@fontsource/atkinson-hyperlegible-next/400-italic.css";
import "@fontsource/atkinson-hyperlegible-next/500.css";
import "@fontsource/atkinson-hyperlegible-next/600.css";
import "@fontsource/atkinson-hyperlegible-next/700.css";
import "@fontsource/atkinson-hyperlegible-mono/400.css";
import "@fontsource/atkinson-hyperlegible-mono/500.css";
import "./assets/main.css";
import "highlight.js/styles/github-dark.css";
import "vue-sonner/style.css";

import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router"; // We will create this file next
import i18n from "./i18n";

/* import the fontawesome core */
import { library } from "@fortawesome/fontawesome-svg-core";

/* import font awesome icon component */
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";

/* import all solid icons */
import { fas } from "@fortawesome/free-solid-svg-icons";
import { faChartLine, faHistory } from "@fortawesome/free-solid-svg-icons";

/* import all regular icons */
import { far } from "@fortawesome/free-regular-svg-icons";

/* import all brand icons */
import { fab } from "@fortawesome/free-brands-svg-icons";

/* add icons to the library */
library.add(fas, far, fab, faChartLine, faHistory);

const app = createApp(App);

app.use(createPinia());
app.use(router);
app.use(i18n);
app.component("font-awesome-icon", FontAwesomeIcon);

app.mount("#app");
