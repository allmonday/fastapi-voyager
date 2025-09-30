import SchemaFieldFilter from "./component/schema-field-filter.js";
import SchemaCodeDisplay from "./component/schema-code-display.js";
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
      showFields: "object",
      fieldOptions: [
        { label: "No fields", value: "single" },
        { label: "Object fields", value: "object" },
        { label: "All fields", value: "all" },
      ],
      generating: false,
      rawTags: [], // [{ name, routes: [{ id, name }] }]
      rawSchemas: [], // [{ name, fullname }]
      rawSchemasFull: [], // full objects with source_code & fields
  initializing: true,
    });
    const showDetail = ref(false);
    const showSchemaFieldFilter = ref(false);
    const showSchemaCode = ref(false);
    const schemaName = ref(""); // used by detail dialog
    const schemaFieldFilterSchema = ref(null); // external schemaName for schema-field-filter
    const schemaCodeName = ref("");
    function openDetail() {
      showDetail.value = true;
    }
    function closeDetail() {
      showDetail.value = false;
    }

    function applyRoutesForTag(tagName) {
      const tag = state.rawTags.find((t) => t.name === tagName);
      state.routeOptions = [];
      if (tag && Array.isArray(tag.routes)) {
        state.routeOptions.push(
          ...tag.routes.map((r) => ({ label: r.name, value: r.id }))
        );
      }
      state.routeId = "";
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
        const res = await fetch("/dot");
        const data = await res.json();
        state.rawTags = Array.isArray(data.tags) ? data.tags : [];
        state.rawSchemasFull = Array.isArray(data.schemas) ? data.schemas : [];
        state.rawSchemas = state.rawSchemasFull.map((s) => ({
          name: s.name,
          fullname: s.fullname,
        }));

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
        };

        const res = await fetch("/dot", {
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
            if (state.rawSchemas.find((s) => s.fullname === name)) {
              schemaCodeName.value = name;
              showSchemaCode.value = true;
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

    function showDialog() {
      schemaFieldFilterSchema.value = null;
      showSchemaFieldFilter.value = true;
    }

    async function onReset() {
      state.tag = null;
      state.routeId = "";
      state.schemaFullname = null;
      state.showFields = "object";
      await loadInitial();
    }

    // react to tag changes to rebuild routes
    watch(
      () => state.tag,
      (val) => {
        applyRoutesForTag(val);
      }
    );

    onMounted(async () => {
      await loadInitial();
    });

    return {
      state,
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
      schemaCodeName,
    };
  },
});
app.use(window.Quasar);
app.component("schema-field-filter", SchemaFieldFilter);
app.component("schema-code-display", SchemaCodeDisplay);
app.mount("#q-app");
