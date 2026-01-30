export class GraphUI {
  constructor(selector = "#graph", options = {}) {
    this.selector = selector
    this.options = options // e.g. { onSchemaClick: (name) => {} }
    this.graphviz = d3.select(this.selector).graphviz()

    this.gv = null
    this.currentSelection = []
    this._init()
  }

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

  highlightSchemaBanner(node) {
    // Get all polygons in the node
    const polygons = node.querySelectorAll("polygon")

    // The first polygon is typically the outer frame of the entire node
    const outerFrame = polygons[0]
    // The second polygon is typically the title background
    const titleBg = polygons[1]

    if (outerFrame) {
      // Save original attributes for potential restoration
      if (!outerFrame.hasAttribute("data-original-stroke")) {
        outerFrame.setAttribute("data-original-stroke", outerFrame.getAttribute("stroke") || "")
        outerFrame.setAttribute(
          "data-original-stroke-width",
          outerFrame.getAttribute("stroke-width") || "1"
        )
        outerFrame.setAttribute("data-original-fill", outerFrame.getAttribute("fill") || "")
      }

      // Apply bold purple border to the outer frame
      outerFrame.setAttribute("stroke", "#822dba")
      outerFrame.setAttribute("stroke-width", "3.0")
    }

    if (titleBg) {
      // Save original attributes
      if (!titleBg.hasAttribute("data-original-stroke")) {
        titleBg.setAttribute("data-original-stroke", titleBg.getAttribute("stroke") || "")
        titleBg.setAttribute(
          "data-original-stroke-width",
          titleBg.getAttribute("stroke-width") || "1"
        )
        titleBg.setAttribute("data-original-fill", titleBg.getAttribute("fill") || "")
      }

      // Apply purple background to title
      titleBg.setAttribute("fill", "#822dba")
      // Also update the stroke to match
      titleBg.setAttribute("stroke", "#822dba")
    }
  }

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
          try {
            self.highlightSchemaBanner(this)
          } catch (e) {
            console.log(e)
          }
          const set = $()
          set.push(this)
          const schemaName = event.currentTarget.dataset.name
          if (schemaName) {
            try {
              self.options.onSchemaClick(schemaName)
            } catch (e) {
              console.warn("onSchemaClick callback failed", e)
            }
          }
        })

        edges.on("click.graphui", function (event) {
          const up = $()
          const down = $()
          const edge = $()
          const [upStreamNode, downStreamNode] = event.currentTarget.dataset.name.split("->")
          const nodes = self.gv.nodesByName()
          up.push(nodes[upStreamNode])
          down.push(nodes[downStreamNode])
          edge.push(this)
          const upObj = { set: up, direction: "upstream" }
          const downObj = { set: down, direction: "downstream" }
          const edgeOjb = { set: edge, direction: "single" }
          self.currentSelection = [upObj, downObj, edgeOjb]

          self._highlightEdgeNodes()
        })

        nodes.on("click.graphui", function (event) {
          const set = $()
          set.push(this)
          const obj = { set, direction: "bidirectional" }

          const schemaName = event.currentTarget.dataset.name
          console.log("shift click detected")
          if (event.shiftKey && self.options.onSchemaShiftClick) {
            if (schemaName) {
              try {
                self.options.onSchemaShiftClick(schemaName)
              } catch (e) {
                console.warn("onSchemaShiftClick callback failed", e)
              }
            }
          } else {
            self.currentSelection = [obj]
            self._highlight()
          }
        })

        $(document)
          .off("click.graphui")
          .on("click.graphui", function (evt) {
            // if outside container, do nothing
            const graphContainer = $(self.selector)[0]
            if (!graphContainer || !evt.target || !graphContainer.contains(evt.target)) {
              return
            }

            let isNode = false
            const $everything = self.gv.$nodes.add(self.gv.$edges).add(self.gv.$clusters)
            const node = evt.target.parentNode
            $everything.each(function () {
              if (this === node) {
                isNode = true
              }
            })
            if (!isNode && self.gv) {
              self.gv.highlight()
              if (self.options.resetCb) {
                self.options.resetCb()
              }
            }
          })
      },
    })
  }

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
            resolve()
          })
      } catch (err) {
        reject(err)
      }
    })
  }
}
