export class GraphUI {
  // ====================
  // Constants
  // ====================

  static HIGHLIGHT_COLOR = "#FF8C00"
  static HIGHLIGHT_STROKE_WIDTH = "3.0"

  // ====================
  // Constructor
  // ====================

  constructor(selector = "#graph", options = {}) {
    this.selector = selector
    this.options = options // e.g. { onSchemaClick: (name) => {} }
    this.graphviz = d3.select(this.selector).graphviz().zoom(false)

    this.gv = null
    this.currentSelection = []
    this.magnifyingGlass = null

    // Magnifying glass magnification setting (radius is percentage of viewBox width)
    this._magnification = options.magnifyingGlassMagnification || 3.0

    this._init()
  }

  // ====================
  // Highlight Methods
  // ====================

  _highlight(mode = "bidirectional") {
    let highlightedNodes = $()
    for (const selection of this.currentSelection) {
      const nodes = this._getAffectedNodes(selection.set, mode)
      highlightedNodes = highlightedNodes.add(nodes)
    }
    if (this.gv) {
      this.gv.highlight(highlightedNodes, true)
      this.gv.bringToFront(highlightedNodes)
    }
  }

  _highlightEdgeNodes() {
    let highlightedNodes = $()
    const [up, down, edge] = this.currentSelection
    highlightedNodes = highlightedNodes.add(this._getAffectedNodes(up.set, up.direction))
    highlightedNodes = highlightedNodes.add(this._getAffectedNodes(down.set, down.direction))
    highlightedNodes = highlightedNodes.add(edge.set)
    if (this.gv) {
      this.gv.highlight(highlightedNodes, true)
      this.gv.bringToFront(highlightedNodes)
    }
  }

  _getAffectedNodes($set, mode = "bidirectional") {
    let $result = $().add($set)
    if (mode === "bidirectional" || mode === "downstream") {
      $set.each((i, el) => {
        if (el.className.baseVal === "edge") {
          const edge = $(el).data("name")
          const nodes = this.gv.nodesByName()
          const downStreamNode = edge.split("->")[1]
          if (downStreamNode) {
            $result.push(nodes[downStreamNode])
            $result = $result.add(this.gv.linkedFrom(nodes[downStreamNode], true))
          }
        } else {
          $result = $result.add(this.gv.linkedFrom(el, true))
        }
      })
    }
    if (mode === "bidirectional" || mode === "upstream") {
      $set.each((i, el) => {
        if (el.className.baseVal === "edge") {
          const edge = $(el).data("name")
          const nodes = this.gv.nodesByName()
          const upStreamNode = edge.split("->")[0]
          if (upStreamNode) {
            $result.push(nodes[upStreamNode])
            $result = $result.add(this.gv.linkedTo(nodes[upStreamNode], true))
          }
        } else {
          $result = $result.add(this.gv.linkedTo(el, true))
        }
      })
    }
    return $result
  }

  // ====================
  // Schema Banner Methods
  // ====================

  highlightSchemaBanner(node) {
    const polygons = node.querySelectorAll("polygon")
    const outerFrame = polygons[0]
    const titleBg = polygons[1]

    if (outerFrame) {
      this._saveOriginalAttributes(outerFrame)
      outerFrame.setAttribute("stroke", GraphUI.HIGHLIGHT_COLOR)
      outerFrame.setAttribute("stroke-width", GraphUI.HIGHLIGHT_STROKE_WIDTH)
    }

    if (titleBg) {
      this._saveOriginalAttributes(titleBg)
      titleBg.setAttribute("fill", GraphUI.HIGHLIGHT_COLOR)
      titleBg.setAttribute("stroke", GraphUI.HIGHLIGHT_COLOR)
    }
  }

  clearSchemaBanners() {
    if (this.gv) {
      this.gv.highlight()
    }

    const allPolygons = document.querySelectorAll("polygon[data-original-stroke]")
    allPolygons.forEach((polygon) => {
      polygon.removeAttribute("data-original-stroke")
      polygon.removeAttribute("data-original-stroke-width")
      polygon.removeAttribute("data-original-fill")
    })
  }

  _saveOriginalAttributes(element) {
    if (!element.hasAttribute("data-original-stroke")) {
      element.setAttribute("data-original-stroke", element.getAttribute("stroke") || "")
      element.setAttribute(
        "data-original-stroke-width",
        element.getAttribute("stroke-width") || "1"
      )
      element.setAttribute("data-original-fill", element.getAttribute("fill") || "")
    }
  }

  _applyNodeHighlight(node) {
    const set = $()
    set.push(node)
    const obj = { set, direction: "bidirectional" }

    this.clearSchemaBanners()
    this.currentSelection = [obj]
    this._highlight()

    return obj
  }

