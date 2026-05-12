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
    this.highlightMode = options.highlightMode || "deep"

    // Magnifying glass magnification setting (radius is percentage of viewBox width)
    this._magnification = options.magnifyingGlassMagnification || 3.0

    // Highlight state snapshot for restoring after re-render
    this._lastHighlight = null // { type: 'node', name } or { type: 'edge', source, target }

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
      this.gv.highlight(highlightedNodes)
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
      this.gv.highlight(highlightedNodes)
      this.gv.bringToFront(highlightedNodes)
    }
  }

  _highlightEdgeOnly(edgeEl, sourceNodeName, targetNodeName) {
    const nodes = this.gv.nodesByName()
    let $set = $()
    $set = $set.add(edgeEl)
    if (nodes[sourceNodeName]) {
      $set = $set.add(nodes[sourceNodeName])
    }
    if (nodes[targetNodeName]) {
      $set = $set.add(nodes[targetNodeName])
    }
    if (this.gv) {
      this.gv.highlight($set)
      this.gv.bringToFront($set)
    }
    // Highlight node banners
    if (nodes[sourceNodeName]) {
      this.highlightSchemaBanner(nodes[sourceNodeName])
    }
    if (nodes[targetNodeName]) {
      this.highlightSchemaBanner(nodes[targetNodeName])
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
    this._lastHighlight = null

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

  _highlightNodeShallow(node) {
    const nodeName = $(node).attr("data-name")
    const nodesByName = this.gv.nodesByName()
    let $set = $().add(node)

    // Find directly connected edges and their neighbor nodes (no recursion)
    for (const edgeName in this.gv._edgesByName) {
      const parts = edgeName.split("->")
      const srcNode = parts[0].split(":")[0]
      const tgtNode = parts[1] ? parts[1].split(":")[0] : null

      if (srcNode === nodeName || tgtNode === nodeName) {
        this.gv._edgesByName[edgeName].forEach((edge) => {
          $set = $set.add(edge)
        })
        if (srcNode === nodeName && tgtNode && nodesByName[tgtNode]) {
          $set = $set.add(nodesByName[tgtNode])
        }
        if (tgtNode === nodeName && nodesByName[srcNode]) {
          $set = $set.add(nodesByName[srcNode])
        }
      }
    }

    this.gv.highlight($set)
    this.gv.bringToFront($set)
    this.highlightSchemaBanner(node)
    this._lastHighlight = { type: "node", name: nodeName }
  }

  _applyNodeHighlight(node) {
    const set = $()
    set.push(node)
    const obj = { set, direction: "bidirectional" }

    this.clearSchemaBanners()
    this.currentSelection = [obj]
    this._highlight()

    this._lastHighlight = { type: "node", name: $(node).attr("data-name") }

    return obj
  }

  setHighlightMode(mode) {
    this.highlightMode = mode
  }

  _restoreHighlight() {
    if (!this._lastHighlight || !this.gv) return

    if (this._lastHighlight.type === "node") {
      const nodes = this.gv.nodesByName()
      const node = nodes[this._lastHighlight.name]
      if (node) {
        if (this.highlightMode === "shallow") {
          this._highlightNodeShallow(node)
        } else {
          this._applyNodeHighlight(node)
          try {
            this.highlightSchemaBanner(node)
          } catch (e) {
            console.warn("[restore-highlight] banner error:", e)
          }
        }
      }
    } else if (this._lastHighlight.type === "edge") {
      const { source, target } = this._lastHighlight
      const edgeName = Object.keys(this.gv._edgesByName).find((name) => {
        const [s, t] = name.split("->")
        return s.split(":")[0] === source && t.split(":")[0] === target
      })
      if (edgeName && this.gv._edgesByName[edgeName]?.[0]) {
        if (this.highlightMode === "shallow") {
          this._highlightEdgeOnly(this.gv._edgesByName[edgeName][0], source, target)
        } else {
          const nodes = this.gv.nodesByName()
          const up = $()
          const down = $()
          const edge = $()
          if (nodes[source]) up.push(nodes[source])
          if (nodes[target]) down.push(nodes[target])
          edge.push(this.gv._edgesByName[edgeName][0])
          this.currentSelection = [
            { set: up, direction: "upstream" },
            { set: down, direction: "downstream" },
            { set: edge, direction: "single" },
          ]
          this._highlightEdgeNodes()
        }
      }
    }
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

          if (self.highlightMode === "shallow") {
            self.clearSchemaBanners()
            self._highlightNodeShallow(this)
          } else {
            self._applyNodeHighlight(this)
            try {
              self.highlightSchemaBanner(this)
            } catch (e) {
              console.log(e)
            }
          }

          self._triggerCallback("onSchemaClick", event.currentTarget.dataset.name)
        })

        edges.on("click.graphui", function (event) {
          event.stopPropagation()
          const [upStreamNodeRaw, downStreamNodeRaw] = event.currentTarget.dataset.name.split("->")
          // Strip port info (e.g. "ClassA:f.owner_id" -> "ClassA")
          const upStreamNode = upStreamNodeRaw.split(":")[0]
          const downStreamNode = downStreamNodeRaw.split(":")[0]

          if (self.highlightMode === "shallow") {
            self.clearSchemaBanners()
            try {
              self._highlightEdgeOnly(this, upStreamNode, downStreamNode)
            } catch (e) {
              console.warn("[edge-click] highlight error:", e)
            }
            self._lastHighlight = { type: "edge", source: upStreamNode, target: downStreamNode }
          } else {
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
            self._lastHighlight = { type: "edge", source: upStreamNode, target: downStreamNode }
          }
        })

        edges.on("dblclick.graphui", function (event) {
          event.stopPropagation()
          self._triggerCallback("onEdgeClick", event.currentTarget.dataset.name)
        })

        nodes.on("click.graphui", function (event) {
          if (event.shiftKey) {
            self._triggerCallback("onSchemaShiftClick", event.currentTarget.dataset.name)
          } else if (self.highlightMode === "shallow") {
            self.clearSchemaBanners()
            self._highlightNodeShallow(this)
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
    // Save current zoom transform before re-render
    let savedTransform = null
    if (!resetZoom) {
      const svgEl = document.querySelector(`${this.selector} svg`)
      if (svgEl) {
        savedTransform = d3.zoomTransform(svgEl)
      }
    }
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
            this._restoreHighlight()
            if (resetZoom) {
              this.graphviz.resetZoom()
            } else if (savedTransform) {
              this.graphviz
                .zoomSelection()
                .call(this.graphviz.zoomBehavior().transform, savedTransform)
            }

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
