// Expose a small API to be used by the Vue/Quasar app
window.GraphUI = (function () {
  let graphviz;
  let gv;
  var currentSelection = [];

  function highlight() {
    let highlightedNodes = $();
    for (const selection of currentSelection) {
      const nodes = getAffectedNodes(selection.set, "bidirectional");
      highlightedNodes = highlightedNodes.add(nodes);
    }

    gv.highlight(highlightedNodes, true);
    //gv.bringToFront(highlightedNodes);
  }
  function getAffectedNodes($set, $mode = "bidirectional") {
    let $result = $().add($set);
    if ($mode === "bidirectional" || $mode === "downstream") {
      $set.each((i, el) => {
        if (el.className.baseVal === "edge") {
          const edge = $(el).data("name");
          const nodes = gv.nodesByName();
          const downStreamNode = edge.split("->")[1];
          if (downStreamNode) {
            $result.push(nodes[downStreamNode]);
            $result = $result.add(gv.linkedFrom(nodes[downStreamNode], true));
          }
        } else {
          $result = $result.add(gv.linkedFrom(el, true));
        }
      });
    }
    if ($mode === "bidirectional" || $mode === "upstream") {
      $set.each((i, el) => {
        if (el.className.baseVal === "edge") {
          const edge = $(el).data("name");
          const nodes = gv.nodesByName();
          const upStreamNode = edge.split("->")[0];
          if (upStreamNode) {
            $result.push(nodes[upStreamNode]);
            $result = $result.add(gv.linkedTo(nodes[upStreamNode], true));
          }
        } else {
          $result = $result.add(gv.linkedTo(el, true));
        }
      });
    }
    return $result;
  }

  function init() {
    graphviz = d3.select("#graph").graphviz();
    $("#graph").graphviz({
      shrink: null,
      zoom: false,
      ready: function () {
        gv = this;

        gv.nodes().click(function (event) {
          const set = $();
          set.push(this);

          var obj = {
            set: set,
            direction: "bidirectional",
          };
          // If CMD or CTRL is pressed, then add this to the selection
          if (event.ctrlKey || event.metaKey || event.shiftKey) {
            currentSelection.push(obj);
          } else {
            currentSelection = [obj];
          }

          highlight();
        });
        gv.clusters().click(function (event) {
          const set = $();
          set.push(this);

          var obj = {
            set: set,
            direction: "single",
          };
          // If CMD or CTRL is pressed, then add this to the selection
          if (event.ctrlKey || event.metaKey || event.shiftKey) {
            currentSelection.push(obj);
          } else {
            currentSelection = [obj];
          }
          highlight();
        });

        $(document).keydown(function (evt) {
          // press escape to cancel highlight
          if (evt.keyCode == 27) {
            gv.highlight();
          }
        });
      },
    });
  }

  function render(dotSrc) {
    graphviz
      .engine("dot")
      .fade(true)
      .tweenPaths(true) // default
      .tweenShapes(true) // default
      .zoomScaleExtent([0, Infinity])
      .zoom(true)
      .renderDot(dotSrc)
      .on("end", function () {
        $("#graph").data("graphviz.svg").setup();
        // Make SVG fill its container (which fills the viewport)
        const $svg = $("#graph svg");
        $svg.attr("width", "100%");
        $svg.attr("height", "100%");
        $svg.attr("preserveAspectRatio", "xMidYMid meet");
        // notify listeners that graph rendering is complete
        $(document).trigger("graphviz:render:end");
      });
  }
  async function renderDot(dotText) {
    return new Promise((resolve) => {
      $(document).one("graphviz:render:end", resolve);
      render(dotText);
    });
  }

  // auto-init when DOM ready, so the Vue app can call render later
  $(document).ready(function () {
    init();
  });

  return { renderDot };
})();
