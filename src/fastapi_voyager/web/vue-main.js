import SchemaFieldFilter from "./component/schema-field-filter.js";
import SchemaCodeDisplay from "./component/schema-code-display.js";
import RouteCodeDisplay from "./component/route-code-display.js";
import Demo from './component/demo.js'
import RenderGraph from "./component/render-graph.js";
import { GraphUI } from "./graph-ui.js";
import { store } from './store.js'

const { createApp, reactive, onMounted, ref } = window.Vue;

const app = createApp({
  setup() {
    const state = reactive({
      // options and selections
      showFields: "object",
      brief: false,
      focus: false,
      hidePrimitiveRoute: false,
      rawSchemas: new Set(), // [{ name, id }]
      rawSchemasFull: {}, // full schemas dict: { [schema.id]: schema }
      showModule: true,
    });

    const showDumpDialog = ref(false);
    const dumpJson = ref("");
    const showImportDialog = ref(false);
    const importJsonText = ref("");

    const showRenderGraph = ref(false);

    const renderCoreData = ref(null);

    const schemaName = ref(""); // used by detail dialog
    const schemaCodeName = ref("");
    const routeCodeId = ref("");
    const showRouteDetail = ref(false);

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
      if (selection.route && state.routeItems?.[selection.route]) {
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
        state.rawSchemasFull = Object.fromEntries(
          schemasArr.map((s) => [s.id, s])
        );
        state.rawSchemas = new Set(Object.keys(state.rawSchemasFull));
        state.routeItems = data.tags
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
          const ele = $(`[data-name='${schemaCodeName.value}'] polygon`);
          ele.dblclick();
        }, 1);
      }
    }

    async function onGenerate(resetZoom = true) {
      const schema_name = state.focus ? schemaCodeName.value : null;
      store.state.generating = true;
      try {
        const payload = {
          tags: store.state.leftPanel.tag ? [store.state.leftPanel.tag] : null,
          schema_name: schema_name || null,
          route_name: store.state.leftPanel.routeId || null,
          show_fields: state.showFields,
          brief: state.brief,
          hide_primitive_route: state.hidePrimitiveRoute,
          show_module: state.showModule,
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
              if (state.rawSchemas.has(id)) {
                resetDetailPanels();
                store.state.searchDialog.show = true;
                store.state.searchDialog.schema = id;
              }
            },
            onSchemaClick: (id) => {
              resetDetailPanels();
              if (state.rawSchemas.has(id)) {
                schemaCodeName.value = id;
                store.state.rightDrawer.drawer = true;
              }
              if (id in state.routeItems) {
                routeCodeId.value = id;
                showRouteDetail.value = true;
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

    // async function onDumpData() {
    //   try {
    //     const payload = {
    //       tags: state.tag ? [state.tag] : null,
    //       schema_name: state.schemaId || null,
    //       route_name: state.routeId || null,
    //       show_fields: state.showFields,
    //       brief: state.brief,
    //     };
    //     const res = await fetch("dot-core-data", {
    //       method: "POST",
    //       headers: { "Content-Type": "application/json" },
    //       body: JSON.stringify(payload),
    //     });
    //     const json = await res.json();
    //     dumpJson.value = JSON.stringify(json, null, 2);
    //     showDumpDialog.value = true;
    //   } catch (e) {
    //     console.error("Dump data failed", e);
    //   }
    // }

    // async function copyDumpJson() {
    //   try {
    //     await navigator.clipboard.writeText(dumpJson.value || "");
    //     if (window.Quasar?.Notify) {
    //       window.Quasar.Notify.create({ type: "positive", message: "Copied" });
    //     }
    //   } catch (e) {
    //     console.error("Copy failed", e);
    //   }
    // }

    // function openImportDialog() {
    //   importJsonText.value = "";
    //   showImportDialog.value = true;
    // }

    // async function onImportConfirm() {
    //   let payloadObj = null;
    //   try {
    //     payloadObj = JSON.parse(importJsonText.value || "{}");
    //   } catch (e) {
    //     if (window.Quasar?.Notify) {
    //       window.Quasar.Notify.create({
    //         type: "negative",
    //         message: "Invalid JSON",
    //       });
    //     }
    //     return;
    //   }
    //   // Move the request into RenderGraph component: pass the parsed object and let the component call /dot-render-core-data
    //   renderCoreData.value = payloadObj;
    //   showRenderGraph.value = true;
    //   showImportDialog.value = false;
    // }

    function showSearchDialog() {
      store.state.searchDialog.show = true;
      store.state.searchDialog.schema = null;
    }

    function resetDetailPanels() {
      store.state.rightDrawer.drawer = false;
      showRouteDetail.value = false;
      schemaCodeName.value = "";
    }

    async function onReset() {
      // state.tag = null;
      // state._tag = null;
      // state.routeId = "";
      // state.schemaId = null;

      store.state.leftPanel.tag = null;
      store.state.leftPanel._tag = null;
      store.state.leftPanel.routeId = null;

      store.state.graph.schemaId = null;

      // state.showFields = "object";
      state.focus = false;
      schemaCodeName.value = "";
      onGenerate();
      syncSelectionToUrl();
    }

    function toggleTag(tagName, expanded = null) {
      if (expanded === true) {
        store.state.leftPanel._tag = tagName;
        store.state.leftPanel.tag = tagName;
        store.state.leftPanel.routeId = "";

        state.focus = false;
        schemaCodeName.value = "";
        onGenerate();
      } else {
        store.state.leftPanel._tag = null;
      }

      store.state.rightDrawer.drawer = false;
      showRouteDetail.value = false;
      syncSelectionToUrl();
    }

    function selectRoute(routeId) {
      if (store.state.leftPanel.routeId === routeId) {
        store.state.leftPanel.routeId = "";
      } else {
        store.state.leftPanel.routeId = routeId;
      }
      store.state.rightDrawer.drawer = false;
      showRouteDetail.value = false;
      state.focus = false;
      schemaCodeName.value = "";
      onGenerate();
      syncSelectionToUrl();
    }

    function toggleShowModule(val) {
      state.showModule = val;
      onGenerate()
    }

    function toggleShowField(field) {
      state.showFields = field;
      onGenerate(false);
    }

    function toggleBrief(val) {
      state.brief = val;
      onGenerate();
    }

    function toggleHidePrimitiveRoute(val) {
      state.hidePrimitiveRoute = val;
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
      state,
      toggleTag,
      toggleBrief,
      toggleHidePrimitiveRoute,
      selectRoute,
      onGenerate,
      onReset,
      showRouteDetail,
      schemaName,
      showSearchDialog,
      schemaCodeName,
      routeCodeId,
      // dump/import
      // showDumpDialog,
      // dumpJson,
      // copyDumpJson,
      // onDumpData,
      // showImportDialog,
      // importJsonText,
      // openImportDialog,
      // onImportConfirm,
      // render graph dialog
      showRenderGraph,
      renderCoreData,
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
