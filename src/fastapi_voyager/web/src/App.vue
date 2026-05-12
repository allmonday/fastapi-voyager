<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <n-notification-provider>
      <div style="display: flex; flex-direction: column; height: 100vh">
        <!-- Header / Toolbar -->
        <header
          style="
            border-bottom: 2px solid var(--primary-color);
            background: #fff;
            color: #424242;
            flex-shrink: 0;
          "
        >
          <div
            style="display: flex; align-items: center; height: 52px; padding: 0 8px; width: 100%"
          >
            <div
              style="
                font-size: 18px;
                font-weight: bold;
                display: flex;
                align-items: baseline;
                color: var(--primary-color);
                flex-shrink: 0;
              "
            >
              <n-icon size="20" style="margin-right: 8px"><RocketOutline /></n-icon>
              <span>{{ store.state.framework_name }} Voyager</span>
              <span
                v-if="store.state.version"
                style="font-size: 12px; margin-left: 8px; font-weight: normal"
                >{{ store.state.version }}</span
              >
            </div>
            <div style="flex-shrink: 0">
              <n-button
                size="small"
                quaternary
                @click="onReset"
                title="clear tag, route selection"
                style="margin-left: 80px"
              >
                <template #icon
                  ><n-icon><ExpandOutline /></n-icon
                ></template>
              </n-button>
            </div>
            <div style="font-size: 16px; flex-shrink: 0">
              <n-radio-group
                v-model:value="store.state.filter.showFields"
                @update:value="(val) => toggleShowField(val)"
                size="small"
              >
                <n-radio-button
                  v-for="opt in store.state.fieldOptions"
                  :key="opt.value"
                  :value="opt.value"
                  :label="opt.label"
                />
              </n-radio-group>
            </div>
            <div style="flex: 1"></div>
            <div style="display: flex; align-items: center; gap: 8px; flex-shrink: 0">
              <n-select
                v-show="!store.state.search.invisible"
                v-model:value="store.state.search.schemaName"
                :options="store.state.search.schemaOptions"
                filterable
                clearable
                placeholder="Select schema"
                style="min-width: 320px"
                size="small"
                @update:value="onSearchSchemaChange"
                @clear="resetSearch"
              />
              <n-select
                v-show="!store.state.search.invisible"
                v-model:value="store.state.search.fieldName"
                :options="store.state.search.fieldOptions"
                :disabled="
                  !store.state.search.schemaName || store.state.search.fieldOptions.length === 0
                "
                clearable
                placeholder="Select field (optional)"
                style="min-width: 180px"
                size="small"
                @update:value="onSearch"
              />
            </div>
            <div v-if="store.state.config.has_er_diagram" style="flex-shrink: 0; margin-left: 16px">
              <n-button-group size="small">
                <n-button
                  :type="store.state.mode === 'voyager' ? 'primary' : 'default'"
                  @click="store.state.mode = 'voyager'"
                  >Voyager</n-button
                >
                <n-button
                  :type="store.state.mode === 'er-diagram' ? 'primary' : 'default'"
                  @click="store.state.mode = 'er-diagram'"
                  >ER diagram</n-button
                >
              </n-button-group>
            </div>
            <div style="flex-shrink: 0">
              <n-tooltip trigger="hover">
                <template #trigger>
                  <n-button
                    size="small"
                    quaternary
                    circle
                    style="margin-right: 50px; margin-left: 20px"
                  >
                    <template #icon
                      ><n-icon><HelpCircleOutline /></n-icon
                    ></template>
                  </n-button>
                </template>
                <div style="text-align: left; line-height: 1.4; font-size: 14px">
                  <ul style="margin: 0; padding-left: 20px">
                    <li>scroll to zoom in/out</li>
                    <li>double click node to view details.</li>
                    <li>shift + click to search the schema and highlight related nodes.</li>
                    <li>hold <strong>Space</strong> to activate magnifying glass.</li>
                  </ul>
                </div>
              </n-tooltip>
              <a
                href="https://github.com/allmonday/fastapi-voyager"
                target="_blank"
                class="github-corner"
                aria-label="View source on GitHub"
              >
                <svg
                  width="52"
                  height="52"
                  viewBox="0 0 250 250"
                  :style="`fill:${themeColor}; color:#fff; position:absolute; top:0; border:0; right:0;`"
                  aria-hidden="true"
                >
                  <path d="M0,0 L115,115 L130,115 L142,142 L250,250 L250,0 Z" />
                  <path
                    d="M128.3,109.0 C113.8,99.7 119.0,89.6 119.0,89.6 C122.0,82.7 120.5,78.6 120.5,78.6 C119.2,72.0 123.4,76.3 123.4,76.3 C127.3,80.9 125.5,87.3 125.5,87.3 C122.9,97.6 130.6,101.9 134.4,103.2"
                    fill="currentColor"
                    style="transform-origin: 130px 106px"
                    class="octo-arm"
                  />
                  <path
                    d="M115.0,115.0 C114.9,115.1 118.7,116.5 119.8,115.4 L133.7,101.6 C136.9,99.2 139.9,98.4 142.2,98.6 C133.8,88.0 127.5,74.4 143.8,58.0 C148.5,53.4 154.0,51.2 159.7,51.0 C160.3,49.4 163.2,43.6 171.4,40.1 C171.4,40.1 176.1,42.5 178.8,56.2 C183.1,58.6 187.2,61.8 190.9,65.4 C194.5,69.0 197.7,73.2 200.1,77.6 C213.8,80.2 216.3,84.9 216.3,84.9 C212.7,93.1 206.9,96.0 205.4,96.6 C205.1,102.4 203.0,107.8 198.3,112.5 C181.9,128.9 168.3,122.5 157.7,114.1 C157.9,116.9 156.7,120.9 152.7,124.9 L141.0,136.5 C139.8,137.7 141.6,141.9 141.8,141.8 Z"
                    fill="currentColor"
                    class="octo-body"
                  />
                </svg>
              </a>
            </div>
          </div>
        </header>

        <!-- Main content area -->
        <div style="flex: 1; display: flex; overflow: hidden; position: relative">
          <!-- Left panel: Tag Navigator -->
          <div
            id="tag-navigator"
            v-show="store.state.mode === 'voyager' && store.state.leftPanel.width > 0"
            :style="{
              width: store.state.leftPanel.width + 'px',
              borderRight: '1px solid #e0e0e0',
              backgroundColor: '#fff',
              minHeight: 0,
              height: '100%',
              flexShrink: 0,
              overflow: 'hidden',
            }"
          >
            <n-scrollbar style="height: 100%">
              <n-collapse
                v-model:expanded-names="expandedTagNames"
                accordion
                style="padding-top: 16px"
              >
                <n-collapse-item
                  v-for="tag in store.state.leftPanel.tags"
                  :key="tag.name"
                  :name="tag.name"
                >
                  <template #header>
                    <div style="white-space: nowrap; width: 100%">
                      <n-icon size="20" style="vertical-align: top; margin-right: 8px"
                        ><component
                          :is="
                            store.state.leftPanel.tag === tag.name
                              ? FolderOutline
                              : FolderOpenOutline
                          "
                      /></n-icon>
                      <span
                        >{{ tag.name }}
                        <n-tag
                          size="small"
                          round
                          style="position: relative; top: -1px; margin-left: 8px"
                          >{{ tag.routes.length }}</n-tag
                        >
                      </span>
                      <a
                        v-if="store.state.leftPanel._tag === tag.name && store.state.swagger.url"
                        target="_blank"
                        style="margin-left: 8px"
                        :href="store.state.swagger.url + '#/' + tag.name"
                      >
                        <n-icon
                          size="18"
                          style="color: var(--primary-color)"
                          title="open in swagger"
                          ><LinkOutline
                        /></n-icon>
                      </a>
                    </div>
                  </template>
                  <div style="overflow: auto; max-height: 60vh">
                    <div
                      v-for="route in store.state.filter.hidePrimitiveRoute
                        ? tag.routes.filter((r) => !r.is_primitive)
                        : tag.routes || []"
                      :key="route.id"
                      style="
                        display: flex;
                        align-items: center;
                        padding: 4px 8px 4px 24px;
                        cursor: pointer;
                        white-space: nowrap;
                      "
                      :style="{
                        background:
                          store.state.leftPanel.routeId === route.id
                            ? 'rgba(0,148,133,0.08)'
                            : 'transparent',
                        color:
                          store.state.leftPanel.routeId === route.id
                            ? 'var(--primary-color)'
                            : 'inherit',
                        fontWeight: store.state.leftPanel.routeId === route.id ? 'bold' : 'normal',
                      }"
                      @click="selectRoute(route.id)"
                    >
                      <n-icon size="18" style="margin-right: 8px"><CodeWorkingOutline /></n-icon>
                      <span style="flex: 1">{{ route.name }}</span>
                      <a
                        v-if="store.state.leftPanel.routeId === route.id && store.state.swagger.url"
                        target="_blank"
                        style="margin-left: 8px; display: flex; align-items: center"
                        :href="store.state.swagger.url + '#/' + tag.name + '/' + route.unique_id"
                        @click.stop
                      >
                        <n-icon
                          size="18"
                          style="color: var(--primary-color)"
                          title="open in swagger"
                          ><LinkOutline
                        /></n-icon>
                      </a>
                    </div>
                    <div
                      v-if="!tag.routes || tag.routes.length === 0"
                      style="padding: 4px 8px 4px 24px; color: #757575"
                    >
                      No routes
                    </div>
                  </div>
                </n-collapse-item>
              </n-collapse>
            </n-scrollbar>
          </div>

          <!-- Left panel resize handle -->
          <div
            v-show="store.state.mode === 'voyager'"
            @mousedown="startDragLeftPanel"
            style="
              width: 6px;
              cursor: col-resize;
              background: transparent;
              flex-shrink: 0;
              position: relative;
              z-index: 5;
            "
            title="drag to resize"
          ></div>

          <!-- Center: Graph area -->
          <div style="flex: 1; position: relative; overflow: hidden">
            <div id="graph" class="adjust-fit"></div>

            <!-- Floating controls -->
            <div
              style="
                position: absolute;
                left: 8px;
                top: 8px;
                z-index: 10;
                background: rgba(255, 255, 255, 0.85);
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 12px;
                color: #666;
              "
            >
              <div
                style="display: flex; align-items: center; gap: 6px; margin-top: 6px"
                v-if="
                  store.state.modeControl.briefModeEnabled &&
                  store.state.search.mode === false &&
                  store.state.mode === 'voyager'
                "
              >
                <n-switch
                  v-model:value="store.state.filter.brief"
                  size="small"
                  @update:value="(val) => toggleBrief(val)"
                />
                <span>Brief Mode</span>
              </div>
              <div
                style="display: flex; align-items: center; gap: 6px; margin-top: 6px"
                v-if="store.state.search.mode === false && store.state.mode === 'voyager'"
              >
                <n-switch
                  v-model:value="store.state.filter.hidePrimitiveRoute"
                  size="small"
                  @update:value="(val) => toggleHidePrimitiveRoute(val)"
                />
                <span>Hide Primitive</span>
              </div>
              <div style="display: flex; align-items: center; gap: 6px; margin-top: 6px">
                <n-switch
                  v-model:value="store.state.filter.showModule"
                  size="small"
                  @update:value="(val) => toggleShowModule(val)"
                />
                <span>Show Module Cluster</span>
              </div>
              <div
                style="display: flex; align-items: center; gap: 6px; margin-top: 6px"
                v-if="store.state.mode === 'er-diagram'"
              >
                <n-switch
                  v-model:value="store.state.filter.showMethods"
                  size="small"
                  @update:value="(val) => toggleShowMethods(val)"
                />
                <span>Show Methods</span>
              </div>
              <div
                style="display: flex; align-items: center; gap: 6px; margin-top: 6px"
                v-if="
                  store.state.mode === 'voyager' && store.state.config.enable_pydantic_resolve_meta
                "
              >
                <n-switch
                  v-model:value="store.state.modeControl.pydanticResolveMetaEnabled"
                  size="small"
                  @update:value="(val) => togglePydanticResolveMeta(val)"
                />
                <span>Pydantic Resolve Meta</span>
              </div>
              <div style="margin-top: 8px; margin-left: 8px" v-if="store.state.mode === 'voyager'">
                <div style="font-size: 12px; color: #666; margin-bottom: 4px">
                  Magnification: {{ store.state.filter.magnification.toFixed(1) }}x
                </div>
                <n-slider
                  v-model:value="store.state.filter.magnification"
                  :min="2"
                  :max="5"
                  :step="0.5"
                  :marks="{ 2: '2x', 3: '3x', 4: '4x', 5: '5x' }"
                  @update:value="(val) => updateMagnification(val)"
                  style="max-width: 200px"
                />
              </div>
              <div style="margin-top: 8px" v-if="store.state.mode === 'er-diagram'">
                <div style="font-size: 12px; color: #666; margin-bottom: 4px">Edge Length</div>
                <n-button-group size="small">
                  <n-button
                    :type="store.state.filter.edgeMinlen === 3 ? 'primary' : 'default'"
                    @click="updateEdgeMinlen(3)"
                    >Small</n-button
                  >
                  <n-button
                    :type="store.state.filter.edgeMinlen === 7 ? 'primary' : 'default'"
                    @click="updateEdgeMinlen(7)"
                    >Middle</n-button
                  >
                  <n-button
                    :type="store.state.filter.edgeMinlen === 10 ? 'primary' : 'default'"
                    @click="updateEdgeMinlen(10)"
                    >Large</n-button
                  >
                </n-button-group>
              </div>
            </div>

            <!-- Collapse toggle for tag navigator -->
            <div
              v-show="store.state.mode === 'voyager'"
              class="tag-navigator-collapse-btn-right"
              @click="toggleTagNavigatorCollapse"
              :title="
                store.state.leftPanel.collapsed ? 'Expand tag navigator' : 'Collapse tag navigator'
              "
            >
              <n-icon size="18"
                ><component
                  :is="
                    store.state.leftPanel.collapsed ? ChevronForwardOutline : ChevronBackOutline
                  "
              /></n-icon>
            </div>
          </div>
        </div>

        <!-- Right drawer -->
        <n-drawer
          v-model:show="store.state.rightDrawer.drawer"
          :width="store.state.rightDrawer.width"
          placement="right"
          :mask-closable="true"
        >
          <n-drawer-content :native-scrollbar="false" style="padding: 0" :closable="true">
            <div
              @mousedown="startDragDrawer"
              style="
                position: absolute;
                left: -3px;
                top: 0;
                width: 6px;
                height: 100%;
                cursor: col-resize;
                background: transparent;
                z-index: 10;
              "
              title="drag to resize"
            ></div>
            <SchemaCodeDisplay
              v-if="store.state.schemaDetail.schemaCodeName"
              :schema-name="store.state.schemaDetail.schemaCodeName"
              :schemas="
                store.state.mode === 'er-diagram'
                  ? store.state.erDiagramSchemas
                  : store.state.graph.schemaMap
              "
            />
            <LoaderCodeDisplay
              v-else-if="store.state.edgeDetail.loaderFullname"
              :loader-fullname="store.state.edgeDetail.loaderFullname"
              :source-entity="store.state.edgeDetail.sourceEntity"
              :target-entity="store.state.edgeDetail.targetEntity"
              :label="store.state.edgeDetail.label"
            />
          </n-drawer-content>
        </n-drawer>

        <!-- Route detail modal (bottom) -->
        <n-modal
          v-model:show="store.state.routeDetail.show"
          :bordered="true"
          style="width: 1100px; max-width: 1100px; max-height: 40vh; position: fixed; bottom: 0"
        >
          <n-card style="max-height: 40vh" :bordered="true">
            <RouteCodeDisplay
              :route-id="store.state.routeDetail.routeCodeId"
              @close="store.state.routeDetail.show = false"
            />
          </n-card>
        </n-modal>
      </div>
    </n-notification-provider>
  </n-config-provider>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from "vue"
