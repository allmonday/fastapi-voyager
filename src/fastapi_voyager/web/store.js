const { reactive } = window.Vue

const state = reactive({
  version: "",
  config: {
    initial_page_policy: "first",
    has_er_diagram: false,
    enable_pydantic_resolve_meta: false,
  },

  mode: "voyager", // voyager / er-diagram

  previousTagRoute: {
    // Store the last non-search tag/route selection for restoration when clearing search
    // Used by resetSearch to return to the state before entering search mode
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

  // tags and routes
  leftPanel: {
    width: 300,
    previousWidth: 300,
    tags: null,
    fullTagsCache: null, // Cache for full tags (before search)
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

  // schema options, schema, fields
  search: {
    mode: false,
    invisible: false,
    schemaName: null,
    fieldName: null,
    schemaOptions: [],
    fieldOptions: [],
  },

  // cache all schema options for filtering
  allSchemaOptions: [],

  // route information
  routeDetail: {
    show: false,
    routeCodeId: "",
  },

  // schema information
  schemaDetail: {
    show: false,
    schemaCodeName: "",
  },

  searchDialog: {
    show: false,
    schema: null,
  },

  // global status
  status: {
    generating: false,
    loading: false,
    initializing: true,
  },

  // brief, hide primitive ...
  modeControl: {
    focus: false, // control the schema param
    briefModeEnabled: false, // show brief mode toggle
    pydanticResolveMetaEnabled: false, // show pydantic resolve meta toggle
  },

  // api filters
  filter: {
    hidePrimitiveRoute: false,
    showFields: "object",
    brief: false,
    showModule: false,
  },
})

const getters = {
  /**
   * Find tag name by route ID
   * Used to determine which tag a route belongs to
   */
  findTagByRoute(routeId) {
    return (
      state.leftPanel.tags.find((tag) => (tag.routes || []).some((route) => route.id === routeId))
        ?.name || null
    )
  },
}

const actions = {
  /**
   * Read tag, route and mode from URL query parameters
   * @returns {{ tag: string|null, route: string|null, mode: string|null }}
   */
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

  /**
   * Sync current tag, route and mode selection to URL
   * Updates browser URL without reloading the page
   */
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
    // Always sync mode to URL for consistency
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

  /**
   * Apply selection from URL query parameters to state
   * @param {{ tag: string|null, route: string|null, mode: string|null }} selection
   * @returns {boolean} - true if any selection was applied
   */
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
    // Apply mode from URL if it's valid
    if (selection.mode === "voyager" || selection.mode === "er-diagram") {
      state.mode = selection.mode
      applied = true
    }
    return applied
  },

  /**
   * Restore full tags from cache
   * Used when resetting search mode
   */
  loadFullTags() {
    state.leftPanel.tags = state.leftPanel.fullTagsCache
  },

  /**
   * Populate field options based on selected schema
   * @param {string} schemaId - Schema ID
   */
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
    const fields = Array.isArray(schema.fields) ? schema.fields.map((f) => f.name) : []
    state.search.fieldOptions = fields
    if (!fields.includes(state.search.fieldName)) {
      state.search.fieldName = null
    }
  },

  /**
   * Rebuild schema options from schema map
   * Should be called when schema map changes
   */
  rebuildSchemaOptions() {
    const dict = state.graph.schemaMap || {}
    const opts = Object.values(dict).map((s) => ({
      label: s.name,
      desc: s.id,
      value: s.id,
    }))
    state.allSchemaOptions = opts
    state.search.schemaOptions = opts.slice()
    this.populateFieldOptions(state.search.schemaName)
  },

  /**
   * Load tags based on search criteria
   * @returns {Promise<void>}
   */
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

  /**
   * Load initial data from API
   * @param {Function} onGenerate - Callback to generate graph after load
   * @param {Function} renderBasedOnInitialPolicy - Callback to render based on policy
   * @returns {Promise<void>}
   */
  async loadInitial(onGenerate, renderBasedOnInitialPolicy) {
    state.initializing = true
    try {
      const res = await fetch("dot")
      const data = await res.json()
      const tags = Array.isArray(data.tags) ? data.tags : []
      state.leftPanel.tags = tags
      // Cache the full tags for later use (e.g., resetSearch)
      state.leftPanel.fullTagsCache = tags

      const schemasArr = Array.isArray(data.schemas) ? data.schemas : []
      // Build dict keyed by id for faster lookups and simpler prop passing
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

      this.rebuildSchemaOptions()

      const querySelection = this.readQuerySelection()
      const restoredFromQuery = this.applySelectionFromQuery(querySelection)
      if (restoredFromQuery) {
        this.syncSelectionToUrl()
        onGenerate()
        return
      } else {
        state.config.initial_page_policy = data.initial_page_policy
        // Check if mode was applied from URL even if tag/route wasn't
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

      // default route options placeholder
    } catch (e) {
      console.error("Initial load failed", e)
    } finally {
      state.initializing = false
    }
  },

  /**
   * Filter schema options based on search text
   * Used by Quasar select component's filter function
   * @param {string} val - Search text
   * @param {Function} update - Quasar update callback
   */
  filterSearchSchemas(val, update) {
    const needle = (val || "").toLowerCase()
    update(() => {
      if (!needle) {
        state.search.schemaOptions = state.allSchemaOptions.slice()
        return
      }
      state.search.schemaOptions = state.allSchemaOptions.filter((option) =>
        option.label.toLowerCase().includes(needle)
      )
    })
  },

  /**
   * Handle schema selection change
   * Updates state and triggers search if a schema is selected
   * @param {string} val - Selected schema ID
   * @param {Function} onSearch - Callback to trigger search
   */
  onSearchSchemaChange(val, onSearch) {
    state.search.schemaName = val
    state.search.mode = false
    if (!val) {
      // Clearing the select should only run resetSearch via @clear
      return
    }
    onSearch()
  },

  /**
   * Reset detail panels (right drawer and route detail)
   */
  resetDetailPanels() {
    state.rightDrawer.drawer = false
    state.routeDetail.show = false
    state.schemaDetail.schemaCodeName = ""
  },

  /**
   * Reset left panel selection and regenerate
   * @param {Function} onGenerate - Callback to regenerate graph
   */
  onReset(onGenerate) {
    state.leftPanel.tag = null
    state.leftPanel._tag = null
    state.leftPanel.routeId = null
    this.syncSelectionToUrl()
    onGenerate()
  },

  /**
   * Toggle pydantic resolve meta visibility
   * @param {boolean} val - New value
   * @param {Function} onGenerate - Callback to regenerate graph
   */
  togglePydanticResolveMeta(val, onGenerate) {
    state.modeControl.pydanticResolveMetaEnabled = val
    try {
      localStorage.setItem("pydantic_resolve_meta", JSON.stringify(val))
    } catch (e) {
      console.warn("Failed to save pydantic_resolve_meta to localStorage", e)
    }
    onGenerate()
  },

  /**
   * Toggle show module clustering
   * @param {boolean} val - New value
   * @param {Function} onGenerate - Callback to regenerate graph
   */
  toggleShowModule(val, onGenerate) {
    state.filter.showModule = val
    try {
      localStorage.setItem("show_module_cluster", JSON.stringify(val))
    } catch (e) {
      console.warn("Failed to save show_module_cluster to localStorage", e)
    }
    onGenerate()
  },

  /**
   * Toggle show fields option
   * @param {string} field - Field display option ("single", "object", "all")
   * @param {Function} onGenerate - Callback to regenerate graph
   */
  toggleShowField(field, onGenerate) {
    state.filter.showFields = field
    onGenerate(false)
  },

  /**
   * Toggle brief mode
   * @param {boolean} val - New value
   * @param {Function} onGenerate - Callback to regenerate graph
   */
  toggleBrief(val, onGenerate) {
    state.filter.brief = val
    try {
      localStorage.setItem("brief_mode", JSON.stringify(val))
    } catch (e) {
      console.warn("Failed to save brief_mode to localStorage", e)
    }
    onGenerate()
  },

  /**
   * Toggle hide primitive route
   * @param {boolean} val - New value
   * @param {Function} onGenerate - Callback to regenerate graph
   */
  toggleHidePrimitiveRoute(val, onGenerate) {
    state.filter.hidePrimitiveRoute = val
    try {
      localStorage.setItem("hide_primitive", JSON.stringify(val))
    } catch (e) {
      console.warn("Failed to save hide_primitive to localStorage", e)
    }
    onGenerate(false)
  },

  /**
   * Render based on initial page policy
   * @param {Function} onGenerate - Callback to regenerate graph
   */
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

  /**
   * Build payload for Voyager rendering
   * @returns {Object} Payload for dot API
   */
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

  /**
   * Build payload for ER Diagram rendering
   * @returns {Object} Payload for er-diagram API
   */
  buildErDiagramPayload() {
    return {
      show_fields: state.filter.showFields,
      show_module: state.filter.showModule,
    }
  },

  /**
   * Restore search state and return whether to regenerate
   * @returns {boolean} - true if should regenerate with previous selection
   */
  resetSearchState() {
    state.search.mode = false
    const hadPreviousValue = state.previousTagRoute.hasValue

    if (hadPreviousValue) {
      state.leftPanel.tag = state.previousTagRoute.tag
      state.leftPanel._tag = state.previousTagRoute.tag
      state.leftPanel.routeId = state.previousTagRoute.routeId
      // Clear the saved state
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

const mutations = {}

export const store = {
  state,
  getters,
  actions,
  mutations,
}
