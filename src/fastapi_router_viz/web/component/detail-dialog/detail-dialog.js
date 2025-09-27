const { defineComponent, onMounted, nextTick } = window.Vue;
import { GraphUI } from "../../graph-ui.js";

const DetailDialog = defineComponent({
  name: "DetailDialog",
  props: {
    modelValue: { type: Boolean, default: false },
    schemaName: { type: String, default: "" },
    showFields: { type: String, default: "" },
  },
  template: `
    <div style="height: 100vh; position: relative; background-color: #fff;">
          <div class="text-body2" style="position: absolute; top: 10px; left: 10px; z-index: 10;">
            Schema: <span class="text-primary">{{ schemaName }}</span> (esc to close)
          </div>
          <div id="graph-container" style="width:100%; overflow:auto; background:#fafafa"></div>
    </div>
  `,
  emits: ["update:modelValue", "close"],
  setup(props, { emit }) {
    let graphInstance = null;

    async function loadGraph() {
      try {
        const payload = {
          tags: null,
          schema_name: props.schemaName,
          route_name: null,
          show_fields: props.showFields,
        };
        console.log(payload);
        const res = await fetch("/dot", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const dotText = await res.text();
        if (!graphInstance) {
          graphInstance = new GraphUI(
            document.getElementById("graph-container")
          );
        }
        await graphInstance.render(dotText);
      } catch (e) {
        console.error("DetailDialog graph load failed", e);
      } finally {
      }
    }
    onMounted(async () => {
      await nextTick();
      loadGraph();
    });

    function close() {
      emit("update:modelValue", false);
      emit("close");
    }
    return { close };
  },
});

export default DetailDialog;
