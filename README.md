[![pypi](https://img.shields.io/pypi/v/fastapi-voyager.svg)](https://pypi.python.org/pypi/fastapi-voyager)
![Python Versions](https://img.shields.io/pypi/pyversions/fastapi-voyager)
[![PyPI Downloads](https://static.pepy.tech/badge/fastapi-voyager/month)](https://pepy.tech/projects/fastapi-voyager)


> This repo is still in early stage, it supports pydantic v2 only

Visualize your FastAPI endpoints, and explore them interactively.

[visit online demo](https://www.newsyeah.fun/voyager/) of project: [composition oriented development pattern](https://github.com/allmonday/composition-oriented-development-pattern)

<img width="1600" height="986" alt="image" src="https://github.com/user-attachments/assets/8829cda0-f42d-4c84-be2f-b019bb5fe7e1" />

## Installation

```bash
pip install fastapi-voyager
# or
uv add fastapi-voyager
```

```shell
voyager -m path.to.your.app.module --server
```

> [Sub-Application mounts](https://fastapi.tiangolo.com/advanced/sub-applications/) are not supported yet, but you can specify the name of the FastAPI application used with `--app`. Only a single application (default: 'app') can be selected, but in a scenario where `api` is attached through `app.mount("/api", api)`, you can select `api` like this:

```shell
voyager -m path.to.your.app.module --server --app api
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

### highlight
click a node to highlight it's upperstream and downstream nodes. figure out the related models of one page, or homw many pages are related with one model.

<img width="1100" height="700" alt="image" src="https://github.com/user-attachments/assets/3e0369ea-5fa4-469a-82c1-ed57d407e53d" />

### focus on nodes
toggle focus to hide nodes not related with current picked one.

before: 
<img width="1066" height="941" alt="image" src="https://github.com/user-attachments/assets/39f30817-899a-4289-93f4-a1646d3441c1" />
after:
<img width="1061" height="937" alt="image" src="https://github.com/user-attachments/assets/79709b02-7571-43fc-abc9-17a287a97515" />

### view source code
double click a node to show source code or open file in vscode.
<img width="1297" height="940" alt="image" src="https://github.com/user-attachments/assets/c8bb2e7d-b727-42a6-8c9e-64dce297d2d8" />

double click a route to show source code or open file in vscode
<img width="1132" height="824" alt="image" src="https://github.com/user-attachments/assets/b706e879-e4fc-48dd-ace1-99bf97e3ed6a" />



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

voyager --help
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


## About pydantic-resolve

pydantic-resolve's `@ensure_subset` decorator helps safely pick fields from the 'source class' while indicating the reference from the current class to the base class.

pydantic-resolve is a lightweight tool designed to build complex, nested data in a simple, declarative way. In version 2, it will introduce an important feature: ER model definition, and fastapi-voyager will support and visualize these diagrams.

Developers can use fastapi-voyager without needing to know about pydantic-resolve.


## Credits

- https://apis.guru/graphql-voyager/, thanks for inspiration.
- https://github.com/tintinweb/vscode-interactive-graphviz, thanks for web visualization.


## Dependencies

- FastAPI
- [pydantic-resolve](https://github.com/allmonday/pydantic-resolve)
- Quasar


## How to develop & contribute?

fork, clone.

install uv.

```shell
uv venv
source .venv/bin/activate
uv pip install ".[dev]"
uvicorn tests.programatic:app  --reload
```

open `localhost:8000/voyager`


frontend: `src/web/vue-main.js`
backend: `voyager.py`, `render.py`, `server.py`

## Branch and Release flow

TODO
