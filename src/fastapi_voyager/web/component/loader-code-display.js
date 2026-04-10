const { defineComponent, ref, watch, onMounted } = window.Vue

export default defineComponent({
  name: "LoaderCodeDisplay",
  props: {
    loaderFullname: { type: String, default: null },
    sourceEntity: { type: String, default: null },
    targetEntity: { type: String, default: null },
    label: { type: String, default: null },
  },
  setup(props) {
    const code = ref("")
    const link = ref("")
    const error = ref("")
    const loading = ref(false)

    async function highlightLater() {
      requestAnimationFrame(() => {
        try {
          if (window.hljs) {
            const block = document.querySelector(".frv-loader-display pre code.language-python")
            if (block) {
              if (block.dataset && block.dataset.highlighted) {
                block.removeAttribute("data-highlighted")
              }
              window.hljs.highlightElement(block)
            }
          }
        } catch (e) {
          console.warn("highlight failed", e)
        }
      })
    }

    function resetState() {
      code.value = ""
      link.value = ""
      error.value = null
      loading.value = true
    }

    async function loadSource() {
      if (!props.loaderFullname) return

      resetState()

      const payload = { schema_name: props.loaderFullname }
      try {
        const resp = await fetch(`source`, {
          method: "POST",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        })
        const data = await resp.json().catch(() => ({}))
        if (resp.ok) {
          code.value = data.source_code || "# no source code available"
        } else {
          error.value = (data && data.error) || "Failed to load source"
        }

        const resp2 = await fetch(`vscode-link`, {
          method: "POST",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        })
        const data2 = await resp2.json().catch(() => ({}))
        if (resp2.ok) {
          link.value = data2.link || ""
        }
      } catch (e) {
        error.value = "Failed to load source"
      } finally {
        loading.value = false
        highlightLater()
      }
    }

    watch(
      () => props.loaderFullname,
      () => {
        if (props.loaderFullname) {
          loadSource()
        }
      }
    )

    onMounted(() => {
      if (props.loaderFullname) {
        loadSource()
      }
    })

    function shortName(fullname) {
      if (!fullname) return ""
      const parts = fullname.split(".")
      return parts[parts.length - 1]
    }

    return { code, link, error, loading, shortName }
  },
  template: `
  <div class="frv-loader-display" style="border: 1px solid #ccc; border-left: none; position:relative; height:100%; background:#fff;">
      <div v-show="loading" style="position:absolute; top:0; left:0; right:0; z-index:10;">
        <q-linear-progress indeterminate color="primary" size="2px"/>
      </div>
      <div class="q-ml-lg q-mt-md">
        <p style="font-size: 14px; font-weight: bold;">
          {{ shortName(sourceEntity) }} → {{ shortName(targetEntity) }}
        </p>
        <p v-if="label" style="font-size: 12px; color: #666; margin-top: 2px; white-space: pre-line;">
          {{ label }}
        </p>
        <p style="font-size: 12px; color: #888; margin-top: 4px;">
          {{ loaderFullname }}
        </p>
        <a v-if="link" :href="link" target="_blank" rel="noopener" style="font-size:12px; color:#3b82f6;">
          Open in VSCode
        </a>
      </div>
      <q-separator class="q-mt-sm" />
      <div style="padding:8px 16px 16px 16px; box-sizing:border-box; overflow:auto;">
        <div v-if="error" style="color:#c10015; font-family:Menlo, monospace; font-size:12px;">{{ error }}</div>
        <div v-else>
          <pre style="margin:0;"><code class="language-python">{{ code }}</code></pre>
        </div>
      </div>
  </div>
  `,
})
