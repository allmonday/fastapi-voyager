import { GraphUI } from "../graph-ui.js";
const { defineComponent, ref, onMounted, nextTick } = window.Vue;

export default defineComponent({
	name: "RenderGraph",
	props: {
		coreData: { type: [Object, Array], required: false, default: null },
	},
	emits: ["close"],
	setup(props, { emit }) {
		const containerId = `graph-render-${Math.random().toString(36).slice(2, 9)}`;
		const hasRendered = ref(false);
		const loading = ref(false);
		let graphInstance = null;

		async function ensureGraph() {
			await nextTick();
			if (!graphInstance) {
				graphInstance = new GraphUI(`#${containerId}`);
			}
		}

		async function renderFromDot(dotText) {
			if (!dotText) return;
			await ensureGraph();
			await graphInstance.render(dotText);
			hasRendered.value = true;
		}

		async function renderFromCoreData() {
			if (!props.coreData) return;
			loading.value = true;
			try {
				const res = await fetch("dot-render-core-data", {
					method: "POST",
					headers: { "Content-Type": "application/json" },
					body: JSON.stringify(props.coreData),
				});
				const dotText = await res.text();
				await renderFromDot(dotText);
				if (window.Quasar?.Notify) {
					window.Quasar.Notify.create({ type: "positive", message: "Rendered" });
				}
			} catch (e) {
				console.error("Render from core data failed", e);
				if (window.Quasar?.Notify) {
					window.Quasar.Notify.create({ type: "negative", message: "Render failed" });
				}
			} finally {
				loading.value = false;
			}
		}

		async function reload() {
			await renderFromCoreData();
		}

		onMounted(async () => {
			await reload();
		});

		function close() {
			emit("close");
		}

		return { containerId, close, hasRendered, reload, loading };
	},
	template: `
		<div style="height:100%; position:relative; background:#fff;">
			<q-btn
				flat dense round icon="close"
				aria-label="Close"
				@click="close"
				style="position:absolute; top:6px; right:6px; z-index:11; background:rgba(255,255,255,0.85);"
			/>
			<q-btn
				flat dense round icon="refresh"
				aria-label="Reload"
				:loading="loading"
				@click="reload"
				style="position:absolute; top:6px; right:46px; z-index:11; background:rgba(255,255,255,0.85);"
			/>
			<div :id="containerId" style="width:100%; height:100%; overflow:auto; background:#fafafa"></div>
		</div>
	`,
});