  _triggerCallback(callbackName, ...args) {
    const callback = this.options[callbackName]
    if (callback) {
      try {
        callback(...args)
      } catch (e) {
        console.warn(`${callbackName} callback failed`, e)
      }
    }
  }

  // ====================
  // Magnifying Glass Methods
  // ====================

  _initMagnifyingGlass() {
    // Destroy existing magnifier if any
    if (this.magnifyingGlass) {
      this.magnifyingGlass.destroy()
      this.magnifyingGlass = null
    }

    // Only initialize if enabled in options (default: true)
    if (this.options.enableMagnifyingGlass !== false) {
      const svgElement = document.querySelector(`${this.selector} svg`)
      if (svgElement) {
        import("./magnifying-glass.js")
          .then((module) => {
            const { MagnifyingGlass } = module
            this.magnifyingGlass = new MagnifyingGlass(svgElement, {
              magnification: this._magnification,
            })
          })
          .catch((err) => {
            console.warn("Failed to load magnifying glass module:", err)
          })
      }
    }
  }

  // ====================
  // Initialization & Events
  // ====================

  _init() {
    const self = this
    $(this.selector).graphviz({
      shrink: null,
      zoom: false,
      ready: function () {
        self.gv = this

        const nodes = self.gv.nodes()
        const edges = self.gv.edges()

        nodes.off(".graphui")
        edges.off(".graphui")

        nodes.on("dblclick.graphui", function (event) {
          event.stopPropagation()

          self._applyNodeHighlight(this)

          try {
            self.highlightSchemaBanner(this)
          } catch (e) {
            console.log(e)
          }

          self._triggerCallback("onSchemaClick", event.currentTarget.dataset.name)
        })

        edges.on("dblclick.graphui", function (event) {
          const [upStreamNodeRaw, downStreamNodeRaw] = event.currentTarget.dataset.name.split("->")
          // Strip port info (e.g. "ClassA:f.owner_id" -> "ClassA")
          const upStreamNode = upStreamNodeRaw.split(":")[0]
          const downStreamNode = downStreamNodeRaw.split(":")[0]
          const nodes = self.gv.nodesByName()

          const up = $()
          const down = $()
          const edge = $()

          if (nodes[upStreamNode]) up.push(nodes[upStreamNode])
          if (nodes[downStreamNode]) down.push(nodes[downStreamNode])
          edge.push(this)

          self.currentSelection = [
            { set: up, direction: "upstream" },
            { set: down, direction: "downstream" },
            { set: edge, direction: "single" },
          ]

          try {
            self._highlightEdgeNodes()
          } catch (e) {
            console.warn("[edge-click] highlight error:", e)
          }

          self._triggerCallback("onEdgeClick", event.currentTarget.dataset.name)
        })

        nodes.on("click.graphui", function (event) {
          if (event.shiftKey) {
            self._triggerCallback("onSchemaShiftClick", event.currentTarget.dataset.name)
          } else {
            self._applyNodeHighlight(this)
          }
        })

        $(document)
          .off("click.graphui")
          .on("click.graphui", function (evt) {
            const graphContainer = $(self.selector)[0]
            if (!graphContainer || !evt.target || !graphContainer.contains(evt.target)) {
              return
            }

            const $everything = self.gv.$nodes.add(self.gv.$edges).add(self.gv.$clusters)
            // Walk up from click target to find if it's inside a node/edge/cluster
            let el = evt.target
            let isNode = false
            while (el && el !== graphContainer) {
              if ($everything.is(el)) {
                isNode = true
                break
              }
              el = el.parentNode
            }

            if (!isNode && self.gv) {
              self.clearSchemaBanners()

              if (self.options.resetCb) {
                self.options.resetCb()
              }
            }
          })
      },
    })
  }

  // ====================
  // Render Method
  // ====================

  async render(dotSrc, resetZoom = true) {
    const height = this.options.height || "100%"
    return new Promise((resolve, reject) => {
      try {
        this.graphviz
          .engine("dot")
          .tweenPaths(false)
          .tweenShapes(false)
          .zoomScaleExtent([0, Infinity])
          .zoom(true)
          .width("100%")
          .height(height)
          .fit(true)
          .renderDot(dotSrc)
          .on("end", () => {
            $(this.selector).data("graphviz.svg").setup()
            if (resetZoom) this.graphviz.resetZoom()

            // Initialize magnifying glass after render
            this._initMagnifyingGlass()

            resolve()
          })
      } catch (err) {
        reject(err)
      }
    })
  }
}
