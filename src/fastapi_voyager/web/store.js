const { reactive, watch, ref } = window.Vue;

const state = reactive({
    count: 0
})

const mutations = {
    increment() {
        state.count += 1
    }
}


export const store = {
    state,
    mutations
}