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
      tag: null,
      tagOptions: [], // array of strings
      routeId: null,
      routeOptions: [], // [{ label, value }]
      schemaFullname: null,
      schemaOptions: [], // [{ label, value }]
      routeItems: {}, // { id: { label, value } }
      showFields: "object",
      fieldOptions: [
        { label: "No fields", value: "single" },
        { label: "Object fields", value: "object" },
        { label: "All fields", value: "all" },
      ],
      brief: false,
      generating: false,
      rawTags: [], // [{ name, routes: [{ id, name }] }]
      rawSchemas: [], // [{ name, fullname }]
      rawSchemasFull: [], // full objects with source_code & fields
      initializing: true,
    });
    const showDetail = ref(false);
    const showSchemaFieldFilter = ref(false);
    const showSchemaCode = ref(false);
    const showRouteCode = ref(false);
    // Dump/Import dialogs and rendered graph dialog
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
    function openDetail() {
      showDetail.value = true;
    }
    function closeDetail() {
      showDetail.value = false;
    }

    function onFilterTags(val, update) {
      const normalized = (val || "").toLowerCase();
      update(() => {
        if (!normalized) {
          state.tagOptions = state.rawTags.map((t) => t.name);
          return;
        }
        state.tagOptions = state.rawTags
          .map((t) => t.name)
          .filter((n) => n.toLowerCase().includes(normalized));
      });
    }

    function onFilterSchemas(val, update) {
      const normalized = (val || "").toLowerCase();
      update(() => {
        const makeLabel = (s) => `${s.name} (${s.fullname})`;
        let list = state.rawSchemas.map((s) => ({
          label: makeLabel(s),
          value: s.fullname,
        }));
        if (normalized) {
          list = list.filter((opt) =>
            opt.label.toLowerCase().includes(normalized)
          );
        }
        state.schemaOptions = list;
      });
    }

    async function loadInitial() {
      state.initializing = true;
      try {
        const res = await fetch("dot");
        const data = await res.json();
        state.rawTags = Array.isArray(data.tags) ? data.tags : [];
        state.rawSchemasFull = Array.isArray(data.schemas) ? data.schemas : [];
        state.rawSchemas = state.rawSchemasFull.map((s) => ({
          name: s.name,
          fullname: s.fullname,
        }));
        state.routeItems = data.tags
          .map((t) => t.routes)
          .flat()
          .reduce((acc, r) => {
            acc[r.id] = r;
            return acc;
          }, {});

        state.tagOptions = state.rawTags.map((t) => t.name);
        state.schemaOptions = state.rawSchemas.map((s) => ({
          label: `${s.name} (${s.fullname})`,
          value: s.fullname,
        }));
        // default route options placeholder
        state.routeOptions = [];
      } catch (e) {
        console.error("Initial load failed", e);
      } finally {
        state.initializing = false;
      }
    }

    async function onGenerate() {
      state.generating = true;
      try {
        const payload = {
          tags: state.tag ? [state.tag] : null,
          schema_name: state.schemaFullname || null,
          route_name: state.routeId || null,
          show_fields: state.showFields,
          brief: state.brief,
        };

        const res = await fetch("dot", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const dotText = await res.text();

        // create graph instance once
        const graphUI = new GraphUI("#graph", {
          onSchemaClick: (name) => {
            if (state.rawSchemas.find((s) => s.fullname === name)) {
              schemaFieldFilterSchema.value = name;
              showSchemaFieldFilter.value = true;
            }
          },
          onSchemaAltClick: (name) => {
            // priority: schema full name; else route id
            if (state.rawSchemas.find((s) => s.fullname === name)) {
              schemaCodeName.value = name;
              showSchemaCode.value = true;
              return;
            }
            if (name in state.routeItems) {
              routeCodeId.value = name;
              showRouteCode.value = true;
              return;
            }
          },
        });

        await graphUI.render(dotText);
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
          schema_name: state.schemaFullname || null,
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

    async function onReset() {
      state.tag = null;
      state.routeId = "";
      state.schemaFullname = null;
      state.showFields = "object";
      state.brief = false;
      onGenerate()
      // await loadInitial();
    }

    function toggleTag(tagName, expanded = null) {
      if (expanded === true) {
        state.tag = tagName;
        return;
      }
    }

    function selectRoute(routeId) {
      state.routeId = routeId
      onGenerate()
    }

    // react to tag changes to rebuild routes
    watch(
      () => state.tag,
      (val) => {
        if (!state.initializing) {
          state.routeId = ''
          onGenerate();
        }
      }
    );

    watch(
      () => state.showFields,
      () => {
        if (!state.initializing) {
          onGenerate();
        }
      }
    )

    watch(
      () => state.brief,
      () => {
        if (!state.initializing) {
          onGenerate();
        }
      }
    );

    onMounted(async () => {
      await loadInitial();
    });

    return {
      state,
      toggleTag,
      selectRoute,
      onFilterTags,
      onFilterSchemas,
      onGenerate,
      onReset,
      showDetail,
      openDetail,
      closeDetail,
      schemaName,
      showSchemaFieldFilter,
      schemaFieldFilterSchema,
      showDialog,
      showSchemaCode,
      showRouteCode,
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
    };
  },
});
app.use(window.Quasar);
app.component("schema-field-filter", SchemaFieldFilter);
app.component("schema-code-display", SchemaCodeDisplay);
app.component("route-code-display", RouteCodeDisplay);
app.component("render-graph", RenderGraph);
app.mount("#q-app");