import {
  NConfigProvider,
  NNotificationProvider,
  NDrawer,
  NDrawerContent,
  NButton,
  NButtonGroup,
  NRadioGroup,
  NRadioButton,
  NSelect,
  NSwitch,
  NSlider,
  NTooltip,
  NTag,
  NScrollbar,
  NCollapse,
  NCollapseItem,
  NModal,
  NCard,
  NDivider,
  NIcon,
} from "naive-ui"
import {
  RocketOutline,
  ExpandOutline,
  HelpCircleOutline,
  FolderOutline,
  FolderOpenOutline,
  LinkOutline,
  CodeWorkingOutline,
  ChevronForwardOutline,
  ChevronBackOutline,
} from "@vicons/ionicons5"
import { GraphUI } from "./graph-ui.js"
import { store } from "./store.js"
import SchemaCodeDisplay from "./component/SchemaCodeDisplay.vue"
import RouteCodeDisplay from "./component/RouteCodeDisplay.vue"
import LoaderCodeDisplay from "./component/LoaderCodeDisplay.vue"

const themeColor = window.FRAMEWORK_THEME_COLOR || "#009485"

const themeOverrides = {
  common: {
    primaryColor: themeColor,
    primaryColorHover: themeColor + "cc",
    primaryColorPressed: themeColor + "aa",
  },
}

