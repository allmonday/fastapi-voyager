import SchemaFieldFilter from "./component/schema-field-filter.js";
import SchemaCodeDisplay from "./component/schema-code-display.js";
import RouteCodeDisplay from "./component/route-code-display.js";
import Demo from './component/demo.js'
import RenderGraph from "./component/render-graph.js";
import { GraphUI } from "./graph-ui.js";
import { store } from './store.js'

const { createApp, onMounted, ref } = window.Vue;

const app = createApp({
  setup() {
    let graphUI = null;

    function readQuerySelection() {
      if (typeof window === "undefined") {
        return { tag: null, route: null };
      }
      const params = new URLSearchParams(window.location.search);
      return {
        tag: params.get("tag") || null,
        route: params.get("route") || null,
      };
    }

    function findTagByRoute(routeId) {
      return (
        store.state.leftPanel.tags.find((tag) =>
          (tag.routes || []).some((route) => route.id === routeId)
        )?.name || null
      );
    }

    function syncSelectionToUrl() {
      if (typeof window === "undefined") {
        return;
      }
      const params = new URLSearchParams(window.location.search);
      if (store.state.leftPanel.tag) {
        params.set("tag", store.state.leftPanel.tag);
      } else {
        params.delete("tag");
      }
      if (store.state.leftPanel.routeId) {
        params.set("route", store.state.leftPanel.routeId);
      } else {
        params.delete("route");
      }
      const hash = window.location.hash || "";
      const search = params.toString();
      const base = window.location.pathname;
      const newUrl = search ? `${base}?${search}${hash}` : `${base}${hash}`;
      window.history.replaceState({}, "", newUrl);
    }

    function applySelectionFromQuery(selection) {
      let applied = false;
      if (selection.tag && store.state.leftPanel.tags.some((tag) => tag.name === selection.tag)) {
        store.state.leftPanel.tag = selection.tag;
        store.state.leftPanel._tag = selection.tag;
        applied = true;
      }
      if (selection.route && store.state.graph.routeItems?.[selection.route]) {
        store.state.leftPanel.routeId = selection.route;
        applied = true;
        const inferredTag = findTagByRoute(selection.route);
        if (inferredTag) {
          store.state.leftPanel.tag = inferredTag;
          store.state.leftPanel._tag = inferredTag;
        }
      }
      return applied;
    }

    async function loadInitial() {
      store.state.initializing = true;
      try {
        const res = await fetch("dot");
        const data = await res.json();
        store.state.leftPanel.tags = Array.isArray(data.tags) ? data.tags : [];

        const schemasArr = Array.isArray(data.schemas) ? data.schemas : [];
        // Build dict keyed by id for faster lookups and simpler prop passing
        const schemaMap = Object.fromEntries(
          schemasArr.map((s) => [s.id, s])
        );
        store.state.graph.schemaMap = schemaMap
        store.state.graph.schemaKeys = new Set(Object.keys(schemaMap));
        store.state.graph.routeItems = data.tags
          .map((t) => t.routes)
          .flat()
          .reduce((acc, r) => {
            acc[r.id] = r;
            return acc;
          }, {});
        store.state.modeControl.briefModeEnabled = data.enable_brief_mode || false;
        store.state.version = data.version || "";
        store.state.swagger.url = data.swagger_url || null

        const querySelection = readQuerySelection();
        const restoredFromQuery = applySelectionFromQuery(querySelection);
        if (restoredFromQuery) {
          syncSelectionToUrl();
          onGenerate();
          return;
        }

        switch (data.initial_page_policy) {
          case "full":
            onGenerate()
            return
          case "empty":
            return
          case "first":
            store.state.leftPanel.tag = store.state.leftPanel.tags.length > 0 ? store.state.leftPanel.tags[0].name : null;
            store.state.leftPanel._tag = store.state.leftPanel.tag;
            onGenerate();
            return
        }

        // default route options placeholder
      } catch (e) {
        console.error("Initial load failed", e);
      } finally {
        store.state.initializing = false;
      }
    }

    async function onFocusChange(val) {
      if (val) {
        await onGenerate(true); // target could be out of view when switchingfrom big to small
      } else {
        await onGenerate(false);
        setTimeout(() => {
          const ele = $(`[data-name='${store.state.schemaDetail.schemaCodeName}'] polygon`);
          ele.dblclick();
        }, 1);
      }
    }

    async function onGenerate(resetZoom = true) {
      const schema_name = store.state.modeControl.focus ? store.state.schemaDetail.schemaCodeName : null;
      store.state.generating = true;
      try {
        const payload = {
          tags: store.state.leftPanel.tag ? [store.state.leftPanel.tag] : null,
          schema_name: schema_name || null,
          route_name: store.state.leftPanel.routeId || null,
          show_fields: store.state.filter.showFields,
          brief: store.state.modeControl.brief,
          hide_primitive_route: store.state.filter.hidePrimitiveRoute,
          show_module: store.state.filter.showModule,
        };
        const res = await fetch("dot", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const dotText = await res.text();

        // create graph instance once
        if (!graphUI) {
          graphUI = new GraphUI("#graph", {
            onSchemaShiftClick: (id) => {
              if (store.state.graph.schemaKeys.has(id)) {
                resetDetailPanels();
                store.state.searchDialog.show = true;
                store.state.searchDialog.schema = id;
              }
            },
            onSchemaClick: (id) => {
              resetDetailPanels();
              if (store.state.graph.schemaKeys.has(id)) {
                store.state.schemaDetail.schemaCodeName = id;
                store.state.rightDrawer.drawer = true;
              }
              if (id in store.state.graph.routeItems) {
                store.state.routeDetail.routeCodeId = id;
                store.state.routeDetail.show = true;
              }
            },
            resetCb: () => {
              resetDetailPanels();
            },
          });
        }
        await graphUI.render(dotText, resetZoom);
      } catch (e) {
        console.error("Generate failed", e);
      } finally {
        store.state.generating = false;
      }
    }

    function showSearchDialog() {
      store.state.searchDialog.show = true;
      store.state.searchDialog.schema = null;
    }

    function resetDetailPanels() {
      store.state.rightDrawer.drawer = false;
      store.state.routeDetail.show = false
      store.state.schemaDetail.schemaCodeName = "";
    }

    async function onReset() {
      store.state.leftPanel.tag = null;
      store.state.leftPanel._tag = null;
      store.state.leftPanel.routeId = null;

      store.state.graph.schemaId = null;

      // state.showFields = "object";
      store.state.modeControl.focus = false;
      store.state.schemaDetail.schemaCodeName = "";
      onGenerate();
      syncSelectionToUrl();
    }

    function toggleTag(tagName, expanded = null) {
      if (expanded === true) {
        store.state.leftPanel._tag = tagName;
        store.state.leftPanel.tag = tagName;
        store.state.leftPanel.routeId = "";

        store.state.modeControl.focus = false;
        store.state.schemaDetail.schemaCodeName = "";
        onGenerate();
      } else {
        store.state.leftPanel._tag = null;
      }

      store.state.rightDrawer.drawer = false;
      store.state.routeDetail.show = false
      syncSelectionToUrl();
    }

    function selectRoute(routeId) {
      if (store.state.leftPanel.routeId === routeId) {
        store.state.leftPanel.routeId = "";
      } else {
        store.state.leftPanel.routeId = routeId;
      }
      store.state.rightDrawer.drawer = false;
      store.state.routeDetail.show = false
      store.state.modeControl.focus = false;
      store.state.schemaDetail.schemaCodeName = "";
      onGenerate();
      syncSelectionToUrl();
    }

    function toggleShowModule(val) {
      store.state.filter.showModule = val;
      onGenerate()
    }

    function toggleShowField(field) {
      store.state.filter.showFields = field;
      onGenerate(false);
    }

    function toggleBrief(val) {
      store.state.modeControl.brief = val;
      onGenerate();
    }

    function toggleHidePrimitiveRoute(val) {
      store.state.filter.hidePrimitiveRoute = val;
      onGenerate(false);
    }

    function startDragDrawer(e) {
      const startX = e.clientX;
      const startWidth = store.state.rightDrawer.width;

      function onMouseMove(moveEvent) {
        const deltaX = startX - moveEvent.clientX;
        const newWidth = Math.max(300, Math.min(800, startWidth + deltaX));
        store.state.rightDrawer.width = newWidth;
      }

      function onMouseUp() {
        document.removeEventListener("mousemove", onMouseMove);
        document.removeEventListener("mouseup", onMouseUp);
        document.body.style.cursor = "";
        document.body.style.userSelect = "";
      }

      document.addEventListener("mousemove", onMouseMove);
      document.addEventListener("mouseup", onMouseUp);
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
      e.preventDefault();
    }

    onMounted(async () => {
      document.body.classList.remove("app-loading")
      await loadInitial();
      // Reveal app content only after initial JS/data is ready
    });

    return {
      store,
      toggleTag,
      toggleBrief,
      toggleHidePrimitiveRoute,
      selectRoute,
      onGenerate,
      onReset,
      showSearchDialog,
      toggleShowField,
      startDragDrawer,
      onFocusChange,
      toggleShowModule,
    };
  },
});

app.use(window.Quasar);

// Set Quasar primary theme color to green
if (window.Quasar && typeof window.Quasar.setCssVar === "function") {
  window.Quasar.setCssVar("primary", "#009485");
}

app.component("schema-field-filter", SchemaFieldFilter);  // shift click and see relationships
app.component("schema-code-display", SchemaCodeDisplay);  // double click to see node details
app.component("route-code-display", RouteCodeDisplay);  // double click to see route details
app.component("render-graph", RenderGraph);   // for debug, render pasted dot content
app.component('demo-component', Demo)

app.mount("#q-app");
