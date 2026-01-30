import SchemaCodeDisplay from "./component/schema-code-display.js"
import RouteCodeDisplay from "./component/route-code-display.js"
import Demo from "./component/demo.js"
import RenderGraph from "./component/render-graph.js"
import { GraphUI } from "./graph-ui.js"
import { store } from "./store.js"

const { createApp, onMounted, ref, watch } = window.Vue

// Load toggle states from localStorage
function loadToggleState(key, defaultValue = false) {
  if (typeof window === "undefined") return defaultValue
  try {
    const saved = localStorage.getItem(key)
    return saved !== null ? JSON.parse(saved) : defaultValue
  } catch (e) {
    console.warn(`Failed to load ${key} from localStorage`, e)
    return defaultValue
  }
}

const app = createApp({
  setup() {
    let graphUI = null
    const erDiagramLoading = ref(false)
    const erDiagramCache = ref("")

    // Initialize toggle states from localStorage
    store.state.modeControl.pydanticResolveMetaEnabled = loadToggleState(
      "pydantic_resolve_meta",
      false
    )
    store.state.filter.hidePrimitiveRoute = loadToggleState("hide_primitive", false)
    store.state.filter.brief = loadToggleState("brief_mode", false)
    store.state.filter.showModule = loadToggleState("show_module_cluster", false)

    function initGraphUI() {
      if (graphUI) {
        return
      }
      graphUI = new GraphUI("#graph", {
        onSchemaShiftClick: (id) => {
          if (store.state.graph.schemaKeys.has(id)) {
            store.state.search.mode = true
            store.state.search.schemaName = id
            onSearch()
          }
        },
        onSchemaClick: (id) => {
          store.actions.resetDetailPanels()
          if (store.state.graph.schemaKeys.has(id)) {
            store.state.schemaDetail.schemaCodeName = id
            store.state.rightDrawer.drawer = true
          }
          if (id in store.state.graph.routeItems) {
            store.state.routeDetail.routeCodeId = id
            store.state.routeDetail.show = true
          }
        },
        resetCb: () => {
          store.actions.resetDetailPanels()
        },
      })
    }

    async function resetSearch() {
      const hadPreviousValue = store.actions.resetSearchState()

      // If we restored a previous tag/route, generate with it
      // Otherwise, fall back to initial policy
      if (hadPreviousValue) {
        onGenerate()
      } else {
        store.actions.renderBasedOnInitialPolicy(onGenerate)
      }
    }

    async function onSearch() {
      // Save current state before entering search mode (only if not already saved)
      if (!store.state.previousTagRoute.hasValue) {
        store.state.previousTagRoute.tag = store.state.leftPanel.tag
        store.state.previousTagRoute.routeId = store.state.leftPanel.routeId
        store.state.previousTagRoute.hasValue = true
      }

      store.state.search.mode = true
      store.state.leftPanel.tag = null
      store.state.leftPanel._tag = null
      store.state.leftPanel.routeId = null
      store.actions.syncSelectionToUrl()
      await store.actions.loadSearchedTags()
      await onGenerate()
    }

    async function loadInitial() {
      await store.actions.loadInitial(onGenerate, (cb) =>
        store.actions.renderBasedOnInitialPolicy(cb)
      )
    }

    async function onGenerate(resetZoom = true) {
      switch (store.state.mode) {
        case "voyager":
          await renderVoyager(resetZoom)
          break
        case "er-diagram":
          await renderErDiagram(resetZoom)
          break
      }
    }

    async function renderVoyager(resetZoom = true) {
      store.state.generating = true
      try {
        const payload = store.actions.buildVoyagerPayload()
        initGraphUI()
        const res = await fetch("dot", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        })
        const dotText = await res.text()

        await graphUI.render(dotText, resetZoom)
      } catch (e) {
        console.error("Generate failed", e)
      } finally {
        store.state.generating = false
      }
    }

    async function renderErDiagram(resetZoom = true) {
      initGraphUI()
      erDiagramLoading.value = true
      const payload = store.actions.buildErDiagramPayload()
      try {
        const res = await fetch("er-diagram", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        })
        if (!res.ok) {
          throw new Error(`failed with status ${res.status}`)
        }
        const dot = await res.text()
        erDiagramCache.value = dot
        await graphUI.render(dot, resetZoom)
      } catch (err) {
        console.error(err)
      } finally {
        erDiagramLoading.value = false
      }
    }

    async function onModeChange(val) {
      if (val === "er-diagram") {
        // clear search
        store.state.search.schemaName = null
        store.state.search.fieldName = null
        store.state.search.invisible = true

        if (store.state.leftPanel.width > 0) {
          store.state.leftPanel.previousWidth = store.state.leftPanel.width
        }
        store.state.leftPanel.width = 0
        store.actions.syncSelectionToUrl()
        await renderErDiagram()
      } else {
        store.state.search.invisible = false

        const fallbackWidth = store.state.leftPanel.previousWidth || 300
        store.state.leftPanel.width = fallbackWidth
        store.actions.syncSelectionToUrl()
        await onGenerate()
      }
    }

    function toggleTag(tagName, expanded = null) {
      if (expanded === true || store.state.search.mode === true) {
        store.state.leftPanel._tag = tagName
        store.state.leftPanel.tag = tagName
        store.state.leftPanel.routeId = ""

        store.state.schemaDetail.schemaCodeName = ""
        onGenerate()
      } else {
        store.state.leftPanel._tag = null
      }

      store.state.rightDrawer.drawer = false
      store.state.routeDetail.show = false
      store.actions.syncSelectionToUrl()
    }

    function toggleTagNavigatorCollapse() {
      if (store.state.leftPanel.collapsed) {
        // Expand: restore previous width
        const fallbackWidth = store.state.leftPanel.previousWidth || 300
        store.state.leftPanel.width = fallbackWidth
        store.state.leftPanel.collapsed = false
      } else {
        // Collapse: save current width and set to 0
        if (store.state.leftPanel.width > 0) {
          store.state.leftPanel.previousWidth = store.state.leftPanel.width
        }
        store.state.leftPanel.width = 0
        store.state.leftPanel.collapsed = true
      }
    }

    function selectRoute(routeId) {
      // find belonging tag
      const belongingTag = store.getters.findTagByRoute(routeId)
      if (belongingTag) {
        store.state.leftPanel.tag = belongingTag
        store.state.leftPanel._tag = belongingTag
      }

      if (store.state.leftPanel.routeId === routeId) {
        store.state.leftPanel.routeId = ""
      } else {
        store.state.leftPanel.routeId = routeId
      }

      store.state.rightDrawer.drawer = false
      store.state.routeDetail.show = false
      store.state.schemaDetail.schemaCodeName = ""
      store.actions.syncSelectionToUrl()
      onGenerate()
    }

    function startDragDrawer(e) {
      const startX = e.clientX
      const startWidth = store.state.rightDrawer.width

      function onMouseMove(moveEvent) {
        const deltaX = startX - moveEvent.clientX
        const newWidth = Math.max(300, Math.min(800, startWidth + deltaX))
        store.state.rightDrawer.width = newWidth
      }

      function onMouseUp() {
        document.removeEventListener("mousemove", onMouseMove)
        document.removeEventListener("mouseup", onMouseUp)
        document.body.style.cursor = ""
        document.body.style.userSelect = ""
      }

      document.addEventListener("mousemove", onMouseMove)
      document.addEventListener("mouseup", onMouseUp)
      document.body.style.cursor = "col-resize"
      document.body.style.userSelect = "none"
      e.preventDefault()
    }

    watch(
      () => store.state.graph.schemaMap,
      () => {
        store.actions.rebuildSchemaOptions()
      },
      { deep: false }
    )

    watch(
      () => store.state.leftPanel.width,
      (val) => {
        if (store.state.mode === "voyager" && typeof val === "number" && val > 0) {
          store.state.leftPanel.previousWidth = val
        }
      }
    )

    watch(
      () => store.state.mode,
      (mode) => {
        onModeChange(mode)
      }
    )

    watch(
      () => store.state.search.schemaName,
      (schemaId) => {
        store.state.search.schemaOptions = store.state.allSchemaOptions.slice()
        store.actions.populateFieldOptions(schemaId)
        if (!schemaId) {
          store.state.search.mode = false
        }
      }
    )

    onMounted(async () => {
      document.body.classList.remove("app-loading")
      await loadInitial()
      // Reveal app content only after initial JS/data is ready
    })

    return {
      store,
      onSearch,
      resetSearch,
      filterSearchSchemas: (val, update) => store.actions.filterSearchSchemas(val, update),
      onSearchSchemaChange: (val) => store.actions.onSearchSchemaChange(val, onSearch),
      toggleTag,
      toggleTagNavigatorCollapse,
      toggleBrief: (val) => store.actions.toggleBrief(val, onGenerate),
      toggleHidePrimitiveRoute: (val) => store.actions.toggleHidePrimitiveRoute(val, onGenerate),
      selectRoute,
      onGenerate,
      onReset: () => store.actions.onReset(onGenerate),
      toggleShowField: (field) => store.actions.toggleShowField(field, onGenerate),
      startDragDrawer,
      toggleShowModule: (val) => store.actions.toggleShowModule(val, onGenerate),
      onModeChange,
      renderErDiagram,
      togglePydanticResolveMeta: (val) => store.actions.togglePydanticResolveMeta(val, onGenerate),
      resetDetailPanels: () => store.actions.resetDetailPanels(),
    }
  },
})

app.use(window.Quasar)

// Set Quasar primary theme color to green
if (window.Quasar && typeof window.Quasar.setCssVar === "function") {
  window.Quasar.setCssVar("primary", "#009485")
}

app.component("schema-code-display", SchemaCodeDisplay) // double click to see node details
app.component("route-code-display", RouteCodeDisplay) // double click to see route details
app.component("render-graph", RenderGraph) // for debug, render pasted dot content
app.component("demo-component", Demo)

app.mount("#q-app")