let graphUI = null
const erDiagramLoading = ref(false)
const erDiagramCache = ref("")

// Initialize toggle states from localStorage
function loadToggleState(key, defaultValue = false) {
  if (typeof window === "undefined") return defaultValue
  try {
    const saved = localStorage.getItem(key)
    return saved !== null ? JSON.parse(saved) : defaultValue
  } catch (e) {
    console.warn(`Failed to load ${key} from localStorage`, e)
    return defaultValue
  }
}

store.state.modeControl.pydanticResolveMetaEnabled = loadToggleState("pydantic_resolve_meta", false)
store.state.filter.hidePrimitiveRoute = loadToggleState("hide_primitive", false)
store.state.filter.brief = loadToggleState("brief_mode", false)
store.state.filter.showModule = loadToggleState("show_module_cluster", false)
store.state.filter.magnification = loadToggleState("magnification", 3.0)
store.state.filter.edgeMinlen = loadToggleState("edge_minlen", 3)
store.state.filter.showMethods = loadToggleState("show_methods", true)

// Expanded tag names for NCollapse
const expandedTagNames = computed({
  get() {
    if (store.state.search.mode) {
      return store.state.leftPanel.tags?.map((t) => t.name) || []
    }
    return store.state.leftPanel._tag ? [store.state.leftPanel._tag] : []
  },
  set(names) {
    if (store.state.search.mode) return
    if (names.length === 0) {
      // Collapsed
      store.state.leftPanel._tag = null
      store.state.rightDrawer.drawer = false
      store.state.routeDetail.show = false
      store.actions.syncSelectionToUrl()
    } else {
      // Expanded a tag (accordion: only one at a time)
      const newTag = names[names.length - 1]
      store.state.leftPanel._tag = newTag
      store.state.leftPanel.tag = newTag
      store.state.leftPanel.routeId = ""
      store.state.schemaDetail.schemaCodeName = ""
      store.state.rightDrawer.drawer = false
      store.state.routeDetail.show = false
      store.actions.syncSelectionToUrl()
      onGenerate()
    }
  },
})

