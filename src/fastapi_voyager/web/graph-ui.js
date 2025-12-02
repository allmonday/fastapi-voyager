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

  highlightSchemaBanner(node) {
    const polygons = node.querySelectorAll("polygon");
    const ele = polygons[2]; // select the second polygon
    if (ele) {
      ele.setAttribute('stroke-width', '3.5');
    }
  }

  _init() {
    const self = this;
    $(this.selector).graphviz({
      shrink: null,
      zoom: false,
      ready: function () {
        self.gv = this;

        self.gv.nodes().dblclick(function (event) {
          event.stopPropagation();
          try {
            self.highlightSchemaBanner(this)
          } catch(e) {
            console.log(e)
          }
          const set = $();
          set.push(this);
          const schemaName = event.currentTarget.dataset.name;
          if (schemaName) {
            try {
              self.options.onSchemaClick(schemaName);
            } catch (e) {
              console.warn("onSchemaClick callback failed", e);
            }
          }
        });

        self.gv.edges().click(function (event) {
          // const set = $();
          // const downStreamNode = event.currentTarget.dataset.name.split("->")[1];
          // const nodes = self.gv.nodesByName();
          // set.push(nodes[downStreamNode]);
          // const obj = { set, direction: "single" };
          // self.currentSelection = [obj];
          // todo highlight edge and downstream node
        })

        self.gv.nodes().click(function (event) {
          const set = $();
          set.push(this);
          const obj = { set, direction: "bidirectional" };

          const schemaName = event.currentTarget.dataset.name;
          if (event.shiftKey && self.options.onSchemaClick) {
            if (schemaName) {
              try {
                self.options.onSchemaShiftClick(schemaName);
              } catch (e) {
                console.warn("onSchemaShiftClick callback failed", e);
              }
            }
          } else {
            self.currentSelection = [obj];
            self._highlight();
            try {
              self.options.resetCb();
            } catch (e) {
              console.warn("resetCb callback failed", e);
            }
          }
        });

        self.gv.clusters().click(function (event) {
          const set = $();
          set.push(this);
          const obj = { set, direction: "single" };
          self.currentSelection = [obj];
          self._highlight();
        });

        // click background to reset highlight 
        $(document)
          .off("click.graphui")
          .on("click.graphui", function (evt) {
            // if outside container, do nothing
            const graphContainer = $(self.selector)[0];
            if (
              !graphContainer ||
              !evt.target ||
              !graphContainer.contains(evt.target)
            ) {
              return;
            }

            let isNode = false;
            const $nodes = self.gv.nodes();
            const node = evt.target.parentNode;
            $nodes.each(function () {
              if (this === node) {
                isNode = true;
              }
            });
            if (!isNode && self.gv) {
              self.gv.highlight();
              if (self.options.resetCb) {
                self.options.resetCb();
              }
            }
          });
      },
    });
  }

  async render(dotSrc, resetZoom = true) {
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
            if (resetZoom) this.graphviz.resetZoom();
            resolve();
          });
      } catch (err) {
        reject(err);
      }
    });
  }
}
