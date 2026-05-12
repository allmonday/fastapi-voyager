import { reactive } from "vue"

const state = reactive({
  version: "",
  framework_name: "",
  config: {
    initial_page_policy: "first",
    has_er_diagram: false,
    enable_pydantic_resolve_meta: false,
  },

  mode: "voyager", // voyager / er-diagram

  previousTagRoute: {
    hasValue: false,
    tag: null,
    routeId: null,
  },

  swagger: {
    url: "",
  },

  rightDrawer: {
    drawer: false,
    width: 300,
  },

  fieldOptions: [
    { label: "No field", value: "single" },
    { label: "Object fields", value: "object" },
    { label: "All fields", value: "all" },
  ],

  leftPanel: {
    width: 300,
    previousWidth: 300,
    tags: null,
    fullTagsCache: null,
    tag: null,
    _tag: null,
    routeId: null,
    collapsed: false,
  },

  graph: {
    schemaId: null,
    schemaKeys: new Set(),
    schemaMap: {},
    routeItems: [],
  },

  erDiagramLinks: [],
  erDiagramSchemas: {},

  edgeDetail: {
    loaderFullname: null,
    sourceEntity: null,
    targetEntity: null,
    label: null,
  },

  search: {
    mode: false,
    invisible: false,
    schemaName: null,
    fieldName: null,
    schemaOptions: [],
    fieldOptions: [],
  },

  allSchemaOptions: [],

  routeDetail: {
    show: false,
    routeCodeId: "",
  },

  schemaDetail: {
    show: false,
    schemaCodeName: "",
  },

  searchDialog: {
    show: false,
    schema: null,
  },

  status: {
    generating: false,
    loading: false,
    initializing: true,
  },

  modeControl: {
    focus: false,
    briefModeEnabled: false,
    pydanticResolveMetaEnabled: false,
  },

  filter: {
    hidePrimitiveRoute: false,
    showFields: "object",
    brief: false,
    showModule: false,
    magnification: 3.0,
    edgeMinlen: 3,
    showMethods: true,
  },
})

const getters = {
  findTagByRoute(routeId) {
    return (
      state.leftPanel.tags.find((tag) => (tag.routes || []).some((route) => route.id === routeId))
        ?.name || null
    )
  },
}

