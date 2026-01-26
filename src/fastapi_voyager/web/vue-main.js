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
            // Only save current tag/route if we're not already in search mode
            // This prevents overwriting the saved state with null values
            if (!store.state.previousTagRoute.hasValue && !store.state.search.mode) {
              store.state.previousTagRoute.tag = store.state.leftPanel.tag
              store.state.previousTagRoute.routeId = store.state.leftPanel.routeId
              store.state.previousTagRoute.hasValue = true
            }
            store.state.search.mode = true
            store.state.search.schemaName = id
            onSearch()
          }
        },
        onSchemaClick: (id) => {
          resetDetailPanels()
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
          resetDetailPanels()
        },
      })
    }

    function filterSearchSchemas(val, update) {
      const needle = (val || "").toLowerCase()
      update(() => {
        if (!needle) {
          store.state.search.schemaOptions = store.state.allSchemaOptions.slice()
          return
        }
        store.state.search.schemaOptions = store.state.allSchemaOptions.filter((option) =>
          option.label.toLowerCase().includes(needle)
        )
      })
    }

    function onSearchSchemaChange(val) {
      store.state.search.schemaName = val
      store.state.search.mode = false
      if (!val) {
        // Clearing the select should only run resetSearch via @clear
        return
      }
      onSearch()
    }

    async function resetSearch() {
      store.state.search.mode = false
      const hadPreviousValue = store.state.previousTagRoute.hasValue

      if (hadPreviousValue) {
        store.state.leftPanel.tag = store.state.previousTagRoute.tag
        store.state.leftPanel._tag = store.state.previousTagRoute.tag
        store.state.leftPanel.routeId = store.state.previousTagRoute.routeId
        store.state.previousTagRoute.hasValue = false
      } else {
        store.state.leftPanel.tag = null
        store.state.leftPanel._tag = null
        store.state.leftPanel.routeId = null
      }

      store.actions.syncSelectionToUrl()

      // Load the full tags from cache (not search results) since we're resetting search
      store.actions.loadFullTags()

      // If we restored a previous tag/route, generate with it
      // Otherwise, fall back to initial policy
      if (hadPreviousValue) {
        onGenerate()
      } else {
        renderBasedOnInitialPolicy()
      }
    }

    async function onSearch() {
      store.state.search.mode = true
      store.state.leftPanel.tag = null
      store.state.leftPanel._tag = null
      store.state.leftPanel.routeId = null
      store.actions.syncSelectionToUrl()
      await store.actions.loadSearchedTags()
      await onGenerate()
    }

    async function loadInitial() {
      await store.actions.loadInitial(onGenerate, renderBasedOnInitialPolicy)
    }

    async function renderBasedOnInitialPolicy() {
      switch (store.state.config.initial_page_policy) {
        case "full":
          onGenerate()
          return
        case "empty":
          return
        case "first":
          store.state.leftPanel.tag =
            store.state.leftPanel.tags.length > 0 ? store.state.leftPanel.tags[0].name : null
          store.state.leftPanel._tag = store.state.leftPanel.tag
          store.actions.syncSelectionToUrl()
          onGenerate()
          return
      }
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
      const activeSchema = store.state.search.mode ? store.state.search.schemaName : null
      const activeField = store.state.search.mode ? store.state.search.fieldName : null
      store.state.generating = true
      try {
        const payload = {
          tags: store.state.leftPanel.tag ? [store.state.leftPanel.tag] : null,
          schema_name: activeSchema || null,
          schema_field: activeField || null,
          route_name: store.state.leftPanel.routeId || null,
          show_fields: store.state.filter.showFields,
          brief: store.state.filter.brief,
          hide_primitive_route: store.state.filter.hidePrimitiveRoute,
          show_module: store.state.filter.showModule,
          show_pydantic_resolve_meta: store.state.modeControl.pydanticResolveMetaEnabled,
        }
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

    function resetDetailPanels() {
      store.state.rightDrawer.drawer = false
      store.state.routeDetail.show = false
      store.state.schemaDetail.schemaCodeName = ""
    }

    async function onReset() {
      store.state.leftPanel.tag = null
      store.state.leftPanel._tag = null
      store.state.leftPanel.routeId = null
      store.actions.syncSelectionToUrl()
      onGenerate()
    }

    async function togglePydanticResolveMeta(val) {
      store.state.modeControl.pydanticResolveMetaEnabled = val
      try {
        localStorage.setItem("pydantic_resolve_meta", JSON.stringify(val))
      } catch (e) {
        console.warn("Failed to save pydantic_resolve_meta to localStorage", e)
      }
      onGenerate()
    }

    async function renderErDiagram(resetZoom = true) {
      initGraphUI()
      erDiagramLoading.value = true
      const payload = {
        show_fields: store.state.filter.showFields,
        show_module: store.state.filter.showModule,
      }
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
        await renderErDiagram()
      } else {
        store.state.search.invisible = false

        const fallbackWidth = store.state.leftPanel.previousWidth || 300
        store.state.leftPanel.width = fallbackWidth
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

    function toggleShowModule(val) {
      store.state.filter.showModule = val
      try {
        localStorage.setItem("show_module_cluster", JSON.stringify(val))
      } catch (e) {
        console.warn("Failed to save show_module_cluster to localStorage", e)
      }
      onGenerate()
    }

    function toggleShowField(field) {
      store.state.filter.showFields = field
      onGenerate(false)
    }

    function toggleBrief(val) {
      store.state.filter.brief = val
      try {
        localStorage.setItem("brief_mode", JSON.stringify(val))
      } catch (e) {
        console.warn("Failed to save brief_mode to localStorage", e)
      }
      onGenerate()
    }

    function toggleHidePrimitiveRoute(val) {
      store.state.filter.hidePrimitiveRoute = val
      try {
        localStorage.setItem("hide_primitive", JSON.stringify(val))
      } catch (e) {
        console.warn("Failed to save hide_primitive to localStorage", e)
      }
      onGenerate(false)
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
      filterSearchSchemas,
      onSearchSchemaChange,
      toggleTag,
      toggleTagNavigatorCollapse,
      toggleBrief,
      toggleHidePrimitiveRoute,
      selectRoute,
      onGenerate,
      onReset,
      toggleShowField,
      startDragDrawer,
      toggleShowModule,
      onModeChange,
      renderErDiagram,
      togglePydanticResolveMeta,
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
