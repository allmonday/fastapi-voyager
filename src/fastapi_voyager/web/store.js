const { reactive } = window.Vue;

const state = reactive({
    item: {
        count: 0
    },

    version: '',

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
        schemaId: null
    },

    leftPanelFiltered: {

    },

    // schema options, schema, fields
    search: {  
     
    },


    // route information
    routeDetail: {  
        show: false
    },

    // schema information
    schemaDetail: {  
        show: false
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