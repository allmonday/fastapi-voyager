# fastapi-router-viz

Visualize FastAPI application's routes and inner dependencies inside response_models.

> This repo is still in early stage.

## Installation

```bash
pip install fastapi-router-viz
# or
uv add fastapi-router-viz
```

## Command Line Usage

```python
class PageTask(Task):
    owner: Optional[Member]

@ensure_subset(Story)
class PageStory(BaseModel):
    id: int
    sprint_id: int
    title: str

    tasks: list[PageTask] = []
    owner: Optional[Member] = None

class PageSprint(Sprint):
    stories: list[PageStory]
    owner: Optional[Member]

class PageOverall(BaseModel):
    sprints: list[PageSprint]


@app.get("/page_overall", tags=['page'], response_model=PageOverall)
def get_page_info():
    return {"sprints": []}


class PageStories(BaseModel):
    stories: list[PageStory]

@app.get("/page_stories/", tags=['page'], response_model=PageStories)
def get_page_info_2():
    return {}
```

```bash
# Basic usage - assumes your FastAPI app is named 'app' in app.py
router-viz tests/demo.py

# Specify custom app variable name
router-viz tests/demo.py --app app

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

