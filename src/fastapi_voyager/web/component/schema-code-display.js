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
    schemas: { type: Object, default: () => ({}) },
    // visibility from parent (e.g., dialog v-model)
    modelValue: { type: Boolean, default: true },
  },
  setup(props, { emit }) {
    const code = ref("");
    const link = ref("");
    const error = ref("");
    const fields = ref([]); // schema fields list
    const tab = ref("fields");
    const loading = ref(false);


    async function highlightLater() {
      // wait a tick for DOM update
      requestAnimationFrame(() => {
        try {
          if (window.hljs) {
            const block = document.querySelector(
              ".frv-code-display pre code.language-python"
            );
            if (block) {
              // If already highlighted by highlight.js, remove the flag so it can be highlighted again
              if (block.dataset && block.dataset.highlighted) {
                block.removeAttribute("data-highlighted");
              }
              window.hljs.highlightElement(block);
            }
          }
        } catch (e) {
          console.warn("highlight failed", e);
        }
      });
    }

    function resetState() {
      code.value = "";
      link.value = "";
      error.value = null;
      fields.value = [];
      // tab.value = "fields";
      loading.value = true;
    }

    async function loadSource() {
      if (!props.schemaName) return;

      error.value = null;
      code.value = "";
      link.value = "";
      loading.value = true;

      // try to fetch from server: /source/{schema_name}
      const payload = { schema_name: props.schemaName };
      try {
        // validate input: ensure we have a non-empty schemaName
        const resp = await fetch(`source`, {
          method: "POST",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        });
        // surface server-side validation message for bad request
        const data = await resp.json().catch(() => ({}));
        if (resp.ok) {
          code.value = data.source_code || "// no source code available";
        } else {
          error.value = (data && data.error) || "Failed to load source";
        }

        const resp2 = await fetch(`vscode-link`, {
          method: "POST",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        });
        const data2 = await resp2.json().catch(() => ({}));
        if (resp2.ok) {
          link.value = data2.link || "// no vscode link available";
        } else {
          error.value = (error.value || "") + ((data2 && data2.error) || "Failed to load source");
        }
      } catch (e) {
        error.value = "Failed to load source";
      } finally {
        loading.value = false;
      }

      const schema = props.schemas && props.schemas[props.schemaName];
      fields.value = Array.isArray(schema?.fields) ? schema.fields : [];

      if (tab.value === "source") {
        highlightLater();
      }
    }

    // re-highlight when switching back to source tab
    watch(
      () => tab.value,
      (val) => {
        if (val === "source") {
          highlightLater();
        }
      }
    );

    watch(
      () => props.schemaName,
      () => {
        resetState();
        loadSource();
      },
    );

    // respond to visibility changes: when shown, clear old data and reload
    watch(
      () => props.modelValue,
      (val) => {
        if (val) {
          resetState();
          loadSource();
        }
      }
    );

    onMounted(() => {
      if (props.modelValue) {
        resetState();
        loadSource();
      }
    });

    return { link, code, error, fields, tab, loading };
  },
  template: `
  <div class="frv-code-display" style="border: 1px solid #ccc; border-left: none; position:relative; height:100%; background:#fff;">
      <div v-show="loading" style="position:absolute; top:0; left:0; right:0; z-index:10;">
        <q-linear-progress indeterminate color="primary" size="2px"/>
      </div>
      <div class="q-ml-lg q-mt-md">
        <p style="font-size: 16px;"> {{ schemaName }} </p>
        <a :href="link" target="_blank" rel="noopener" style="font-size:12px; color:#3b82f6;">
          Open in VSCode
        </a>
      </div>

      <div style="padding:8px 12px 0 12px; box-sizing:border-box;">
        <q-tabs v-model="tab" align="left" dense active-color="primary" indicator-color="primary" class="text-grey-8">
          <q-tab name="fields" label="Fields" />
          <q-tab name="source" label="Source Code" />
        </q-tabs>
      </div>
      <q-separator />
      <div style="padding:8px 16px 16px 16px; box-sizing:border-box; overflow:auto;">
        <div v-if="error" style="color:#c10015; font-family:Menlo, monospace; font-size:12px;">{{ error }}</div>
        <template v-else>
          <div v-show="tab === 'fields'">
            <table style="border-collapse:collapse; width:100%; font-size:12px; font-family:Menlo, monospace;">
              <thead>
                <tr>
                  <th style="text-align:left; border-bottom:1px solid #ddd; padding:4px 6px;">Field</th>
                  <th style="text-align:left; border-bottom:1px solid #ddd; padding:4px 6px;">Type</th>
                  <th style="text-align:left; border-bottom:1px solid #ddd; padding:4px 6px;">Description</th>
                  <th style="text-align:left; border-bottom:1px solid #ddd; padding:4px 6px;">Inherited</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="f in fields" :key="f.name">
                  <td style="padding:4px 6px; border-bottom:1px solid #f0f0f0;">{{ f.name }}</td>
                  <td style="padding:4px 6px; border-bottom:1px solid #f0f0f0; white-space:nowrap;">{{ f.type_name }}</td>
                  <td style="padding:4px 6px; border-bottom:1px solid #f0f0f0; max-width: 200px;">{{ f.desc }}</td>
                  <td style="padding:4px 6px; border-bottom:1px solid #f0f0f0; text-align:left;">{{ f.from_base ? '✔︎' : '' }}</td>
                </tr>
                <tr v-if="!fields.length">
                  <td colspan="3" style="padding:8px 6px; color:#666; font-style:italic;">No fields</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-show="tab === 'source'">
            <pre style="margin:0;"><code class="language-python">{{ code }}</code></pre>
          </div>
        </template>
      </div>
	</div>
	`,
});
