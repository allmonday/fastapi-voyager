[![pypi](https://img.shields.io/pypi/v/fastapi-router-viz.svg)](https://pypi.python.org/pypi/fastapi-router-viz)
![Python Versions](https://img.shields.io/pypi/pyversions/fastapi-router-viz)


# fastapi-router-viz

Visualize FastAPI application's routes and inner dependencies inside response_models.

> This repo is still in early stage.


[![Video Title](https://img.youtube.com/vi/9ywdMt1wPOY/0.jpg)](https://www.youtube.com/watch?v=9ywdMt1wPOY)


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

# group & highlight your schems as lightblue which located in service modules
router-viz tests/demo.py --app app --service_prefixes tests.service

# filter tag name
router-viz tests/demo.py --app app --tags page

# filter schema name, display related nodes
router-viz tests/demo.py --app app --schema Task

# show fields
router-viz tests/demo.py --app app --show_fields

# Custom output file
router-viz tests/demo.py -o my_visualization.dot

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

<img width="1062" height="283" alt="image" src="https://github.com/user-attachments/assets/d8134277-fa84-444a-b6cd-1287e477a83e" />

`--show_fields` to display details

<img width="1329" height="592" alt="image" src="https://github.com/user-attachments/assets/d5dceee8-995b-4dab-a016-46fa98e74d77" />


## Next

- [ ] group schemas by module hierarchy
- [ ] support programmatic usage
- [ ] support dataclass
- [ ] user can generate nodes/edges manually and connect to generated ones
- [ ] add configuration for highlight (optional)
- [ ] make a explorer dashboard, provide list of routes, schemas, to make it easy to switch and search
- [ ] integration with pydantic-resolve
    - [ ] show difference between resolve, post fields
    - [ ] strikethrough for excluded fields
    - [ ] display loader as edges