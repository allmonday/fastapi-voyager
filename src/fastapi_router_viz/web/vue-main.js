import DetailDialog from "./component/detail-dialog/detail-dialog.js";
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
    });
    const showDetail = ref(false);
    const schemaName = ref("");
    function openDetail() {
      showDetail.value = true;
    }
    function closeDetail() {
      showDetail.value = false;
    }

    function applyRoutesForTag(tagName) {
      const tag = state.rawTags.find((t) => t.name === tagName);
      state.routeOptions = [{ label: "-- All routes --", value: "" }];
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
      const res = await fetch("/dot");
      const data = await res.json();
      state.rawTags = Array.isArray(data.tags) ? data.tags : [];
      state.rawSchemas = Array.isArray(data.schemas) ? data.schemas : [];

      state.tagOptions = state.rawTags.map((t) => t.name);
      state.schemaOptions = state.rawSchemas.map((s) => ({
        label: `${s.name} (${s.fullname})`,
        value: s.fullname,
      }));
      // default route options placeholder
      state.routeOptions = [{ label: "-- All routes --", value: "" }];
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
            schemaName.value = name;
            openDetail();
          },
        });
        
        graphUI.render(dotText);
      } catch (e) {
        console.error("Generate failed", e);
      } finally {
        state.generating = false;
      }
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
    };
  },
});
app.use(window.Quasar);
app.component("detail-dialog", DetailDialog);
app.mount("#q-app");
