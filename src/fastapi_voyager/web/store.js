const { reactive } = window.Vue;

const state = reactive({
    item: {
        count: 0
    },

    version: '',
    config: {
        initial_page_policy: 'first'
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
    },

    // api filters
    filter: {
        hidePrimitiveRoute: false,
        showFields: 'object',
        brief: false,
        showModule: true,
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