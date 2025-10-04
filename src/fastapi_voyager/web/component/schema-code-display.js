const { defineComponent, ref, watch, onMounted } = window.Vue;

// Component: SchemaCodeDisplay
// Props:
//   schemaName: full qualified schema id (module.Class)
//   modelValue: boolean (dialog visibility from parent)
//   source: optional direct source code (if already resolved client side)
//   schemas: list of schema meta objects (each containing fullname & source_code)
// Behavior:
//   - When dialog opens and schemaName changes, search schemas prop and display its source_code.
//   - No network / global cache side effects.
export default defineComponent({
  name: "SchemaCodeDisplay",
  props: {
    schemaName: { type: String, required: true },
    modelValue: { type: Boolean, default: false },
    source: { type: String, default: null },
    schemas: { type: Array, default: () => [] },
  },
  emits: ["close"],
  setup(props, { emit }) {
    const loading = ref(false);
    const code = ref("");
    const link = ref("");
    const error = ref(null);
    const fields = ref([]); // schema fields list
    const tab = ref('source');

    function close() {
      emit("close");
    }

    function highlightLater() {
      // wait a tick for DOM update
      requestAnimationFrame(() => {
        try {
          if (window.hljs) {
            const block = document.querySelector(
              ".frv-code-display pre code.language-python"
            );
            if (block) {
              window.hljs.highlightElement(block);
            }
          }
        } catch (e) {
          console.warn("highlight failed", e);
        }
      });
    }

    function loadSource() {
      if (!props.schemaName) return;
      if (props.source) {
        code.value = props.source;
        highlightLater();
        return;
      }
      loading.value = true;
      error.value = null;
      try {
        const item = props.schemas.find((s) => s.fullname === props.schemaName);
        if (item) {
          link.value = item.vscode_link || "";
          code.value = item.source_code || "// no source code available";
          // capture fields if provided
          fields.value = Array.isArray(item.fields) ? item.fields : [];
          highlightLater();
        } else {
          error.value = "Schema not found";
        }
      } catch (e) {
        error.value = "Failed to load source";
      } finally {
        loading.value = false;
      }
    }

    // re-highlight when switching back to source tab
    watch(
      () => tab.value,
      (val) => {
        if (val === 'source') {
          highlightLater();
        }
      }
    );

    watch(
      () => props.modelValue,
      (val) => {
        if (val) {
          loadSource();
        }
      }
    );

    onMounted(() => {
      if (props.modelValue) loadSource();
    });

    return { loading, link, code, error, close, fields, tab };
  },
  template: `
  <div class="frv-code-display" style="border: 1px solid #ccc; border-left: none; position:relative; width:40vw; max-width:40vw; height:100%; background:#fff;">
			<q-btn dense flat round icon="close" @click="close" aria-label="Close"
				style="position:absolute; top:6px; right:6px; z-index:10; background:rgba(255,255,255,0.85)" />
      <div v-if="link" class="q-ml-md q-mt-md">
        <a :href="link" target="_blank" rel="noopener" style="font-size:12px; color:#3b82f6;">
          Open in VSCode
        </a>
      </div>

      <div style="padding:8px 12px 0 12px; box-sizing:border-box;">
        <q-tabs v-model="tab" align="left" dense active-color="primary" indicator-color="primary" class="text-grey-8">
          <q-tab name="source" label="Source Code" />
          <q-tab name="fields" label="Fields" />
        </q-tabs>
      </div>
      <q-separator />
      <div style="padding:8px 16px 16px 16px; height:75%; box-sizing:border-box; overflow:auto;">
        <div v-if="loading" style="font-family:Menlo, monospace; font-size:12px;">Loading source...</div>
        <div v-else-if="error" style="color:#c10015; font-family:Menlo, monospace; font-size:12px;">{{ error }}</div>
        <template v-else>
          <div v-show="tab === 'source'">
            <pre style="margin:0;"><code class="language-python">{{ code }}</code></pre>
          </div>
          <div v-show="tab === 'fields'">
            <table style="border-collapse:collapse; width:100%; font-size:12px; font-family:Menlo, monospace;">
              <thead>
                <tr>
                  <th style="text-align:left; border-bottom:1px solid #ddd; padding:4px 6px;">Field</th>
                  <th style="text-align:left; border-bottom:1px solid #ddd; padding:4px 6px;">Type</th>
                  <th style="text-align:left; border-bottom:1px solid #ddd; padding:4px 6px;">From Base</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="f in fields" :key="f.name">
                  <td style="padding:4px 6px; border-bottom:1px solid #f0f0f0;">{{ f.name }}</td>
                  <td style="padding:4px 6px; border-bottom:1px solid #f0f0f0; white-space:nowrap;">{{ f.type_name }}</td>
                  <td style="padding:4px 6px; border-bottom:1px solid #f0f0f0; text-align:left;">{{ f.from_base ? '✔︎' : '' }}</td>
                </tr>
                <tr v-if="!fields.length">
                  <td colspan="3" style="padding:8px 6px; color:#666; font-style:italic;">No fields</td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
      </div>
	</div>
	`,
});
