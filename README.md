[![pypi](https://img.shields.io/pypi/v/fastapi-voyager.svg)](https://pypi.python.org/pypi/fastapi-voyager)
![Python Versions](https://img.shields.io/pypi/pyversions/fastapi-voyager)
[![PyPI Downloads](https://static.pepy.tech/badge/fastapi-voyager/month)](https://pepy.tech/projects/fastapi-voyager)


# FastAPI Voyager

Visualize your FastAPI endpoints and explore them interactively.

Its vision is to make code easier to read and understand, serving as an ideal documentation tool.

> This repo is still in early stage, it supports Pydantic v2 only.

- **Live Demo**: https://www.newsyeah.fun/voyager/
- **Example Source**: [composition-oriented-development-pattern](https://github.com/allmonday/composition-oriented-development-pattern)

<img width="1597" height="933" alt="fastapi-voyager overview" src="https://github.com/user-attachments/assets/020bf5b2-6c69-44bf-ba1f-39389d388d27" />

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
- [Features](#features)
- [Command Line Usage](#command-line-usage)
- [About pydantic-resolve](#about-pydantic-resolve)
- [Development](#development)
- [Dependencies](#dependencies)
- [Credits](#credits)

## Quick Start

With simple configuration, fastapi-voyager can be embedded into FastAPI:

```python
from fastapi import FastAPI
from fastapi_voyager import create_voyager

app = FastAPI()

app.mount('/voyager',
          create_voyager(
            app,
            module_color={'src.services': 'tomato'},
            module_prefix='src.services',
            swagger_url="/docs",
            ga_id="G-XXXXXXXXVL",
            initial_page_policy='first',
            online_repo_url='https://github.com/allmonday/composition-oriented-development-pattern/blob/master',
            enable_pydantic_resolve_meta=True))
```

Visit `http://localhost:8000/voyager` to explore your API visually.

[View full example](https://github.com/allmonday/composition-oriented-development-pattern/blob/master/src/main.py#L48)

## Installation

### Install via pip

```bash
pip install fastapi-voyager
```

### Install via uv

```bash
uv add fastapi-voyager
```

### Run with CLI

```bash
voyager -m path.to.your.app.module --server
```

For sub-application scenarios (e.g., `app.mount("/api", api)`), specify the app name:

```bash
voyager -m path.to.your.app.module --server --app api
```

> **Note**: [Sub-Application mounts](https://fastapi.tiangolo.com/advanced/sub-applications/) are not supported yet, but you can specify the name of the FastAPI application with `--app`. Only a single application (default: `app`) can be selected.

## Features

fastapi-voyager is designed for scenarios using FastAPI as internal API integration endpoints. It helps visualize dependencies and serves as an architecture tool to identify implementation issues such as wrong relationships, overfetching, and more.

**Best Practice**: When building view models following the ER model pattern, fastapi-voyager can fully realize its potential - quickly identifying which APIs use specific entities and vice versa.

### Highlight Nodes and Links

Click a node to highlight its upstream and downstream nodes. Figure out the related models of one page, or how many pages are related with one model.

<img width="1100" height="700" alt="highlight nodes and dependencies" src="https://github.com/user-attachments/assets/3e0369ea-5fa4-469a-82c1-ed57d407e53d" />

### View Source Code

Double-click a node or route to show source code or open the file in VSCode.

<img width="1297" height="940" alt="view source code" src="https://github.com/user-attachments/assets/c8bb2e7d-b727-42a6-8c9e-64dce297d2d8" />

### Quick Search

Search schemas by name and display their upstream and downstream dependencies. Use `Shift + Click` on any node to quickly search for it.

<img width="1587" height="873" alt="quick search functionality" src="https://github.com/user-attachments/assets/ee4716f3-233d-418f-bc0e-3b214d1498f7" />

### Display ER Diagram

ER diagram is a feature from pydantic-resolve which provides a solid expression for business descriptions. You can visualize application-level entity relationship diagrams.

```python
from pydantic_resolve import ErDiagram, Entity, Relationship

diagram = ErDiagram(
    configs=[
        Entity(
            kls=Team,
            relationships=[
                Relationship(field='id', target_kls=list[Sprint], loader=sprint_loader.team_to_sprint_loader),
                Relationship(field='id', target_kls=list[User], loader=user_loader.team_to_user_loader)
            ]
        ),
        Entity(
            kls=Sprint,
            relationships=[
                Relationship(field='id', target_kls=list[Story], loader=story_loader.sprint_to_story_loader)
            ]
        ),
        Entity(
            kls=Story,
            relationships=[
                Relationship(field='id', target_kls=list[Task], loader=task_loader.story_to_task_loader),
                Relationship(field='owner_id', target_kls=User, loader=user_loader.user_batch_loader)
            ]
        ),
        Entity(
            kls=Task,
            relationships=[
                Relationship(field='owner_id', target_kls=User, loader=user_loader.user_batch_loader)
            ]
        )
    ]
)

# Display in voyager
app.mount('/voyager',
          create_voyager(
            app,
            er_diagram=diagram
          ))
```

<img width="1276" height="613" alt="ER diagram visualization" src="https://github.com/user-attachments/assets/ea0091bb-ee11-4f71-8be3-7129d956c910" />

### Show Pydantic Resolve Meta Info

Set `enable_pydantic_resolve_meta=True` in `create_voyager`, then toggle the "pydantic resolve meta" button to visualize resolve/post/expose/collect operations.

<img width="1604" height="535" alt="pydantic resolve meta information" src="https://github.com/user-attachments/assets/d1639555-af41-4a08-9970-4b8ef314596a" />

## Command Line Usage

### Start Server

```bash
# Open in browser (default port 8000)
voyager -m tests.demo --server

# Custom port
voyager -m tests.demo --server --port=8002

# Specify app name
voyager -m tests.demo --server --app my_app
```

### Generate DOT File

```bash
# Generate .dot file
voyager -m tests.demo

# Specify app
voyager -m tests.demo --app my_app

# Filter by schema
voyager -m tests.demo --schema Task

# Show all fields
voyager -m tests.demo --show_fields all

# Custom module colors
voyager -m tests.demo --module_color=tests.demo:red --module_color=tests.service:tomato

# Output to file
voyager -m tests.demo -o my_visualization.dot

# Version and help
voyager --version
voyager --help
```

## About pydantic-resolve

pydantic-resolve is a lightweight tool designed to build complex, nested data in a simple, declarative way. In v2, it introduced an important feature: **ER Diagram**, and fastapi-voyager has supported this feature, allowing for a clearer understanding of business relationships.

The ~~`@ensure_subset` decorator~~ `DefineSubset` metaclass helps safely pick fields from the 'source class' while **indicating the reference** from the current class to the base class.

Developers can use fastapi-voyager without needing to know anything about pydantic-resolve, but I still highly recommend everyone to give it a try.

## Development

### Setup Development Environment

```bash
# Fork and clone the repository
git clone https://github.com/your-username/fastapi-voyager.git
cd fastapi-voyager

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install ".[dev]"

# Run development server
uvicorn tests.programatic:app --reload
```

Visit `http://localhost:8000/voyager` to see changes.

### Setup Git Hooks (Optional)

Enable automatic code formatting before commits:

```bash
./setup-hooks.sh
# or manually:
git config core.hooksPath .githooks
```

This will run Prettier automatically before each commit. See [`.githooks/README.md`](./.githooks/README.md) for details.

### Project Structure

**Frontend:**
- `src/fastapi_voyager/web/vue-main.js` - Main JavaScript entry

**Backend:**
- `voyager.py` - Main entry point
- `render.py` - Generate DOT files
- `server.py` - Server mode

## Roadmap

- [Ideas](./docs/idea.md)
- [Changelog & Roadmap](./docs/changelog.md)

## Dependencies

- [FastAPI](https://fastapi.tiangolo.com/)
- [pydantic-resolve](https://github.com/allmonday/pydantic-resolve)
- [Quasar Framework](https://quasar.dev/)

## Credits

- [graphql-voyager](https://apis.guru/graphql-voyager/) - Thanks for inspiration
- [vscode-interactive-graphviz](https://github.com/tintinweb/vscode-interactive-graphviz) - Thanks for web visualization

## License

MIT License
