const { reactive } = window.Vue;

const state = reactive({
    item: {
        count: 0
    },

    version: '',
    config: {
        initial_page_policy: 'first',
        has_er_diagram: false,
        enable_pydantic_resolve_meta: false,
    },

    mode: 'voyager', // voyager / er-diagram
    
    previousTagRoute: {  // for shift + click, store previous tag/route, and populate back when needed
        hasValue: false,
        tag: null,
        routeId: null
    },

    swagger: {
        url: ''
    },

    rightDrawer: {
        drawer: false,
        width: 300
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
        tag: null,
        _tag: null,
        routeId: null,
    },

    graph: {
        schemaId: null,
        schemaKeys: new Set(),
        schemaMap: {},
        routeItems: []
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
        routeCodeId: ''
    },

    // schema information
    schemaDetail: {  
        show: false,
        schemaCodeName: '',
    },

    searchDialog: {
        show: false,
        schema: null
    },

    // global status
    status: {  
        generating: false,
        loading: false,
        initializing: true,
    },

    // brief, hide primitive ...
    modeControl: {  
        focus: false,  // control the schema param
        briefModeEnabled: false,  // show brief mode toggle
        pydanticResolveMetaEnabled: false,  // show pydantic resolve meta toggle
    },

    // api filters
    filter: {
        hidePrimitiveRoute: false,
        showFields: 'object',
        brief: false,
        showModule: false,
    }

})


const mutations = {
    increment() {
        state.item.count += 1
    }
}


export const store = {
    state,
    mutations
}