function initGraphUI() {
  if (graphUI) return
  graphUI = new GraphUI("#graph", {
    onSchemaShiftClick: (id) => {
      if (store.state.graph.schemaKeys.has(id)) {
        store.state.search.mode = true
        store.state.search.schemaName = id
        onSearch()
      }
    },
    onSchemaClick: (id) => {
      store.actions.resetDetailPanels()
      if (store.state.mode === "er-diagram" || store.state.graph.schemaKeys.has(id)) {
        store.state.schemaDetail.schemaCodeName = id
        store.state.rightDrawer.drawer = true
      }
      if (id in store.state.graph.routeItems) {
        store.state.routeDetail.routeCodeId = id
        store.state.routeDetail.show = true
      }
    },
    onEdgeClick: (edgeName, edgeLabel) => {
      const [sourceRaw, targetRaw] = edgeName.split("->")
      const source = sourceRaw.split(":")[0]
      const target = targetRaw.split(":")[0]
      const link = store.state.erDiagramLinks.find(
        (l) => l.source_origin === source && l.target_origin === target
      )
      if (link && link.loader_fullname) {
        store.actions.resetDetailPanels()
        store.state.edgeDetail.loaderFullname = link.loader_fullname
        store.state.edgeDetail.sourceEntity = link.source_origin
        store.state.edgeDetail.targetEntity = link.target_origin
        store.state.edgeDetail.label = link.label
        store.state.rightDrawer.drawer = true
      }
    },
    resetCb: () => {
      store.actions.resetDetailPanels()
    },
    magnifyingGlassMagnification: store.state.filter.magnification,
  })
}

