import SchemaFieldFilter from "./component/schema-field-filter.js";
import SchemaCodeDisplay from "./component/schema-code-display.js";
import RouteCodeDisplay from "./component/route-code-display.js";
import RenderGraph from "./component/render-graph.js";
import { GraphUI } from "./graph-ui.js";
const { createApp, reactive, onMounted, watch, ref } = window.Vue;

const app = createApp({
  setup() {
    const state = reactive({
      // options and selections
      tag: null, // picked tag
      _tag: null, // display tag
      routeId: null, // picked route
      schemaId: null, // picked schema
      showFields: "object",
      fieldOptions: [
        { label: "No field", value: "single" },
        { label: "Object fields", value: "object" },
        { label: "All fields", value: "all" },
      ],
      enableBriefMode: false,
      brief: false,
      focus: false,
      hidePrimitiveRoute: false,
      generating: false,
      swaggerUrl: null,
      rawTags: [], // [{ name, routes: [{ id, name }] }]
      rawSchemas: new Set(), // [{ name, id }]
      rawSchemasFull: {}, // full schemas dict: { [schema.id]: schema }
      initializing: true,
      // Splitter size (left panel width in px)
      splitter: 300,
      detailDrawer: false,
      drawerWidth: 300, // drawer 宽度
      version: "", // version from backend
      showModule: true,
    });

    const showDetail = ref(false);
    const showSchemaFieldFilter = ref(false);
    const showDumpDialog = ref(false);
    const dumpJson = ref("");
    const showImportDialog = ref(false);
    const importJsonText = ref("");
    const showRenderGraph = ref(false);
    const renderCoreData = ref(null);
    const schemaName = ref(""); // used by detail dialog
    const schemaFieldFilterSchema = ref(null); // external schemaName for schema-field-filter
    const schemaCodeName = ref("");
    const routeCodeId = ref("");
    const showRouteDetail = ref(false);
    let graphUI = null;

    function openDetail() {
      showDetail.value = true;
    }
    function closeDetail() {
      showDetail.value = false;
    }

    async function loadInitial() {
      state.initializing = true;
      try {
        const res = await fetch("dot");
        const data = await res.json();
        state.rawTags = Array.isArray(data.tags) ? data.tags : [];
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
        state.enableBriefMode = data.enable_brief_mode || false;
        state.version = data.version || "";
        state.swaggerUrl = data.swagger_url || null

        switch (data.initial_page_policy) {
          case "full":
            onGenerate()
            return
          case "empty":
            return
          case "first":
            state.tag = state.rawTags.length > 0 ? state.rawTags[0].name : null;
            state._tag = state.tag;
            onGenerate();
            return
        }

        // default route options placeholder
      } catch (e) {
        console.error("Initial load failed", e);
      } finally {
        state.initializing = false;
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
      state.generating = true;
      try {
        const payload = {
          tags: state.tag ? [state.tag] : null,
          schema_name: schema_name || null,
          route_name: state.routeId || null,
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
                schemaFieldFilterSchema.value = id;
                showSchemaFieldFilter.value = true;
              }
            },
            onSchemaClick: (id) => {
              resetDetailPanels();
              if (state.rawSchemas.has(id)) {
                schemaCodeName.value = id;
                state.detailDrawer = true;
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
        state.generating = false;
      }
    }

    async function onDumpData() {
      try {
        const payload = {
          tags: state.tag ? [state.tag] : null,
          schema_name: state.schemaId || null,
          route_name: state.routeId || null,
          show_fields: state.showFields,
          brief: state.brief,
        };
        const res = await fetch("dot-core-data", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const json = await res.json();
        dumpJson.value = JSON.stringify(json, null, 2);
        showDumpDialog.value = true;
      } catch (e) {
        console.error("Dump data failed", e);
      }
    }

    async function copyDumpJson() {
      try {
        await navigator.clipboard.writeText(dumpJson.value || "");
        if (window.Quasar?.Notify) {
          window.Quasar.Notify.create({ type: "positive", message: "Copied" });
        }
      } catch (e) {
        console.error("Copy failed", e);
      }
    }

    function openImportDialog() {
      importJsonText.value = "";
      showImportDialog.value = true;
    }

    async function onImportConfirm() {
      let payloadObj = null;
      try {
        payloadObj = JSON.parse(importJsonText.value || "{}");
      } catch (e) {
        if (window.Quasar?.Notify) {
          window.Quasar.Notify.create({
            type: "negative",
            message: "Invalid JSON",
          });
        }
        return;
      }
      // Move the request into RenderGraph component: pass the parsed object and let the component call /dot-render-core-data
      renderCoreData.value = payloadObj;
      showRenderGraph.value = true;
      showImportDialog.value = false;
    }

    function showDialog() {
      schemaFieldFilterSchema.value = null;
      showSchemaFieldFilter.value = true;
    }

    function resetDetailPanels() {
      state.detailDrawer = false;
      showRouteDetail.value = false;
      schemaCodeName.value = "";
    }

    async function onReset() {
      state.tag = null;
      state._tag = null;
      state.routeId = "";
      state.schemaId = null;
      // state.showFields = "object";
      state.focus = false;
      schemaCodeName.value = "";
      onGenerate();
    }

    function toggleTag(tagName, expanded = null) {
      if (expanded === true) {
        state._tag = tagName;
        state.tag = tagName;
        state.routeId = "";
        state.focus = false;
        schemaCodeName.value = "";
        onGenerate();
      } else {
        state._tag = null;
      }

      state.detailDrawer = false;
      showRouteDetail.value = false;
    }

    function selectRoute(routeId) {
      if (state.routeId === routeId) {
        state.routeId = "";
      } else {
        state.routeId = routeId;
      }
      state.detailDrawer = false;
      showRouteDetail.value = false;
      state.focus = false;
      schemaCodeName.value = "";
      onGenerate();
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
      const startWidth = state.drawerWidth;

      function onMouseMove(moveEvent) {
        const deltaX = startX - moveEvent.clientX;
        const newWidth = Math.max(300, Math.min(800, startWidth + deltaX));
        state.drawerWidth = newWidth;
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
      state,
      toggleTag,
      toggleBrief,
      toggleHidePrimitiveRoute,
      selectRoute,
      onGenerate,
      onReset,
      showDetail,
      showRouteDetail,
      openDetail,
      closeDetail,
      schemaName,
      showSchemaFieldFilter,
      schemaFieldFilterSchema,
      showDialog,
      schemaCodeName,
      routeCodeId,
      // dump/import
      showDumpDialog,
      dumpJson,
      copyDumpJson,
      onDumpData,
      showImportDialog,
      importJsonText,
      openImportDialog,
      onImportConfirm,
      // render graph dialog
      showRenderGraph,
      renderCoreData,
      toggleShowField,
      startDragDrawer,
      onFocusChange,
      toggleShowModule
    };
  },
});
app.use(window.Quasar);
// Set Quasar primary theme color to green
if (window.Quasar && typeof window.Quasar.setCssVar === "function") {
  window.Quasar.setCssVar("primary", "#009485");
}
app.component("schema-field-filter", SchemaFieldFilter);
app.component("schema-code-display", SchemaCodeDisplay);
app.component("route-code-display", RouteCodeDisplay);
app.component("render-graph", RenderGraph);
app.mount("#q-app");
