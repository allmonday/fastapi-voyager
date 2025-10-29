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
    const ele = node.querySelector("polygon[fill='#009485']")
    if (ele) {
      ele.setAttribute('fill', 'tomato');
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
          // const obj = { set, direction: "bidirectional" };
          const schemaName = event.currentTarget.dataset.name;
          // self.currentSelection = [obj];
          if (schemaName) {
            try {
              self.options.onSchemaClick(schemaName);
            } catch (e) {
              console.warn("onSchemaClick callback failed", e);
            }
          }
        });
        self.gv.nodes().click(function (event) {
          const set = $();
          set.push(this);
          const obj = { set, direction: "bidirectional" };

          const schemaName = event.currentTarget.dataset.name;
          if (event.shiftKey && self.options.onSchemaClick) {
            // try data-name or title text
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
          if (event.ctrlKey || event.metaKey || event.shiftKey) {
            self.currentSelection.push(obj);
          } else {
            self.currentSelection = [obj];
          }
          self._highlight();
        });

        // svg 背景点击高亮清空

        $(document)
          .off("click.graphui")
          .on("click.graphui", function (evt) {
            // 如果点击目标不在 graph 容器内，直接退出
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

        $(document).on("keydown.graphui", function (evt) {
          if (evt.keyCode === 27 && self.gv) {
            self.gv.highlight();
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
