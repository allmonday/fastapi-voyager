import { GraphUI } from "../graph-ui.js";
const { defineComponent, ref, onMounted, watch, nextTick } = window.Vue;

// Simple dialog-embeddable component that renders a DOT graph.
// Props:
//  - dot: String (required) the DOT source to render
// Emits:
//  - close: when the close button is clicked
export default defineComponent({
	name: "RenderGraph",
	props: {
		dot: { type: String, required: true },
	},
	emits: ["close"],
	setup(props, { emit }) {
		const containerId = `graph-render-${Math.random().toString(36).slice(2, 9)}`;
		const hasRendered = ref(false);
		let graphInstance = null;

		async function renderDot() {
			if (!props.dot) return;
			await nextTick();
			if (!graphInstance) {
				graphInstance = new GraphUI(`#${containerId}`);
			}
			await graphInstance.render(props.dot);
			hasRendered.value = true;
		}

		onMounted(async () => {
			await renderDot();
		});

		watch(
			() => props.dot,
			async () => {
				await renderDot();
			}
		);

		function close() {
			emit("close");
		}

		return { containerId, close, hasRendered };
	},
	template: `
		<div style="height:100%; position:relative; background:#fff;">
			<q-btn
				flat dense round icon="close"
				aria-label="Close"
				@click="close"
				style="position:absolute; top:6px; right:6px; z-index:11; background:rgba(255,255,255,0.85);"
			/>
			<div :id="containerId" style="width:100%; height:100%; overflow:auto; background:#fafafa"></div>
		</div>
	`,
});

