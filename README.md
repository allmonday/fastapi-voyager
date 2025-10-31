[![pypi](https://img.shields.io/pypi/v/fastapi-voyager.svg)](https://pypi.python.org/pypi/fastapi-voyager)
![Python Versions](https://img.shields.io/pypi/pyversions/fastapi-voyager)
[![PyPI Downloads](https://static.pepy.tech/badge/fastapi-voyager/month)](https://pepy.tech/projects/fastapi-voyager)


> This repo is still in early stage, it supports pydantic v2 only

FastAPI can help you:

- design your API
- inspect your API
- refactor your API

interactively !!


[visit online demo](https://www.newsyeah.fun/voyager/) of project: [composition oriented development pattern](https://github.com/allmonday/composition-oriented-development-pattern)

<p align="center"><img src="./voyager.jpg" alt="" /></p>
<p align="center"><a target="_blank" rel="" href="https://www.youtube.com/watch?v=PGlbQq1M-n8"><img src="http://img.youtube.com/vi/PGlbQq1M-n8/0.jpg" alt="" style="max-width: 100%;"></a></p>

## Installation

```bash
pip install fastapi-voyager
# or
uv add fastapi-voyager
```

```shell
voyager -m path.to.your.app.module --server
```

## Mount into project

```python
from fastapi import FastAPI
from fastapi_voyager import create_voyager
from tests.demo import app

app.mount('/voyager', create_voyager(
    app, 
    module_color={"tests.service": "red"}, 
    module_prefix="tests.service"),
    swagger_url="/docs")
```

more about [sub application](https://fastapi.tiangolo.com/advanced/sub-applications/?h=sub)


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
after initialization, pick tag, rotue to render graph

<img width="1628" height="765" alt="image" src="https://github.com/user-attachments/assets/b4712f82-e754-453b-aa69-24c932b8f48f" />

### highlight
click a node to highlight it's upperstream and downstream nodes. figure out the related models of one page, or homw many pages are related with one model.

<img width="1485" height="616" alt="image" style="border: 1px solid #aaa" src="https://github.com/user-attachments/assets/70c4095f-86c7-45da-a6f0-fd41ac645813" />

### filter related nodes
`shift` click a node to check related node, pick a field to narrow the result, picked node is marked as red.

<img width="1423" height="552" alt="image" src="https://github.com/user-attachments/assets/468a058d-afa1-4601-a7c5-c6aad6a8a557" />

### view source code
`alt` click a node to show source code or open file in vscode.

<img width="1049" height="694" alt="image" src="https://github.com/user-attachments/assets/7839ac83-8d60-44ad-b1c9-9652a76339b1" />

<img width="1042" height="675" alt="image" src="https://github.com/user-attachments/assets/38ae705f-5982-4a02-9c3f-038b1d00bcf6" />

`alt` click a route to show source code or open file in vscode

<img width="882" height="445" alt="image" src="https://github.com/user-attachments/assets/158560ef-63ca-4991-9b7d-587be4fa04e4" />




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


### backlog
- [ ] user can generate nodes/edges manually and connect to generated ones
    - [ ] eg: add owner
    - [ ] add extra info for schema
- [ ] display standard ER diagram `hard`
    - [ ] display potential invalid links
- [ ] optimize static resource (allow manually config url)
- [ ] improve search dialog
    - [ ] add route/tag list
- [ ] type alias should not be kept as node instead of compiling to original type
- [ ] how to correctly handle the generic type ?

### in analysis
- [ ] click field to highlight links
- [ ] animation effect for edges
- [ ] customrized right click panel
    - [ ] show own dependencies

### plan:
#### <0.9:
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
    - [x] add response_model in route
- [x] fixed left bar show tag/ route
- [x] export voyager core data into json (for better debugging)
    - [x] add api to rebuild core data from json, and render it
- [x] fix Generic case  `test_generic.py`
- [x] show tips for routes not return pydantic type.
- [x] fix duplicated link from class and parent class, it also break clicking highlight
- [x] refactor: abstract render module

#### 0.9
- [x] refactor: server.py
    - [x] rename create_app_with_fastapi -> create_voyager
    - [x] add doc for parameters
- [x] improve initialization time cost
    - [x] query route / schema info through realtime api
    - [x] adjust fe
- 0.9.3
    - [x] adjust layout 
        - [x] show field detail in right panel
        - [x] show route info in bottom
- 0.9.4
    - [x] close schema sidebar when switch tag/route
    - [x] schema detail panel show fields by default
    - [x] adjust schema panel's height
    - [x] show from base information in subset case
- 0.9.5
    - [x] route list should have a max height 

#### 0.10
- 0.10.1
    - [x] refactor voyager.py tag -> route structure
    - [x] fix missing route (tag has only one route which return primitive value)
    - [x] make right panel resizable by dragging
    - [x] allow closing tag expansion item
    - [x] hide brief mode if not configured
    - [x] add focus button to only show related nodes under current route/tag graph in dialog
- 0.10.2
    - [x] fix graph height
    - [x] show version in title
- 0.10.3
    - [x] fix focus in brief-mode
    - [x] ui: adjust focus position
    - [x] refactor naming
    - [x] fix layout issue when rendering huge graph
- 0.10.4
    - [x] fix: when focus is on, should ensure changes from other params not broken.
- 0.10.5
    - [x] double click to show details, and highlight as tomato
    

#### 0.11
- 0.11.1
    - [x] support opening route in swagger
        - [x] config docs path
    - [x] provide option to hide routes in brief mode (auto hide in full graph mode)
- 0.11.2
    - [x] enable/disable module cluster  (to save space)
- 0.11.3
    - [x] support online repo url
- 0.11.4
    - [x] add loading for field detail panel
- 0.11.5
    - [x] optimize open in swagger link
    - [ ] logging information
    - [ ] sort field name
    - [ ] set max limit for fields

#### 0.12
- [ ] add tests
- [ ] integration with pydantic-resolve
    - [ ] show hint for resolve, post fields
    - [ ] display loader as edges

#### 0.13
- [ ] config release pipeline


## Using with pydantic-resolve

WIP: ...

pydantic-resolve's @ensure_subset decorator is helpful to pick fields from `source class` in safe.



## Credits

- https://apis.guru/graphql-voyager/, thanks for inspiration.
- https://github.com/tintinweb/vscode-interactive-graphviz, thanks for web visualization.


## Dependencies

- FastAPI
- [pydantic-resolve](https://github.com/allmonday/pydantic-resolve)
- Quasar

