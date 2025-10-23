const { defineComponent, ref, watch, onMounted } = window.Vue;

// Component: RouteCodeDisplay
// Props:
//   routeId: route id key in routeItems
export default defineComponent({
  name: "RouteCodeDisplay",
  props: {
    routeId: { type: String, required: true },
  },
  emits: ["close"],
  setup(props, { emit }) {
    const loading = ref(false);
    const code = ref("");
    const error = ref("");
    const link = ref("");

    function close() {
      emit("close");
    }

    function highlightLater() {
      requestAnimationFrame(() => {
        try {
          if (window.hljs) {
            const block = document.querySelector(
              ".frv-route-code-display pre code.language-python"
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

    async function load() {
      if (!props.routeId) {
        code.value = "";
        return;
      }

      loading.value = true;
      error.value = null;
      code.value = "";
      link.value = "";

      // try to fetch from server: POST /source with { schema_name: routeId }
      const payload = { schema_name: props.routeId };
      try {
        const resp = await fetch(`source`, {
          method: "POST",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        });

        const data = await resp.json().catch(() => ({}));
        if (resp.ok) {
          code.value = data.source_code || "// no source code available";
        } else {
          error.value = (data && data.error) || "Failed to load source";
        }
      } catch (e) {
        error.value = e && e.message ? e.message : "Failed to load source";
      } finally {
        loading.value = false;
      }

      try {
        const resp = await fetch(`vscode-link`, {
          method: "POST",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        });

        const data = await resp.json().catch(() => ({}));
        if (resp.ok) {
          link.value = data.link || "// no source code available";
        } else {
          error.value += (data && data.error) || "Failed to load vscode link";
        }
      } catch (e) {
      } finally {
        loading.value = false;
      }

      if (!error.value) {
        highlightLater();
      }
    }

    watch(
      () => props.routeId,
      () => {
        load();
      }
    );

    onMounted(() => {
      load();
    });

    return { loading, code, error, close, link };
  },
  template: `
  <div class="frv-route-code-display" style="border:1px solid #ccc; position:relative; background:#fff;">
    <q-btn dense flat round icon="close" @click="close" aria-label="Close" style="position:absolute; top:6px; right:6px; z-index:10; background:rgba(255,255,255,0.85)" />
    <div v-if="link" class="q-ml-md q-mt-md" style="padding-top:4px;">
      <a :href="link" target="_blank" rel="noopener" style="font-size:12px; color:#3b82f6;">Open in VSCode</a>
    </div>
    <div style="padding:40px 16px 16px 16px; box-sizing:border-box; overflow:auto;">
      <div v-if="loading" style="font-family:Menlo, monospace; font-size:12px;">Loading source...</div>
      <div v-else-if="error" style="color:#c10015; font-family:Menlo, monospace; font-size:12px;">{{ error }}</div>
      <pre v-else style="margin:0;"><code class="language-python">{{ code }}</code></pre>
    </div>
  </div>`,
});
