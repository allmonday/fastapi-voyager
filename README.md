[![pypi](https://img.shields.io/pypi/v/fastapi-voyager.svg)](https://pypi.python.org/pypi/fastapi-voyager)
![Python Versions](https://img.shields.io/pypi/pyversions/fastapi-voyager)

<p align="center"><img src="./voyager.jpg" alt="" /></p>

> This repo is still in early stage, currently it supports pydantic v2 only, previous name: fastapi-router-viz

Inspect your API interactively

<img width="1480" height="648" alt="image" src="https://github.com/user-attachments/assets/a6ccc9f1-cf06-493a-b99b-eb07767564bd" />

## Installation

```bash
pip install fastapi-voyager
# or
uv add fastapi-voyager
```

```shell
voyager -m path.to.your.app.module --server
```

## Dependencies

- FastAPI
- [pydantic-resolve](https://github.com/allmonday/pydantic-resolve)


## Feature

For scenarios of using FastAPI as internal API integration endpoints, `fastapi-voyager` helps to visualize the dependencies.

It is also an architecture inspection tool that can identify issues in data relationships through visualization during the design phase.

If the process of building the view model follows the ER model, the full potential of fastapi-voyager can be realized. It allows for quick identification of APIs  that use entities, as well as which entities are used by a specific API



```shell
git clone https://github.com/allmonday/fastapi-voyager.git
cd fastapi-voyager

voyager -m tests.demo 
           --server --port=8001 
           --module_color=tests.service:blue 
           --module_color=tests.demo:tomato
```

### generate the graph
after initialization, pick tag, rotue (optional) and click `generate`.

<img width="1919" height="898" alt="image" style="border: 1px solid #aaa" src="https://github.com/user-attachments/assets/05e321d0-49f3-4af6-a7c7-f4c9c6b1dbfd" />

### highlight
click a node to highlight it's upperstream and downstream nodes. figure out the related models of one page, or homw many pages are related with one model.

<img width="1485" height="616" alt="image" style="border: 1px solid #aaa" src="https://github.com/user-attachments/assets/70c4095f-86c7-45da-a6f0-fd41ac645813" />

### filter related nodes
`shift` click a node to check related node, pick a field to narrow the result.

<img width="1917" height="800" alt="image" style="border: 1px solid #aaa" src="https://github.com/user-attachments/assets/e770dc70-f293-49e1-bcd7-d8dffa15d9ea" />

### view source code
`alt` click a node to show source code or open file in vscode.

<img width="1049" height="694" alt="image" src="https://github.com/user-attachments/assets/7839ac83-8d60-44ad-b1c9-9652a76339b1" />

<img width="1042" height="675" alt="image" src="https://github.com/user-attachments/assets/38ae705f-5982-4a02-9c3f-038b1d00bcf6" />

`alt` click a route to show source code or open file in vscode

<img width="882" height="445" alt="image" src="https://github.com/user-attachments/assets/158560ef-63ca-4991-9b7d-587be4fa04e4" />


## Mount to target project

```python
from fastapi import FastAPI
from fastapi_voyager.server import create_app_with_fastapi
from tests.demo import app

app.mount('/voyager', create_app_with_fastapi(app))
```

more about [sub application](https://fastapi.tiangolo.com/advanced/sub-applications/?h=sub)


## Command Line Usage

### open in browser

```bash
# open in browser
voyager -m tests.demo --server  

voyager -m tests.demo --server --port=8002
```

### generate the dot file
```bash
# generate .dot file
voyager -m tests.demo  

voyager -m tests.demo --app my_app

voyager -m tests.demo --schema Task

voyager -m tests.demo --show_fields all

voyager -m tests.demo --module_color=tests.demo:red --module_color=tests.service:tomato

voyager -m tests.demo -o my_visualization.dot

voyager --version
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


## Plan before v1.0

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
- [x] alt+click to show field details
- [x] display source code of routes (including response_model)
- [x] handle excluded field 
- [x] add tooltips
- [x] route
    - [x] group routes by module hierarchy
    - [ ] add response_model in route
- [ ] support dataclass (pending)
- [ ] click field to highlight links
- [ ] user can generate nodes/edges manually and connect to generated ones
    - [ ] add owner
    - [ ] add extra info for schema
- [ ] ui optimization
    - [ ] fixed left/right bar show field information
    - [x] fixed left bar show tag/ route
- [ ] display standard ER diagram `difference`
    - [ ] display potential invalid links
- [ ] integration with pydantic-resolve
    - [ ] show difference between resolve, post fields
    - [x] strikethrough for excluded fields
    - [ ] display loader as edges
- [x] export voyager core data into json (for better debugging)
    - [x] add api to rebuild core data from json, and render it
- [x] fix Generic case  `test_generic.py`

bugs & non feature:
- [x] fix duplicated link from class and parent class, it also break clicking highlight
- [ ] add tests
- [x] refactor
    - [x] abstract render module

## Using with pydantic-resolve

pydantic-resolve's @ensure_subset decorator is helpful to pick fields from `source class` in safe.

TODO: ...


## Credits

- https://apis.guru/graphql-voyager/, for inspiration.
- https://github.com/tintinweb/vscode-interactive-graphviz, for web visualization.


## Changelog

- 0.7:
    - 0.7.5
        - fix show all display issue
    - 0.7.4
        - optimize tag/route, move to left. 
        - fresh on change, no need to click generate any more.
    - 0.7.3
        - fix `module_color` failure
    - 0.7.2
        - keep links inside filtered nodes.
    - 0.7.1
        - support brief mode, you can use `--module_prefix tests.service` to show links between routes and filtered schemas, to make the graph less complicated.
- 0.6: 
    - 0.6.2: 
        - fix generic related issue
