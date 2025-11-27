const { defineComponent, computed } = window.Vue;

import { store } from '../store.js'

export default defineComponent({
  name: "Demo",
  emits: ["close"],
  setup() {
    return { store };
  },
  template: `
    <div>
      <p>Count: {{ store.state.count }}</p>
      <button @click="store.mutations.increment()">Add</button>
    </div>
  `
});
