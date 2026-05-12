<template>
  <div style="height: 100%; position: relative; background: #fff">
    <n-button
      size="small"
      quaternary
      circle
      aria-label="Close"
      @click="close"
      style="
        position: absolute;
        top: 6px;
        right: 6px;
        z-index: 11;
        background: rgba(255, 255, 255, 0.85);
      "
    >
      <template #icon
        ><n-icon size="18"><CloseOutline /></n-icon
      ></template>
    </n-button>
    <n-button
      size="small"
      quaternary
      circle
      aria-label="Reload"
      :loading="loading"
      @click="reload"
      style="
        position: absolute;
        top: 6px;
        right: 46px;
        z-index: 11;
        background: rgba(255, 255, 255, 0.85);
      "
    >
      <template #icon
        ><n-icon size="18"><RefreshOutline /></n-icon
      ></template>
    </n-button>
    <div
      :id="containerId"
      style="width: 100%; height: 100%; overflow: auto; background: #fafafa"
    ></div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from "vue"
import { NButton, NIcon, createDiscreteApi } from "naive-ui"
import { CloseOutline, RefreshOutline } from "@vicons/ionicons5"
import { GraphUI } from "../graph-ui.js"

const { notification } = createDiscreteApi(["notification"])

const props = defineProps({
  coreData: { type: [Object, Array], required: false, default: null },
})
const emit = defineEmits(["close"])

const containerId = `graph-render-${Math.random().toString(36).slice(2, 9)}`
const hasRendered = ref(false)
const loading = ref(false)
let graphInstance = null

async function ensureGraph() {
  await nextTick()
  if (!graphInstance) {
    graphInstance = new GraphUI(`#${containerId}`)
  }
}

async function renderFromDot(dotText) {
  if (!dotText) return
  await ensureGraph()
  await graphInstance.render(dotText)
  hasRendered.value = true
}

async function renderFromCoreData() {
  if (!props.coreData) return
  loading.value = true
  try {
    const res = await fetch("dot-render-core-data", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(props.coreData),
    })
    const dotText = await res.text()
    await renderFromDot(dotText)
    notification.success({ content: "Rendered" })
  } catch (e) {
    console.error("Render from core data failed", e)
    notification.error({ content: "Render failed" })
  } finally {
    loading.value = false
  }
}

async function reload() {
  await renderFromCoreData()
}

function close() {
  emit("close")
}

onMounted(reload)
</script>