async function resetSearch() {
  const hadPreviousValue = store.actions.resetSearchState()
  if (hadPreviousValue) {
    onGenerate()
  } else {
    store.actions.renderBasedOnInitialPolicy(onGenerate)
  }
}

async function onSearch() {
  if (!store.state.previousTagRoute.hasValue) {
    store.state.previousTagRoute.tag = store.state.leftPanel.tag
    store.state.previousTagRoute.routeId = store.state.leftPanel.routeId
    store.state.previousTagRoute.hasValue = true
  }
  store.state.search.mode = true
  store.state.leftPanel.tag = null
  store.state.leftPanel._tag = null
  store.state.leftPanel.routeId = null
  store.actions.syncSelectionToUrl()
  await store.actions.loadSearchedTags()
  await onGenerate()
}

async function loadInitial() {
  await store.actions.loadInitial(onGenerate, (cb) => store.actions.renderBasedOnInitialPolicy(cb))
}

async function onGenerate(resetZoom = true) {
  switch (store.state.mode) {
    case "voyager":
      await renderVoyager(resetZoom)
      break
    case "er-diagram":
      await renderErDiagram(resetZoom)
      break
  }
}

async function renderVoyager(resetZoom = true) {
  store.state.generating = true
  try {
    const payload = store.actions.buildVoyagerPayload()
    initGraphUI()
    graphUI.setHighlightMode("deep")
    const res = await fetch("dot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    const dotText = await res.text()
    await graphUI.render(dotText, resetZoom)
  } catch (e) {
    console.error("Generate failed", e)
  } finally {
    store.state.generating = false
  }
}

async function renderErDiagram(resetZoom = true) {
  initGraphUI()
  graphUI.setHighlightMode("shallow")
  erDiagramLoading.value = true
  const payload = store.actions.buildErDiagramPayload()
  try {
    const res = await fetch("er-diagram", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
    if (!res.ok) throw new Error(`failed with status ${res.status}`)
    const data = await res.json()
    erDiagramCache.value = data.dot
    store.state.erDiagramLinks = data.links || []
    const schemasArr = Array.isArray(data.schemas) ? data.schemas : []
    store.state.erDiagramSchemas = Object.fromEntries(schemasArr.map((s) => [s.id, s]))
    await graphUI.render(data.dot, resetZoom)
  } catch (err) {
    console.error(err)
  } finally {
    erDiagramLoading.value = false
  }
}

async function onModeChange(val) {
  if (val === "er-diagram") {
    store.state.search.schemaName = null
    store.state.search.fieldName = null
    store.state.search.invisible = true
    if (store.state.leftPanel.width > 0) {
      store.state.leftPanel.previousWidth = store.state.leftPanel.width
    }
    store.state.leftPanel.width = 0
    store.actions.syncSelectionToUrl()
    await renderErDiagram()
  } else {
    store.state.search.invisible = false
    const fallbackWidth = store.state.leftPanel.previousWidth || 300
    store.state.leftPanel.width = fallbackWidth
    store.actions.syncSelectionToUrl()
    await onGenerate()
  }
}

function toggleTagNavigatorCollapse() {
  if (store.state.leftPanel.collapsed) {
    const fallbackWidth = store.state.leftPanel.previousWidth || 300
    store.state.leftPanel.width = fallbackWidth
    store.state.leftPanel.collapsed = false
  } else {
    if (store.state.leftPanel.width > 0) {
      store.state.leftPanel.previousWidth = store.state.leftPanel.width
    }
    store.state.leftPanel.width = 0
    store.state.leftPanel.collapsed = true
  }
}

function selectRoute(routeId) {
  const belongingTag = store.getters.findTagByRoute(routeId)
  if (belongingTag) {
    store.state.leftPanel.tag = belongingTag
    store.state.leftPanel._tag = belongingTag
  }
  if (store.state.leftPanel.routeId === routeId) {
    store.state.leftPanel.routeId = ""
  } else {
    store.state.leftPanel.routeId = routeId
  }
  store.state.rightDrawer.drawer = false
  store.state.routeDetail.show = false
  store.state.schemaDetail.schemaCodeName = ""
  store.actions.syncSelectionToUrl()
  onGenerate()
}

function startDragDrawer(e) {
  const startX = e.clientX
  const startWidth = store.state.rightDrawer.width
  function onMouseMove(moveEvent) {
    const deltaX = startX - moveEvent.clientX
    const newWidth = Math.max(300, Math.min(800, startWidth + deltaX))
    store.state.rightDrawer.width = newWidth
  }
  function onMouseUp() {
    document.removeEventListener("mousemove", onMouseMove)
    document.removeEventListener("mouseup", onMouseUp)
    document.body.style.cursor = ""
    document.body.style.userSelect = ""
  }
  document.addEventListener("mousemove", onMouseMove)
  document.addEventListener("mouseup", onMouseUp)
  document.body.style.cursor = "col-resize"
  document.body.style.userSelect = "none"
  e.preventDefault()
}

function startDragLeftPanel(e) {
  const startX = e.clientX
  const startWidth = store.state.leftPanel.width
  function onMouseMove(moveEvent) {
    const deltaX = moveEvent.clientX - startX
    const newWidth = Math.max(0, Math.min(800, startWidth + deltaX))
    store.state.leftPanel.width = newWidth
  }
  function onMouseUp() {
    document.removeEventListener("mousemove", onMouseMove)
    document.removeEventListener("mouseup", onMouseUp)
    document.body.style.cursor = ""
    document.body.style.userSelect = ""
  }
  document.addEventListener("mousemove", onMouseMove)
  document.addEventListener("mouseup", onMouseUp)
  document.body.style.cursor = "col-resize"
  document.body.style.userSelect = "none"
  e.preventDefault()
}

function onSearchSchemaChange(val) {
  store.actions.onSearchSchemaChange(val, onSearch)
}

function toggleBrief(val) {
  store.actions.toggleBrief(val, onGenerate)
}
function toggleHidePrimitiveRoute(val) {
  store.actions.toggleHidePrimitiveRoute(val, onGenerate)
}
function toggleShowModule(val) {
  store.actions.toggleShowModule(val, onGenerate)
}
function togglePydanticResolveMeta(val) {
  store.actions.togglePydanticResolveMeta(val, onGenerate)
}
function toggleShowField(field) {
  store.actions.toggleShowField(field, onGenerate)
}
function toggleShowMethods(val) {
  store.actions.toggleShowMethods(val, onGenerate)
}
function updateMagnification(val) {
  store.actions.updateMagnification(val)
  if (graphUI && graphUI.magnifyingGlass) {
    graphUI.magnifyingGlass.magnification = val
  }
}
function updateEdgeMinlen(val) {
  store.actions.updateEdgeMinlen(val, onGenerate)
}

// Watchers
watch(
  () => store.state.graph.schemaMap,
  () => store.actions.rebuildSchemaOptions(),
  { deep: false }
)
watch(
  () => store.state.leftPanel.width,
  (val) => {
    if (store.state.mode === "voyager" && typeof val === "number" && val > 0) {
      store.state.leftPanel.previousWidth = val
    }
  }
)
watch(
  () => store.state.mode,
  (mode) => onModeChange(mode)
)
watch(
  () => store.state.search.schemaName,
  (schemaId) => {
    store.state.search.schemaOptions = store.state.allSchemaOptions.slice()
    store.actions.populateFieldOptions(schemaId)
    if (!schemaId) store.state.search.mode = false
  }
)

onMounted(async () => {
  document.body.classList.remove("app-loading")
  await loadInitial()
  if (store.state.framework_name) {
    document.title = `${store.state.framework_name} Voyager`
  }
  const handleKeyDown = (event) => {
    if (event.key === "Escape" && store.state.search.mode) {
      resetSearch()
    }
  }
  document.addEventListener("keydown", handleKeyDown)
  onUnmounted(() => document.removeEventListener("keydown", handleKeyDown))
})
</script>
