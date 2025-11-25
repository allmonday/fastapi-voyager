# How to develop & contribute?

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
