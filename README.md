# fastapi-router-viz

Visualize FastAPI application's routing tree and dependencies

> This repo is still in early stage.

## Installation

```bash
pip install fastapi-router-viz
# or
uv add fastapi-router-viz
```

## Command Line Usage

Once installed, you can use the `router-viz` command to generate visualization graphs from your FastAPI applications:

```bash
# Basic usage - assumes your FastAPI app is named 'app' in app.py
router-viz app.py

# Specify custom app variable name
router-viz main.py --app my_app

# Custom output file
router-viz app.py -o my_visualization.dot

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

## Programmatic Usage

```python
from fastapi_router_viz.graph import Analytics
from pydantic import BaseModel
from fastapi import FastAPI
from typing import Optional


def test_analysis():

    class X(BaseModel):
        id: int

    class B(BaseModel):
        id: int
        value: str
        x: X

    class A(BaseModel):
        id: int
        name: str
        b: B

    class C(BaseModel):
        id: int
        name: str
        b: B
        x: X

    class D(BaseModel):
        id: int
        name: str
        b: B

    app = FastAPI()

    @app.get("/test", response_model=Optional[A])
    def a():
        return None

    @app.get("/test2", response_model=Optional[C])
    def b():
        return None

    @app.get("/test3", response_model=Optional[D])
    def c():
        return None

    @app.get("/test4", response_model=Optional[D])
    def d():
        return None

    analytics = Analytics()
    analytics.analysis(app)
    print(analytics.generate_dot())


if __name__ == "__main__":
    test_analysis()
```

generate the dot description

```dot
digraph mygraph {
    fontname="Helvetica,Arial,sans-serif"
    node [fontname="Helvetica,Arial,sans-serif"]
    edge [fontname="Helvetica,Arial,sans-serif"]
    graph [
        rankdir = "LR"
    ];
    node [
        fontsize = "16"
    ];

    "router: a_test_get" [
        label = "router: a_test_get"
        shape = "record"
        fillcolor = "lightgreen"
        style = "filled"
    ];

    "router: b_test2_get" [
        label = "router: b_test2_get"
        shape = "record"
        fillcolor = "lightgreen"
        style = "filled"
    ];

    "router: c_test3_get" [
        label = "router: c_test3_get"
        shape = "record"
        fillcolor = "lightgreen"
        style = "filled"
    ];

    "router: d_test4_get" [
        label = "router: d_test4_get"
        shape = "record"
        fillcolor = "lightgreen"
        style = "filled"
    ];

    "__main__.test_analysis.<locals>.A" [
        label = "A"
        shape = "record"
    ];

    "__main__.test_analysis.<locals>.B" [
        label = "B"
        shape = "record"
    ];

    "__main__.test_analysis.<locals>.X" [
        label = "X"
        shape = "record"
    ];

    "__main__.test_analysis.<locals>.C" [
        label = "C"
        shape = "record"
    ];

    "__main__.test_analysis.<locals>.D" [
        label = "D"
        shape = "record"
    ];
    "router: a_test_get" -> "__main__.test_analysis.<locals>.A";
    "router: b_test2_get" -> "__main__.test_analysis.<locals>.C";
    "router: c_test3_get" -> "__main__.test_analysis.<locals>.D";
    "router: d_test4_get" -> "__main__.test_analysis.<locals>.D";
    "__main__.test_analysis.<locals>.A" -> "__main__.test_analysis.<locals>.B";
    "__main__.test_analysis.<locals>.B" -> "__main__.test_analysis.<locals>.X";
    "__main__.test_analysis.<locals>.C" -> "__main__.test_analysis.<locals>.B";
    "__main__.test_analysis.<locals>.C" -> "__main__.test_analysis.<locals>.X";
    "__main__.test_analysis.<locals>.D" -> "__main__.test_analysis.<locals>.B";
    }
```

then you'll see the internal dependencies

<img width="1231" height="625" alt="image" src="https://github.com/user-attachments/assets/46cf82ac-5d06-4cf0-adbd-ceb422709656" />
