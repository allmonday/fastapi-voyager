import { GraphUI } from "../graph-ui.js";
const { defineComponent, reactive, ref, onMounted, nextTick, watch } =
  window.Vue;

// SchemaFieldFilter component
// Features:
//  - Fetch initial schemas list (GET /dot) and build schema options
//  - Second selector lists fields of the chosen schema
//  - Query button disabled until a schema is selected
//  - On query: POST /dot with schema_name + optional schema_field; render returned DOT in #graph-schema-field
//  - Uses GraphUI once and re-renders
//  - Emits 'queried' event after successful render (payload: { schemaName, fieldName })
export default defineComponent({
  name: "SchemaFieldFilter",
  props: {
    schemaName: { type: String, default: null }, // external injection triggers auto-query
    schemas: { type: Array, default: () => [] }, // externally provided schemas (state.rawSchemasFull or similar)
  },
  emits: ["queried", "close"],
  setup(props, { emit }) {
    const state = reactive({
      loadingSchemas: false,
      querying: false,
      schemas: [], // [{ name, fullname, fields: [{name,...}] }]
      schemaOptions: [], // [{ label, value }]
      fieldOptions: [], // [ field.name ]
      schemaFullname: null,
      fieldName: null,
      error: null,
      showFields: "object",
      showFieldOptions: [
        { label: "No fields", value: "single" },
        { label: "Object fields", value: "object" },
        { label: "All fields", value: "all" },
      ],
    });

    let graphInstance = null;
    let lastAppliedExternal = null;

    async function loadSchemas() {
      // Refactored: use externally provided props.schemas directly; no network call.
      state.error = null;
      state.schemas = Array.isArray(props.schemas) ? props.schemas : [];
      state.schemaOptions = state.schemas.map((s) => ({
        label: `${s.name} (${s.fullname})`,
        value: s.fullname,
      }));
      // Maintain compatibility: loadingSchemas flag toggled quickly (no async work)
      state.loadingSchemas = false;
    }

    function onFilterSchemas(val, update) {
      const needle = (val || "").toLowerCase();
      update(() => {
        let opts = state.schemas.map((s) => ({
          label: `${s.name} (${s.fullname})`,
          value: s.fullname,
        }));
        if (needle) {
          opts = opts.filter((o) => o.label.toLowerCase().includes(needle));
        }
        state.schemaOptions = opts;
      });
    }

    function onSchemaChange(val) {
      state.schemaFullname = val;
      state.fieldName = null;
      const schema = state.schemas.find((s) => s.fullname === val);
      state.fieldOptions = schema ? schema.fields.map((f) => f.name) : [];
    }

    async function onQuery() {
      if (!state.schemaFullname) return;
      state.querying = true;
      state.error = null;
      try {
        const payload = {
          schema_name: state.schemaFullname,
          schema_field: state.fieldName || null,
          show_fields: state.showFields,
        };
        const res = await fetch("dot", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const dotText = await res.text();
        if (!graphInstance) {
          graphInstance = new GraphUI("#graph-schema-field");
        }
        await graphInstance.render(dotText);
        emit("queried", {
          schemaName: state.schemaFullname,
          fieldName: state.fieldName,
        });
      } catch (e) {
        state.error = "Query failed";
        console.error("SchemaFieldFilter query failed", e);
      } finally {
        state.querying = false;
      }
    }

    function applyExternalSchema(name) {
      if (!name || !state.schemas.length) return;
      if (lastAppliedExternal === name) return; // avoid duplicate
      const schema = state.schemas.find((s) => s.fullname === name);
      if (!schema) return;
      state.schemaFullname = schema.fullname;
      state.fieldOptions = schema.fields.map((f) => f.name);
      state.fieldName = null; // reset field for external injection
      lastAppliedExternal = name;
      // auto query
      onQuery();
    }

    onMounted(async () => {
      await nextTick();
      await loadSchemas();
      if (props.schemaName) {
        applyExternalSchema(props.schemaName);
      }
    });


    function close() {
      emit("close");
    }

    return { state, onSchemaChange, onQuery, close, onFilterSchemas };
  },
  template: `
	<div style="height:100%; position:relative; background:#fff;">
				<div style="position:absolute; top:8px; left:8px; z-index:10; background:rgba(255,255,255,0.95); padding:8px 10px; border-radius:4px; box-shadow:0 1px 3px rgba(0,0,0,0.15);" class="q-gutter-sm row items-center">
			<q-select 
				dense outlined use-input input-debounce="0"
				v-model="state.schemaFullname"
				:options="state.schemaOptions"
				option-label="label"
				option-value="value"
				emit-value 
        map-options
				:loading="state.loadingSchemas"
				style="min-width:220px"
				clearable
				label="Select schema"
				@update:model-value="onSchemaChange"
        @filter="onFilterSchemas"
			/>
			<q-select 
				dense outlined
				v-model="state.fieldName"
				:disable="!state.schemaFullname || state.fieldOptions.length===0"
				:options="state.fieldOptions"
				style="min-width:180px"
				clearable
				label="Select field (optional)"
			/>
					<q-option-group
						v-model="state.showFields"
						:options="state.showFieldOptions"
						type="radio"
						inline
						dense
						color="primary"
						style="min-width:260px"
					/>
			<q-btn 
          class="q-ml-md"
          icon="search"
				  label="Search" 
          outline
				:disable="!state.schemaFullname" 
				:loading="state.querying" 
				@click="onQuery" />
		</div>
				<q-btn
					flat dense round icon="close"
					aria-label="Close"
					@click="close"
					style="position:absolute; top:6px; right:6px; z-index:11; background:rgba(255,255,255,0.85);"
				/>
		<div v-if="state.error" style="position:absolute; top:52px; left:8px; z-index:10; color:#c10015; font-size:12px;">{{ state.error }}</div>
		<div id="graph-schema-field" style="width:100%; height:100%; overflow:auto; background:#fafafa"></div>
	</div>
	`,
});
