import SchemaCodeDisplay from "./component/schema-code-display.js";
import RouteCodeDisplay from "./component/route-code-display.js";
import Demo from "./component/demo.js";
import RenderGraph from "./component/render-graph.js";
import { GraphUI } from "./graph-ui.js";
import { store } from "./store.js";

const { createApp, onMounted, ref, watch } = window.Vue;

const app = createApp({
  setup() {
    let graphUI = null;
    const allSchemaOptions = ref([]);
    const erDiagramLoading = ref(false);
    const erDiagramCache = ref("");

    function initGraphUI() {
      if (graphUI) {
        return;
      }
      graphUI = new GraphUI("#graph", {
        onSchemaShiftClick: (id) => {
          if (store.state.graph.schemaKeys.has(id)) {
            store.state.previousTagRoute.tag = store.state.leftPanel.tag;
            store.state.previousTagRoute.routeId = store.state.leftPanel.routeId;
            store.state.previousTagRoute.hasValue = true;
            store.state.search.mode = true;
            store.state.search.schemaName = id;
            onSearch();
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

    function rebuildSchemaOptions() {
      const dict = store.state.graph.schemaMap || {};
      const opts = Object.values(dict).map((s) => ({
        label: s.name,
        desc: s.id,
        value: s.id,
      }));
      allSchemaOptions.value = opts;
      store.state.search.schemaOptions = opts.slice();
      populateFieldOptions(store.state.search.schemaName);
    }

    function populateFieldOptions(schemaId) {
      if (!schemaId) {
        store.state.search.fieldOptions = [];
        store.state.search.fieldName = null;
        return;
      }
      const schema = store.state.graph.schemaMap?.[schemaId];
      if (!schema) {
        store.state.search.fieldOptions = [];
        store.state.search.fieldName = null;
        return;
      }
      const fields = Array.isArray(schema.fields)
        ? schema.fields.map((f) => f.name)
        : [];
      store.state.search.fieldOptions = fields;
      if (!fields.includes(store.state.search.fieldName)) {
        store.state.search.fieldName = null;
      }
    }

    function filterSearchSchemas(val, update) {
      const needle = (val || "").toLowerCase();
      update(() => {
        if (!needle) {
          store.state.search.schemaOptions = allSchemaOptions.value.slice();
          return;
        }
        store.state.search.schemaOptions = allSchemaOptions.value.filter((option) =>
          option.label.toLowerCase().includes(needle)
        );
      });
    }

    function onSearchSchemaChange(val) {
      store.state.search.schemaName = val;
      store.state.search.mode = false;
      if (!val) {
        // Clearing the select should only run resetSearch via @clear
        return;
      }
      onSearch();
    }

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
      if (
        selection.tag &&
        store.state.leftPanel.tags.some((tag) => tag.name === selection.tag)
      ) {
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

    async function resetSearch() {
      store.state.search.mode = false;
      console.log(store.state.previousTagRoute.hasValue)
      console.log(store.state.previousTagRoute)
      if (store.state.previousTagRoute.hasValue) {
        store.state.leftPanel.tag = store.state.previousTagRoute.tag;
        store.state.leftPanel._tag = store.state.previousTagRoute.tag;
        store.state.leftPanel.routeId = store.state.previousTagRoute.routeId;
        store.state.previousTagRoute.hasValue = false;
      } else {
        store.state.leftPanel.tag = null;
        store.state.leftPanel._tag = null;
        store.state.leftPanel.routeId = null;
      }

      syncSelectionToUrl()
      await loadSearchedTags();
      renderBasedOnInitialPolicy()
    }

    async function onSearch() {
      console.log('start search')
      store.state.search.mode = true;
      store.state.leftPanel.tag = null;
      store.state.leftPanel._tag = null;
      store.state.leftPanel.routeId = null;
      syncSelectionToUrl()
      await loadSearchedTags();
      await onGenerate();
    }
    async function loadSearchedTags() {
      try {
        const payload = {
          schema_name: store.state.search.schemaName,
          schema_field: store.state.search.fieldName || null,
          show_fields: store.state.filter.showFields,
          brief: store.state.filter.brief,
          hide_primitive_route: store.state.filter.hidePrimitiveRoute,
          show_module: store.state.filter.showModule,
        };
        const res = await fetch("dot-search", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          const data = await res.json();
          const tags = Array.isArray(data.tags) ? data.tags : [];
          store.state.leftPanel.tags = tags;
        }
      } catch (err) {
        console.error("dot-search failed", err);
      }
    }

    async function loadInitial() {
      store.state.initializing = true;
      try {
        const res = await fetch("dot");
        const data = await res.json();
        store.state.leftPanel.tags = Array.isArray(data.tags) ? data.tags : [];

        const schemasArr = Array.isArray(data.schemas) ? data.schemas : [];
        // Build dict keyed by id for faster lookups and simpler prop passing
        const schemaMap = Object.fromEntries(schemasArr.map((s) => [s.id, s]));
        store.state.graph.schemaMap = schemaMap;
        store.state.graph.schemaKeys = new Set(Object.keys(schemaMap));
        store.state.graph.routeItems = data.tags
          .map((t) => t.routes)
          .flat()
          .reduce((acc, r) => {
            acc[r.id] = r;
            return acc;
          }, {});
        store.state.modeControl.briefModeEnabled =
          data.enable_brief_mode || false;
        store.state.version = data.version || "";
        store.state.swagger.url = data.swagger_url || null;
        store.state.config.has_er_diagram = data.has_er_diagram || false;
        store.state.config.enable_pydantic_resolve_meta = data.enable_pydantic_resolve_meta || false;

        rebuildSchemaOptions();

        const querySelection = readQuerySelection();
        const restoredFromQuery = applySelectionFromQuery(querySelection);
        if (restoredFromQuery) {
          syncSelectionToUrl();
          onGenerate();
          return;
        } else {
          store.state.config.initial_page_policy = data.initial_page_policy
          renderBasedOnInitialPolicy()
        }

        // default route options placeholder
      } catch (e) {
        console.error("Initial load failed", e);
      } finally {
        store.state.initializing = false;
      }
    }

    async function renderBasedOnInitialPolicy() {
        switch (store.state.config.initial_page_policy) {
          case "full":
            onGenerate();
            return;
          case "empty":
            return;
          case "first":
            store.state.leftPanel.tag =
              store.state.leftPanel.tags.length > 0
                ? store.state.leftPanel.tags[0].name
                : null;
            store.state.leftPanel._tag = store.state.leftPanel.tag;
            syncSelectionToUrl()
            onGenerate();
            return;
        }
    }

    async function onGenerate(resetZoom = true) {
      switch (store.state.mode) {
        case "voyager":
          await renderVoyager(resetZoom);
          break;
        case "er-diagram":
          await renderErDiagram(resetZoom);
          break;
      }
    }

    async function renderVoyager(resetZoom = true) {
      const activeSchema = store.state.search.mode
        ? store.state.search.schemaName
        : null;
      const activeField = store.state.search.mode
        ? store.state.search.fieldName
        : null;
      store.state.generating = true;
      try {
        const payload = {
          tags: store.state.leftPanel.tag ? [store.state.leftPanel.tag] : null,
          schema_name: activeSchema || null,
          schema_field: activeField || null,
          route_name: store.state.leftPanel.routeId || null,
          show_fields: store.state.filter.showFields,
          brief: store.state.filter.brief,
          hide_primitive_route: store.state.filter.hidePrimitiveRoute,
          show_module: store.state.filter.showModule,
          show_pydantic_resolve_meta: store.state.modeControl.pydanticResolveMetaEnabled
        };
        initGraphUI();
        const res = await fetch("dot", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const dotText = await res.text();

        await graphUI.render(dotText, resetZoom);
      } catch (e) {
        console.error("Generate failed", e);
      } finally {
        store.state.generating = false;
      }
    }

    function resetDetailPanels() {
      store.state.rightDrawer.drawer = false;
      store.state.routeDetail.show = false;
      store.state.schemaDetail.schemaCodeName = "";
    }

    async function onReset() {
        store.state.leftPanel.tag = null;
        store.state.leftPanel._tag = null;
        store.state.leftPanel.routeId = null;
        syncSelectionToUrl()
        onGenerate()
    }

    async function togglePydanticResolveMeta(val) {
      store.state.modeControl.pydanticResolveMetaEnabled = val;
      onGenerate();
    }

    async function renderErDiagram(resetZoom = true) {
      initGraphUI();
      erDiagramLoading.value = true;
      const payload = {
        show_fields: store.state.filter.showFields,
        show_module: store.state.filter.showModule,
      };
      try {
        const res = await fetch("er-diagram", { 
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
         });
        if (!res.ok) {
          throw new Error(`failed with status ${res.status}`);
        }
        const dot = await res.text();
        erDiagramCache.value = dot;
        await graphUI.render(dot, resetZoom);
      } catch (err) {
        console.error(err)
      } finally {
        erDiagramLoading.value = false;
      }
    }

    async function onModeChange(val) {
      if (val === "er-diagram") {
        // clear search 
        store.state.search.schemaName = null
        store.state.search.fieldName = null
        store.state.search.invisible = true

        if (store.state.leftPanel.width > 0) {
          store.state.leftPanel.previousWidth = store.state.leftPanel.width;
        }
        store.state.leftPanel.width = 0;
        await renderErDiagram();
      } else {
        store.state.search.invisible = false
        
        const fallbackWidth = store.state.leftPanel.previousWidth || 300;
        store.state.leftPanel.width = fallbackWidth;
        await onGenerate();
      }
    }

    function toggleTag(tagName, expanded = null) {
      if (expanded === true || store.state.search.mode === true) {
        store.state.leftPanel._tag = tagName;
        store.state.leftPanel.tag = tagName;
        store.state.leftPanel.routeId = "";

        store.state.schemaDetail.schemaCodeName = "";
        onGenerate();
      } else {
        store.state.leftPanel._tag = null;
      }

      store.state.rightDrawer.drawer = false;
      store.state.routeDetail.show = false;
      syncSelectionToUrl();
    }

    function selectRoute(routeId) {
      // find belonging tag
      const belongingTag = findTagByRoute(routeId);
      if (belongingTag) {
        store.state.leftPanel.tag = belongingTag;
        store.state.leftPanel._tag = belongingTag;
      }

      if (store.state.leftPanel.routeId === routeId) {
        store.state.leftPanel.routeId = "";
      } else {
        store.state.leftPanel.routeId = routeId;
      }

      store.state.rightDrawer.drawer = false;
      store.state.routeDetail.show = false;
      store.state.schemaDetail.schemaCodeName = "";
      syncSelectionToUrl();
      onGenerate();
    }

    function toggleShowModule(val) {
      store.state.filter.showModule = val;
      onGenerate();
    }

    function toggleShowField(field) {
      store.state.filter.showFields = field;
      onGenerate(false);
    }

    function toggleBrief(val) {
      store.state.filter.brief = val;
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

    watch(
      () => store.state.graph.schemaMap,
      () => {
        rebuildSchemaOptions();
      },
      { deep: false }
    );

    watch(
      () => store.state.leftPanel.width,
      (val) => {
        if (store.state.mode === "voyager" && typeof val === "number" && val > 0) {
          store.state.leftPanel.previousWidth = val;
        }
      }
    );

    watch(
      () => store.state.mode,
      (mode) => {
        onModeChange(mode);
      }
    );

    watch(
      () => store.state.search.schemaName,
      (schemaId) => {
        store.state.search.schemaOptions = allSchemaOptions.value.slice();
        populateFieldOptions(schemaId);
        if (!schemaId) {
          store.state.search.mode = false;
        }
      }
    );

    onMounted(async () => {
      document.body.classList.remove("app-loading");
      await loadInitial();
      // Reveal app content only after initial JS/data is ready
    });

    return {
      store,
      onSearch,
      resetSearch,
      filterSearchSchemas,
      onSearchSchemaChange,
      toggleTag,
      toggleBrief,
      toggleHidePrimitiveRoute,
      selectRoute,
      onGenerate,
      onReset,
      toggleShowField,
      startDragDrawer,
      toggleShowModule,
      onModeChange,
      renderErDiagram,
      togglePydanticResolveMeta
    };
  },
});

app.use(window.Quasar);

// Set Quasar primary theme color to green
if (window.Quasar && typeof window.Quasar.setCssVar === "function") {
  window.Quasar.setCssVar("primary", "#009485");
}

app.component("schema-code-display", SchemaCodeDisplay); // double click to see node details
app.component("route-code-display", RouteCodeDisplay); // double click to see route details
app.component("render-graph", RenderGraph); // for debug, render pasted dot content
app.component("demo-component", Demo);

app.mount("#q-app");
