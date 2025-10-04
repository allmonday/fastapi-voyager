const { defineComponent, ref, watch, onMounted } = window.Vue;

// Component: RouteCodeDisplay
// Props:
//   routeId: route id key in routeItems
//   modelValue: dialog visibility
//   routes: object map { id: { id, name, source_code } }
export default defineComponent({
  name: 'RouteCodeDisplay',
  props: {
    routeId: { type: String, required: true },
    modelValue: { type: Boolean, default: false },
    routes: { type: Object, default: () => ({}) },
  },
  emits: ['close'],
  setup(props, { emit }) {
    const code = ref('');
    const error = ref(null);
    const link = ref('');

    function close() { emit('close'); }

    function highlightLater() {
      requestAnimationFrame(() => {
        try {
          if (window.hljs) {
            const block = document.querySelector('.frv-route-code-display pre code.language-python');
            if (block) {
              window.hljs.highlightElement(block);
            }
          }
        } catch (e) {
          console.warn('highlight failed', e);
        }
      });
    }

    function load() {
      error.value = null;
      if (!props.routeId) { code.value=''; return; }
      const item = props.routes[props.routeId];
      if (item && item.source_code) {
        code.value = item.source_code;
        link.value = item.vscode_link || '';
        highlightLater();
      } else if (item) {
        code.value = '// no source code available';
        link.value = item.vscode_link || '';
      } else {
        error.value = 'Route not found';
        link.value = '';
      }
    }

    watch(() => props.modelValue, (v) => { if (v) load(); });
    watch(() => props.routeId, () => { if (props.modelValue) load(); });

    onMounted(() => { if (props.modelValue) load(); });

    return { code, error, close, link };
  },
  template: `
  <div class="frv-route-code-display" style="border:1px solid #ccc; position:relative; width:50vw; max-width:50vw; height:100%; background:#fff;">
    <q-btn dense flat round icon="close" @click="close" aria-label="Close" style="position:absolute; top:6px; right:6px; z-index:10; background:rgba(255,255,255,0.85)" />
    <div v-if="link" class="q-ml-md q-mt-md" style="padding-top:4px;">
      <a :href="link" target="_blank" rel="noopener" style="font-size:12px; color:#3b82f6;">Open in VSCode</a>
    </div>
    <div style="padding:40px 16px 16px 16px; height:100%; box-sizing:border-box; overflow:auto;">
      <div v-if="error" style="color:#c10015; font-family:Menlo, monospace; font-size:12px;">{{ error }}</div>
      <pre v-else style="margin:0;"><code class="language-python">{{ code }}</code></pre>
    </div>
  </div>`
});
