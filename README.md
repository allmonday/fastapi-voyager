[![pypi](https://img.shields.io/pypi/v/fastapi-voyager.svg)](https://pypi.python.org/pypi/fastapi-voyager)
![Python Versions](https://img.shields.io/pypi/pyversions/fastapi-voyager)
[![PyPI Downloads](https://static.pepy.tech/badge/fastapi-voyager/month)](https://pepy.tech/projects/fastapi-voyager)


Visualize your FastAPI endpoints, and explore them interactively.

Its vision is to make code easier to read and understand, serving as an ideal documentation tool.

> This repo is still in early stage, it supports pydantic v2 only

visit [live demo](https://www.newsyeah.fun/voyager/) 
source code:[composition oriented development pattern](https://github.com/allmonday/composition-oriented-development-pattern)

<img width="1597" height="933" alt="image" src="https://github.com/user-attachments/assets/020bf5b2-6c69-44bf-ba1f-39389d388d27" />

with simple configuration it can be embedded into FastAPI.

```python
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

https://github.com/allmonday/composition-oriented-development-pattern/blob/master/src/main.py#L48

## Plan & Raodmap
- [ideas](./docs/idea.md)
- [changelog & roadmap](./docs/changelog.md)

## Installation

```bash
pip install fastapi-voyager
# or
uv add fastapi-voyager
```

run with cli:

```shell
voyager -m path.to.your.app.module --server
```

> [Sub-Application mounts](https://fastapi.tiangolo.com/advanced/sub-applications/) are not supported yet, but you can specify the name of the FastAPI application used with `--app`. Only a single application (default: 'app') can be selected, but in a scenario where `api` is attached through `app.mount("/api", api)`, you can select `api` like this:

```shell
voyager -m path.to.your.app.module --server --app api
```


## Features

For scenarios of using FastAPI as internal API integration endpoints, `fastapi-voyager` helps to visualize the dependencies.

It is also an architecture tool that can identify issues inside implementation, finding out wrong relationships, overfetchs, or anything else.

**If the process of building the view model follows the ER model**, the full potential of fastapi-voyager can be realized. It allows for quick identification of APIs  that use entities, as well as which entities are used by a specific API

Given ErDiagram defined by pydantic-resolve, application level entity relationship diagram can be visualized too.


### highlight nodes and links
click a node to highlight it's upperstream and downstream nodes. figure out the related models of one page, or homw many pages are related with one model.

<img width="1100" height="700" alt="image" src="https://github.com/user-attachments/assets/3e0369ea-5fa4-469a-82c1-ed57d407e53d" />

### view source code

double click a node or route to show source code or open file in vscode.

<img width="1297" height="940" alt="image" src="https://github.com/user-attachments/assets/c8bb2e7d-b727-42a6-8c9e-64dce297d2d8" />

### quick search

seach schemas by name and dispaly it's upstream and downstreams.

shift + click can quickly search current one

<img width="1587" height="873" alt="image" src="https://github.com/user-attachments/assets/ee4716f3-233d-418f-bc0e-3b214d1498f7" />

### display ER diagram

ER diagram is a new feature from pydantic-resolve which provide a solid expression for business descritpions. 

```python
diagram = ErDiagram(
    configs=[
        Entity(
            kls=Team,
            relationships=[
                Relationship( field='id', target_kls=list[Sprint], loader=sprint_loader.team_to_sprint_loader),
                Relationship( field='id', target_kls=list[User], loader=user_loader.team_to_user_loader)
            ]
        ),
        Entity(
            kls=Sprint,
            relationships=[
                Relationship( field='id', target_kls=list[Story], loader=story_loader.sprint_to_story_loader)
            ]
        ),
        Entity(
            kls=Story,
            relationships=[
                Relationship( field='id', target_kls=list[Task], loader=task_loader.story_to_task_loader),
                Relationship( field='owner_id', target_kls=User, loader=user_loader.user_batch_loader)
            ]
        ),
        Entity(
            kls=Task,
            relationships=[
                Relationship( field='owner_id', target_kls=User, loader=user_loader.user_batch_loader)
            ]
        )
    ]
)

# display in voyager
app.mount('/voyager', 
          create_voyager(
            app,
            er_diagram=diagram)
```

<img width="1276" height="613" alt="image" src="https://github.com/user-attachments/assets/ea0091bb-ee11-4f71-8be3-7129d956c910" />

### Show pydantic resolve meta info

setting `enable_pydantic_resolve_meta=True` in `create_voyager`, toggle `pydantic resolve meta`. 

<img width="1604" height="535" alt="image" src="https://github.com/user-attachments/assets/d1639555-af41-4a08-9970-4b8ef314596a" />


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

## About pydantic-resolve

pydantic-resolve is a lightweight tool designed to build complex, nested data in a simple, declarative way. In v2 it introduced an important feature: ER Diagram, and fastapi-voyager has supported this feature, allowing for a clearer understanding of the business relationships.

pydantic-resolve's ~~`@ensure_subset` decorator~~ `DefineSubset` metaclass helps safely pick fields from the 'source class' while **indicating the reference** from the current class to the base class.

Developers can use fastapi-voyager without needing to know anything about pydantic-resolve, but I still highly recommend everyone to give it a try.

## Dependencies

- FastAPI
- [pydantic-resolve](https://github.com/allmonday/pydantic-resolve)
- Quasar


## Credits

- https://apis.guru/graphql-voyager/, thanks for inspiration.
- https://github.com/tintinweb/vscode-interactive-graphviz, thanks for web visualization.


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


frontend: 
- `src/web/vue-main.js`: main js

backend: 
- `voyager.py`: main entry
- `render.py`: generate dot file
- `server.py`: serve mode
