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

    return { loading, link, code, error, close };
  },
  template: `
  <div class="frv-code-display" style="position:relative; width:60vw; max-width:60vw; height:100%; background:#fff;">
			<q-btn dense flat round icon="close" @click="close" aria-label="Close"
				style="position:absolute; top:6px; right:6px; z-index:10; background:rgba(255,255,255,0.85)" />
      <div v-if="link" class="q-ml-md q-mt-md">
        <a :href="link" target="_blank" rel="noopener" style="font-size:12px; color:#3b82f6;">
          Open in VSCode
        </a>
      </div>
      <div style="padding:48px 16px 16px 16px; height:80%; box-sizing:border-box; overflow:auto;">
        <div v-if="loading" style="font-family:Menlo, monospace; font-size:12px;">Loading source...</div>
        <div v-else-if="error" style="color:#c10015; font-family:Menlo, monospace; font-size:12px;">{{ error }}</div>
        <pre v-else style="margin:0;"><code class="language-python">{{ code }}</code></pre>
	  </div>
	</div>
	`,
});
