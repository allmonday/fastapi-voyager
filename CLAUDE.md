# CLAUDE.md - fastapi-voyager

## 项目概述

FastAPI Voyager 是一个 Python 包，提供 API 路由树和依赖关系的可视化。前端使用 Vue 3 + Naive UI，通过 Vite 构建。

## 前端构建

前端源码位于 `src/fastapi_voyager/web/`，构建产物为 `src/fastapi_voyager/web/dist/`。

```bash
# 安装依赖（首次或 package.json 变更后）
. "$HOME/.nvm/nvm.sh" && nvm use 20
npm --prefix src/fastapi_voyager/web install

# 构建（修改前端代码后执行）
npm --prefix src/fastapi_voyager/web run build
```

构建产物 `dist/` 已在 `.gitignore` 中，通过 `pyproject.toml` 的 `force-include` 在 CI 打包时包含。

## 开发模式

```bash
# 终端 1：启动 Python 后端（任选一个 demo app）
uv run uvicorn demo_app:app --port 8000
# 或
. .venv/bin/activate && uvicorn demo_app:app --port 8000

# 终端 2（可选）：Vite dev server，支持 HMR
cd src/fastapi_voyager/web && npm run dev
# 浏览器打开 http://localhost:5173，API 请求自动代理到 localhost:8000
```

不启动 Vite dev server 时，直接访问 http://localhost:8000/voyager/ 即可使用构建后的版本。

## 关键文件

| 路径 | 说明 |
|------|------|
| `src/fastapi_voyager/web/src/App.vue` | 主组件（Naive UI） |
| `src/fastapi_voyager/web/src/store.js` | 前端状态管理 |
| `src/fastapi_voyager/web/src/main.js` | Vue 入口 |
| `src/fastapi_voyager/web/src/component/*.vue` | 子组件 |
| `src/fastapi_voyager/web/src/graph-ui.js` | D3 Graphviz 渲染 |
| `src/fastapi_voyager/web/src/magnifying-glass.js` | 放大镜功能 |
| `src/fastapi_voyager/web/index.html` | Vite 入口模板（含 Python 占位符） |
| `src/fastapi_voyager/web/vite.config.js` | Vite 配置 |
| `src/fastapi_voyager/adapters/common.py` | Python 端读取 dist/index.html 并替换占位符 |
| `pyproject.toml` | 含 force-include 配置 |
| `.github/workflows/publish.yml` | CI 含 Node.js 构建步骤 |

## Python 占位符

`dist/index.html` 中的占位符由 Python 在 serve 时替换：
- `<!-- STATIC_PATH -->` → 静态文件路径
- `<!-- VERSION_PLACEHOLDER -->` → 版本号
- `<!-- THEME_COLOR -->` → 框架主题色
- `<!-- GA_SNIPPET -->` → Google Analytics 代码
