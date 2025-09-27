[![pypi](https://img.shields.io/pypi/v/fastapi-router-viz.svg)](https://pypi.python.org/pypi/fastapi-router-viz)
![Python Versions](https://img.shields.io/pypi/pyversions/fastapi-router-viz)


# fastapi-router-viz

If you use FastAPI for internal API integration, `fastapi-router-viz` helps to improve project's visibility.

It visualize FastAPI application's routes and inner dependencies inside response_models.

It can help identify the potential impact of data on interfaces and pages

> This repo is still in early stage.

```shell
router-viz -m tests.demo --app app --server
```

<img width="1847" height="801" alt="image" src="https://github.com/user-attachments/assets/181c7087-8bc0-4c94-bd66-34462f65a851" />


youtube:

[![IMAGE ALT TEXT](http://img.youtube.com/vi/msYsB9Cc3CA/0.jpg)](https://www.youtube.com/watch?v=msYsB9Cc3CA "Unity Snake Game")

## Feature

- visualize the entity-relationship diagram of each API
- quickly find the dependencies of picked entity
- view the full dependencies of each tags/ routes

## Installation

```bash
pip install fastapi-router-viz
# or
uv add fastapi-router-viz
```

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

- [x] group schemas by module hierarchy
- [x] module-based coloring via Analytics(module_color={...})
- [x] view in web browser
    - [x] config params
    - [x] make a explorer dashboard, provide list of routes, schemas, to make it easy to switch and search
- [x] support programmatic usage
- [x] better schema /router node appearance
- [x] hide fields duplicated with parent's (show `parent fields` instead)
- [x] refactor the frontend to vue, and tweak the build process
- [ ] find dependency based on picked schema and it's field.
- [ ] user can generate nodes/edges manually and connect to generated ones
- [ ] add configuration for highlight (optional)
- [ ] support dataclass
- [ ] integration with pydantic-resolve
    - [ ] show difference between resolve, post fields
    - [ ] strikethrough for excluded fields
    - [ ] display loader as edges


## Credits

- https://github.com/tintinweb/vscode-interactive-graphviz, for web visualization.
