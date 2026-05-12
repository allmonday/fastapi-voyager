<template>
  <div class="frv-code-display" style="position: relative; height: 100%; background: #fff">
    <div v-show="loading" style="position: absolute; top: 0; left: 0; right: 0; z-index: 10">
      <n-progress processing :height="2" color="var(--q-primary)" />
    </div>
    <div style="margin-left: 24px; margin-top: 12px">
      <p style="font-size: 16px">{{ schemaName }}</p>
      <a :href="link" target="_blank" rel="noopener" style="font-size: 12px; color: #3b82f6">
        Open in VSCode
      </a>
    </div>

    <div style="padding: 8px 12px 0 12px; box-sizing: border-box">
      <n-tabs v-model:value="tab" type="line" size="small" animated>
        <n-tab-pane name="fields" tab="Fields">
          <table
            style="
              border-collapse: collapse;
              width: 100%;
              min-width: 500px;
              font-size: 12px;
              font-family: Menlo, monospace;
            "
          >
            <thead>
              <tr>
                <th style="text-align: left; border-bottom: 1px solid #ddd; padding: 4px 6px">
                  Field
                </th>
                <th style="text-align: left; border-bottom: 1px solid #ddd; padding: 4px 6px">
                  Type
                </th>
                <th style="text-align: left; border-bottom: 1px solid #ddd; padding: 4px 6px">
                  Description
                </th>
                <th style="text-align: left; border-bottom: 1px solid #ddd; padding: 4px 6px">
                  Inherited
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="f in fields" :key="f.name">
                <td style="padding: 4px 6px; border-bottom: 1px solid #f0f0f0">{{ f.name }}</td>
                <td style="padding: 4px 6px; border-bottom: 1px solid #f0f0f0; white-space: nowrap">
                  {{ f.type_name }}
                </td>
                <td style="padding: 4px 6px; border-bottom: 1px solid #f0f0f0; max-width: 200px">
                  {{ f.desc }}
                </td>
                <td style="padding: 4px 6px; border-bottom: 1px solid #f0f0f0; text-align: left">
                  {{ f.from_base ? "✔︎" : "" }}
                </td>
              </tr>
              <tr v-if="!fields.length">
                <td colspan="3" style="padding: 8px 6px; color: #666; font-style: italic">
                  No fields
                </td>
              </tr>
            </tbody>
          </table>
        </n-tab-pane>
        <n-tab-pane name="source" tab="Source Code">
          <pre style="margin: 0"><code class="language-python">{{ code }}</code></pre>
        </n-tab-pane>
      </n-tabs>
    </div>
    <div
      v-if="error"
      style="color: #c10015; font-family: Menlo, monospace; font-size: 12px; padding: 8px 16px"
    >
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from "vue"
import { NProgress, NTabs, NTabPane } from "naive-ui"

const props = defineProps({
  schemaName: { type: String, required: true },
  schemas: { type: Object, default: () => ({}) },
  modelValue: { type: Boolean, default: true },
})

const code = ref("")
const link = ref("")
const error = ref("")
const fields = ref([])
const tab = ref("fields")
const loading = ref(false)

function highlightLater() {
  requestAnimationFrame(() => {
    try {
      if (window.hljs) {
        const block = document.querySelector(".frv-code-display pre code.language-python")
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
  fields.value = []
  loading.value = true
}

async function loadSource() {
  if (!props.schemaName) return

  error.value = null
  code.value = ""
  link.value = ""
  loading.value = true

  const payload = { schema_name: props.schemaName }
  try {
    const resp = await fetch(`source`, {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    const data = await resp.json().catch(() => ({}))
    if (resp.ok) {
      code.value = data.source_code || "// no source code available"
    } else {
      error.value = (data && data.error) || "Failed to load source"
    }

    const resp2 = await fetch(`vscode-link`, {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    const data2 = await resp2.json().catch(() => ({}))
    if (resp2.ok) {
      link.value = data2.link || ""
    } else {
      error.value = (error.value || "") + ((data2 && data2.error) || "Failed to load source")
    }
  } catch (e) {
    error.value = "Failed to load source"
  } finally {
    loading.value = false
  }

  const schema = props.schemas && props.schemas[props.schemaName]
  fields.value = Array.isArray(schema?.fields) ? schema.fields : []

  if (tab.value === "source") {
    highlightLater()
  }
}

watch(
  () => tab.value,
  (val) => {
    if (val === "source") highlightLater()
  }
)
watch(
  () => props.schemaName,
  () => {
    resetState()
    loadSource()
  }
)
watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      resetState()
      loadSource()
    }
  }
)
onMounted(() => {
  if (props.modelValue) {
    resetState()
    loadSource()
  }
})
</script>
