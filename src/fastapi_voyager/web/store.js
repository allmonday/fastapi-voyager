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
    // for shift + click, store previous tag/route, and populate back when needed
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
   * Read tag and route from URL query parameters
   * @returns {{ tag: string|null, route: string|null }}
   */
  readQuerySelection() {
    if (typeof window === "undefined") {
      return { tag: null, route: null }
    }
    const params = new URLSearchParams(window.location.search)
    return {
      tag: params.get("tag") || null,
      route: params.get("route") || null,
    }
  },

  /**
   * Sync current tag and route selection to URL
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
    const hash = window.location.hash || ""
    const search = params.toString()
    const base = window.location.pathname
    const newUrl = search ? `${base}?${search}${hash}` : `${base}${hash}`
    window.history.replaceState({}, "", newUrl)
  },

  /**
   * Apply selection from URL query parameters to state
   * @param {{ tag: string|null, route: string|null }} selection
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
    return applied
  },
}

const mutations = {}

export const store = {
  state,
  getters,
  actions,
  mutations,
}