const actions = {
  readQuerySelection() {
    if (typeof window === "undefined") {
      return { tag: null, route: null, mode: null }
    }
    const params = new URLSearchParams(window.location.search)
    return {
      tag: params.get("tag") || null,
      route: params.get("route") || null,
      mode: params.get("mode") || null,
    }
  },

  syncSelectionToUrl() {
    if (typeof window === "undefined") {
      return
    }
    const params = new URLSearchParams(window.location.search)
    if (state.leftPanel.tag) {
      params.set("tag", state.leftPanel.tag)
    } else {
      params.delete("tag")
    }
    if (state.leftPanel.routeId) {
      params.set("route", state.leftPanel.routeId)
    } else {
      params.delete("route")
    }
    if (state.mode) {
      params.set("mode", state.mode)
    } else {
      params.delete("mode")
    }
    const hash = window.location.hash || ""
    const search = params.toString()
    const base = window.location.pathname
    const newUrl = search ? `${base}?${search}${hash}` : `${base}${hash}`
    window.history.replaceState({}, "", newUrl)
  },

  applySelectionFromQuery(selection) {
    let applied = false
    if (selection.tag && state.leftPanel.tags.some((tag) => tag.name === selection.tag)) {
      state.leftPanel.tag = selection.tag
      state.leftPanel._tag = selection.tag
      applied = true
    }
    if (selection.route && state.graph.routeItems?.[selection.route]) {
      state.leftPanel.routeId = selection.route
      applied = true
      const inferredTag = getters.findTagByRoute(selection.route)
      if (inferredTag) {
        state.leftPanel.tag = inferredTag
        state.leftPanel._tag = inferredTag
      }
    }
    if (selection.mode === "voyager" || selection.mode === "er-diagram") {
      state.mode = selection.mode
      applied = true
    }
    return applied
  },

  loadFullTags() {
    state.leftPanel.tags = state.leftPanel.fullTagsCache
  },

  populateFieldOptions(schemaId) {
    if (!schemaId) {
      state.search.fieldOptions = []
      state.search.fieldName = null
      return
    }
    const schema = state.graph.schemaMap?.[schemaId]
    if (!schema) {
      state.search.fieldOptions = []
      state.search.fieldName = null
      return
    }
    const fieldNames = Array.isArray(schema.fields) ? schema.fields.map((f) => f.name) : []
    state.search.fieldOptions = fieldNames.map((f) => ({ label: f, value: f }))
    if (!fieldNames.includes(state.search.fieldName)) {
      state.search.fieldName = null
    }
  },

  rebuildSchemaOptions() {
    const dict = state.graph.schemaMap || {}
    const opts = Object.values(dict).map((s) => ({
      label: `${s.name} (${s.id})`,
      value: s.id,
    }))
    state.allSchemaOptions = opts
    state.search.schemaOptions = opts.slice()
    this.populateFieldOptions(state.search.schemaName)
  },

  async loadSearchedTags() {
    try {
      const payload = {
        schema_name: state.search.schemaName,
        schema_field: state.search.fieldName || null,
        show_fields: state.filter.showFields,
        brief: state.filter.brief,
        hide_primitive_route: state.filter.hidePrimitiveRoute,
        show_module: state.filter.showModule,
      }
      const res = await fetch("dot-search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
      if (res.ok) {
        const data = await res.json()
        const tags = Array.isArray(data.tags) ? data.tags : []
        state.leftPanel.tags = tags
      }
    } catch (err) {
      console.error("dot-search failed", err)
    }
  },

  async loadInitial(onGenerate, renderBasedOnInitialPolicy) {
    state.initializing = true
    try {
      const res = await fetch("dot")
      const data = await res.json()
      const tags = Array.isArray(data.tags) ? data.tags : []
      state.leftPanel.tags = tags
      state.leftPanel.fullTagsCache = tags

      const schemasArr = Array.isArray(data.schemas) ? data.schemas : []
      const schemaMap = Object.fromEntries(schemasArr.map((s) => [s.id, s]))
      state.graph.schemaMap = schemaMap
      state.graph.schemaKeys = new Set(Object.keys(schemaMap))
      state.graph.routeItems = data.tags
        .map((t) => t.routes)
        .flat()
        .reduce((acc, r) => {
          acc[r.id] = r
          return acc
        }, {})
      state.modeControl.briefModeEnabled = data.enable_brief_mode || false
      state.version = data.version || ""
      state.swagger.url = data.swagger_url || null
      state.config.has_er_diagram = data.has_er_diagram || false
      state.config.enable_pydantic_resolve_meta = data.enable_pydantic_resolve_meta || false
      state.framework_name = data.framework_name || "API"

      this.rebuildSchemaOptions()

      const querySelection = this.readQuerySelection()
      const restoredFromQuery = this.applySelectionFromQuery(querySelection)
      if (restoredFromQuery) {
        this.syncSelectionToUrl()
        onGenerate()
        return
      } else {
        state.config.initial_page_policy = data.initial_page_policy
        if (
          querySelection.mode &&
          (querySelection.mode === "voyager" || querySelection.mode === "er-diagram")
        ) {
          this.syncSelectionToUrl()
          onGenerate()
          return
        }
        renderBasedOnInitialPolicy(onGenerate)
      }
    } catch (e) {
      console.error("Initial load failed", e)
    } finally {
      state.initializing = false
    }
  },

  onSearchSchemaChange(val, onSearch) {
    state.search.schemaName = val
    state.search.mode = false
    if (!val) {
      return
    }
    onSearch()
  },

  resetDetailPanels() {
    state.rightDrawer.drawer = false
    state.routeDetail.show = false
    state.schemaDetail.schemaCodeName = ""
    state.edgeDetail.loaderFullname = null
    state.edgeDetail.sourceEntity = null
    state.edgeDetail.targetEntity = null
    state.edgeDetail.label = null
  },

  onReset(onGenerate) {
    state.leftPanel.tag = null
    state.leftPanel._tag = null
    state.leftPanel.routeId = null
    this.syncSelectionToUrl()
    onGenerate()
  },

  togglePydanticResolveMeta(val, onGenerate) {
    state.modeControl.pydanticResolveMetaEnabled = val
    try {
      localStorage.setItem("pydantic_resolve_meta", JSON.stringify(val))
    } catch (e) {
      console.warn("Failed to save pydantic_resolve_meta to localStorage", e)
    }
    onGenerate()
  },

  toggleShowModule(val, onGenerate) {
    state.filter.showModule = val
    try {
      localStorage.setItem("show_module_cluster", JSON.stringify(val))
    } catch (e) {
      console.warn("Failed to save show_module_cluster to localStorage", e)
    }
    onGenerate()
  },

  toggleShowField(field, onGenerate) {
    state.filter.showFields = field
    onGenerate(false)
  },

  toggleBrief(val, onGenerate) {
    state.filter.brief = val
    try {
      localStorage.setItem("brief_mode", JSON.stringify(val))
    } catch (e) {
      console.warn("Failed to save brief_mode to localStorage", e)
    }
    onGenerate()
  },

  toggleHidePrimitiveRoute(val, onGenerate) {
    state.filter.hidePrimitiveRoute = val
    try {
      localStorage.setItem("hide_primitive", JSON.stringify(val))
    } catch (e) {
      console.warn("Failed to save hide_primitive to localStorage", e)
    }
    onGenerate(false)
  },

  updateMagnification(val) {
    const validatedValue = Math.max(2, Math.min(5, val))
    state.filter.magnification = validatedValue
    try {
      localStorage.setItem("magnification", JSON.stringify(validatedValue))
    } catch (e) {
      console.warn("Failed to save magnification to localStorage", e)
    }
  },

  updateEdgeMinlen(val, onGenerate) {
    const validatedValue = Math.max(3, Math.min(10, val))
    state.filter.edgeMinlen = validatedValue
    try {
      localStorage.setItem("edge_minlen", JSON.stringify(validatedValue))
    } catch (e) {
      console.warn("Failed to save edge_minlen to localStorage", e)
    }
    onGenerate(true)
  },

  toggleShowMethods(val, onGenerate) {
    state.filter.showMethods = val
    try {
      localStorage.setItem("show_methods", JSON.stringify(val))
    } catch (e) {
      console.warn("Failed to save show_methods to localStorage", e)
    }
    onGenerate(false)
  },

  renderBasedOnInitialPolicy(onGenerate) {
    switch (state.config.initial_page_policy) {
      case "full":
        onGenerate()
        return
      case "empty":
        return
      case "first":
        state.leftPanel.tag = state.leftPanel.tags.length > 0 ? state.leftPanel.tags[0].name : null
        state.leftPanel._tag = state.leftPanel.tag
        this.syncSelectionToUrl()
        onGenerate()
        return
    }
  },

  buildVoyagerPayload() {
    const activeSchema = state.search.mode ? state.search.schemaName : null
    const activeField = state.search.mode ? state.search.fieldName : null
    return {
      tags: state.leftPanel.tag ? [state.leftPanel.tag] : null,
      schema_name: activeSchema || null,
      schema_field: activeField || null,
      route_name: state.leftPanel.routeId || null,
      show_fields: state.filter.showFields,
      brief: state.filter.brief,
      hide_primitive_route: state.filter.hidePrimitiveRoute,
      show_module: state.filter.showModule,
      show_pydantic_resolve_meta: state.modeControl.pydanticResolveMetaEnabled,
    }
  },

  buildErDiagramPayload() {
    return {
      show_fields: state.filter.showFields,
      show_module: state.filter.showModule,
      edge_minlen: state.filter.edgeMinlen,
      show_methods: state.filter.showMethods,
    }
  },

  resetSearchState() {
    state.search.mode = false
    state.search.schemaName = null
    state.search.fieldName = null
    state.search.fieldOptions = []

    const hadPreviousValue = state.previousTagRoute.hasValue

    if (hadPreviousValue) {
      state.leftPanel.tag = state.previousTagRoute.tag
      state.leftPanel._tag = state.previousTagRoute.tag
      state.leftPanel.routeId = state.previousTagRoute.routeId
      state.previousTagRoute.hasValue = false
    } else {
      state.leftPanel.tag = null
      state.leftPanel._tag = null
      state.leftPanel.routeId = null
    }

    this.syncSelectionToUrl()
    this.loadFullTags()

    return hadPreviousValue
  },
}

export const store = {
  state,
  getters,
  actions,
}
