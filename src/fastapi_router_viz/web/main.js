$(document).ready(function () {
  let graphviz = d3.select("#graph").graphviz();
  let gv;
  var currentSelection = [];
  let optionData = { tags: [], schemas: [] };
  // Map of schema label -> schema name for autocomplete selection
  let schemaLabelToName = {};

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

  function populateControls(data) {
    // Populate tags (single-select)
    optionData.tags = Array.isArray(data.tags) ? data.tags : [];
    const $tags = $("#tags");
    // Initialize jQuery UI Autocomplete for tags
    $tags.val("");
    $tags
      .autocomplete({
        source: optionData.tags,
        minLength: 0,
        delay: 0,
      })
      .on("focus", function () {
        $(this).autocomplete("search", "");
      });

    // Populate schemas (single-select)
    optionData.schemas = Array.isArray(data.schemas) ? data.schemas : [];
    const $schema = $("#schema");
    schemaLabelToName = {};
    const schemaLabels = [];
    for (const s of optionData.schemas) {
      const label = `${s.name} (${s.fullname})`;
      schemaLabels.push(label);
      schemaLabelToName[label] = s.name;
    }
    // Initialize jQuery UI Autocomplete for schemas
    $schema.val("");
    $schema
      .autocomplete({
        source: schemaLabels,
        minLength: 0,
        delay: 0,
        select: function (event, ui) {
          // when a schema is selected, ui.item.value is the label
          // we map it to the actual schema name when generating
          $(this).data("selected-schema", schemaLabelToName[ui.item.value]);
        },
        change: function (event, ui) {
          if (!ui.item) {
            // if the value typed doesn't match a known label, clear selection
            $(this).data("selected-schema", null);
          }
        },
      })
      .on("focus", function () {
        $(this).autocomplete("search", "");
      });
  }

  async function loadInitial() {
    const res = await fetch("/dot");
    const data = await res.json();
    populateControls(data);
    // render(data.dot);
  }

  function setGeneratingState(isGenerating) {
    const $generate = $("#generate");
    const $controls = $("#controls :input, #controls button");
    if (isGenerating) {
      if (!$generate.data("original-text")) {
        $generate.data("original-text", $generate.text());
      }
      $generate.text("generating...");
      $controls.prop("disabled", true);
    } else {
      const original = $generate.data("original-text") || "Generate";
      $generate.text(original);
      $controls.prop("disabled", false);
    }
  }

  $("#generate").on("click", async function () {
    setGeneratingState(true);
    const tagInput = $("#tags").val();
    const selectedTags = tagInput ? tagInput : null;

    const schemaInput = $("#schema").val() || "";
    // If user selected from the autocomplete, we stored the actual name on data
    const selectedSchemaName =
      $("#schema").data("selected-schema") ||
      schemaLabelToName[schemaInput] ||
      schemaInput ||
      null;

    const payload = {
      tags: selectedTags ? [selectedTags] : null,
      schema_name: selectedSchemaName ? selectedSchemaName : null,
      show_fields: $("#show_fields").val(),
    };

    try {
      const res = await fetch("/dot", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const dotText = await res.text();
      // when rendering completes, revert loading state (one-time listener)
      $(document).one("graphviz:render:end", function () {
        setGeneratingState(false);
      });
      render(dotText);
    } catch (err) {
      console.error("Failed to generate filtered DOT:", err);
      setGeneratingState(false);
    }
  });

  $("#reset").on("click", async function () {
    // reset selects to default "-- All --"
    $("#tags").val("");
    $("#schema").val("");
    $("#show_fields").val("object");
    // reload options and default graph
    try {
      await loadInitial();
    } catch (err) {
      console.error("Failed to reset:", err);
    }
  });

  // Initial load
  loadInitial();
});
