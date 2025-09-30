export class GraphUI {
  constructor(selector = "#graph", options = {}) {
    this.selector = selector;
    this.options = options; // e.g. { onSchemaClick: (name) => {} }
    this.graphviz = d3.select(this.selector).graphviz();

    this.gv = null;
    this.currentSelection = [];
    this._init();
  }

  _highlight() {
    let highlightedNodes = $();
    for (const selection of this.currentSelection) {
      const nodes = this._getAffectedNodes(selection.set, "bidirectional");
      highlightedNodes = highlightedNodes.add(nodes);
    }
    if (this.gv) {
      this.gv.highlight(highlightedNodes, true);
    }
  }

  _getAffectedNodes($set, mode = "bidirectional") {
    let $result = $().add($set);
    if (mode === "bidirectional" || mode === "downstream") {
      $set.each((i, el) => {
        if (el.className.baseVal === "edge") {
          const edge = $(el).data("name");
          const nodes = this.gv.nodesByName();
          const downStreamNode = edge.split("->")[1];
          if (downStreamNode) {
            $result.push(nodes[downStreamNode]);
            $result = $result.add(
              this.gv.linkedFrom(nodes[downStreamNode], true)
            );
          }
        } else {
          $result = $result.add(this.gv.linkedFrom(el, true));
        }
      });
    }
    if (mode === "bidirectional" || mode === "upstream") {
      $set.each((i, el) => {
        if (el.className.baseVal === "edge") {
          const edge = $(el).data("name");
          const nodes = this.gv.nodesByName();
          const upStreamNode = edge.split("->")[0];
          if (upStreamNode) {
            $result.push(nodes[upStreamNode]);
            $result = $result.add(this.gv.linkedTo(nodes[upStreamNode], true));
          }
        } else {
          $result = $result.add(this.gv.linkedTo(el, true));
        }
      });
    }
    return $result;
  }

  _init() {
    const self = this;
    $(this.selector).graphviz({
      shrink: null,
      zoom: false,
      ready: function () {
        self.gv = this;

        self.gv.nodes().click(function (event) {
          const set = $();
          set.push(this);
          const obj = { set, direction: "bidirectional" };
          // Shift+Click to trigger schema detail callback (if provided)
          if (event.shiftKey && self.options.onSchemaClick) {
            // try data-name or title text
            const schemaName = event.currentTarget.dataset.name;
            if (schemaName) {
              try {
                self.options.onSchemaClick(schemaName);
              } catch (e) {
                console.warn("onSchemaClick callback failed", e);
              }
            }
          } else if (event.altKey && self.options.onSchemaAltClick) {
            const schemaName = event.currentTarget.dataset.name;
            self.options.onSchemaAltClick(schemaName);
          } else {
            self.currentSelection = [obj];
            self._highlight();
          }
        });

        self.gv.clusters().click(function (event) {
          const set = $();
          set.push(this);
          const obj = { set, direction: "single" };
          if (event.ctrlKey || event.metaKey || event.shiftKey) {
            self.currentSelection.push(obj);
          } else {
            self.currentSelection = [obj];
          }
          self._highlight();
        });

        $(document).on("keydown.graphui", function (evt) {
          if (evt.keyCode === 27 && self.gv) {
            self.gv.highlight();
          }
        });
      },
    });
  }

  async render(dotSrc) {
    const height = this.options.height || "100%";
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
            $(this.selector).data("graphviz.svg").setup();
            this.graphviz.resetZoom();
            resolve();
          });
      } catch (err) {
        reject(err);
      }
    });
  }
}
