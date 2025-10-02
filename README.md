[![pypi](https://img.shields.io/pypi/v/fastapi-router-viz.svg)](https://pypi.python.org/pypi/fastapi-router-viz)
![Python Versions](https://img.shields.io/pypi/pyversions/fastapi-router-viz)

## Installation

```bash
pip install fastapi-router-viz
# or
uv add fastapi-router-viz

router-viz --demo  # open localhost:8000 to visit demo page
```

## Dependencies

- FastAPI
- pydantic-resolve


## Feature

For scenarios of using FastAPI as internal API integration endpoints, `fastapi-router-viz` helps to see the internal dependencies.

> This repo is still in early stage.

```shell
router-viz -m tests.demo 
           --server --port=8001 
           --module_color=tests.service:blue 
           --module_color=tests.demo:tomato
```

pick tag, rotue (optional) and click `generate`.

<img width="1919" height="898" alt="image" src="https://github.com/user-attachments/assets/05e321d0-49f3-4af6-a7c7-f4c9c6b1dbfd" />

click a node to highlight it's upperstream and downstream nodes. figure out the related models of one page, or homw many pages are related with one model.

<img width="1485" height="616" alt="image" src="https://github.com/user-attachments/assets/70c4095f-86c7-45da-a6f0-fd41ac645813" />


`shift` click a node to check related nodes.

pick a field to narrow the result.

<img width="1917" height="800" alt="image" src="https://github.com/user-attachments/assets/e770dc70-f293-49e1-bcd7-d8dffa15d9ea" />

`alt` click a node to show source code or open file in vscode.

<img width="497" height="402" alt="image" src="https://github.com/user-attachments/assets/ac81711a-d9c2-4fb1-8b3a-0f4bd1f02572" />

more in video:

[![IMAGE ALT TEXT](http://img.youtube.com/vi/msYsB9Cc3CA/0.jpg)](https://www.youtube.com/watch?v=msYsB9Cc3CA "Unity Snake Game")


## Command Line Usage

```bash
# Basic usage - assumes your FastAPI app is named 'app' in app.py
router-viz tests/demo.py

# Specify custom app variable name
router-viz tests/demo.py --app app

# filter tag name
router-viz tests/demo.py --app app --tags page

# filter schema name, display related nodes
router-viz tests/demo.py --app app --schema Task

# show fields
router-viz tests/demo.py --app app --show_fields all

# highlight module
router-viz tests/demo.py --app app --module_color=tests.demo:red

# Custom output file
router-viz tests/demo.py -o my_visualization.dot

# server mode
router-viz tests/demo.py --app app --server --show_fields --module_color=tests.demo:red 

# Show help
router-viz --help

# Show version
router-viz --version
```

The tool will generate a DOT file that you can render using Graphviz:

```bash
# Install graphviz
brew install graphviz  # macOS
apt-get install graphviz  # Ubuntu/Debian

# Render the graph
dot -Tpng router_viz.dot -o router_viz.png

# Or view online at: https://dreampuf.github.io/GraphvizOnline/
```

or you can open router_viz.dot with vscode extension `graphviz interactive preview`


## Next

features:
- [x] group schemas by module hierarchy
- [x] module-based coloring via Analytics(module_color={...})
- [x] view in web browser
    - [x] config params
    - [x] make a explorer dashboard, provide list of routes, schemas, to make it easy to switch and search
- [x] support programmatic usage
- [x] better schema /router node appearance
- [x] hide fields duplicated with parent's (show `parent fields` instead)
- [x] refactor the frontend to vue, and tweak the build process
- [x] find dependency based on picked schema and it's field.
- [x] optimize static resource (cdn -> local)
- [x] add configuration for highlight (optional)
- [ ] display source code of routes (including response_model)
- [ ] ctrl+click to show field details
- [ ] user can generate nodes/edges manually and connect to generated ones
- [ ] support dataclass
- [ ] integration with pydantic-resolve
    - [ ] show difference between resolve, post fields
    - [x] strikethrough for excluded fields
    - [ ] display loader as edges

bugs:
- [ ] fix duplicated link from class and parent class, it also break clicking highlight
- [ ] handle excluded field 


## Credits

- https://github.com/tintinweb/vscode-interactive-graphviz, for web visualization.
