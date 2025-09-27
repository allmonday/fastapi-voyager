const { defineComponent, ref } = window.Vue;

const DetailDialog = defineComponent({
	name: 'DetailDialog',
	// Inline template (no external script tag needed)
	template: `
		<div>
            <div id="graph-dialog" style="width: 80%; flex: 1 1 auto; overflow: auto"></div>
		</div>
	`,
	props: {
		modelValue: { type: Boolean, default: false },
		disabled: { type: Boolean, default: false }
	},
	emits: ['update:modelValue','close'],
	setup(props, { emit }) {
		const count = ref(0);
		function inc() { count.value += 1; }
		function reset() { count.value = 0; }
		function close() { emit('update:modelValue', false); emit('close'); }
		return { count, inc, reset, close };
	}
});

export default DetailDialog;
