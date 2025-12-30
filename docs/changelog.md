# Changelog & plan

## <0.9:
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

## 0.9
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

## 0.10
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
    

## 0.11
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
    - [x] change jquery cdn
- 0.11.6
    - [x] flag of loading full graph in first render or not
    - [x] optimize loading static resource 
- 0.11.7
    - [x] fix swagger link
- 0.11.8
    - [x] fix swagger link in another way
- 0.11.9
    - [x] replace issubclass with safe_issubclass to prevent exception.
- 0.11.10
    - [x] fix bug during updating forward refs
- 0.11.11
    - [x] replace print with logging and add `--log-level` in cli, by default info
    - [x] fill node title color with module color
    - [x] optimize cluster render logic

## 0.12
- 0.12.1
    - [x] sort tag / route names in left panel
    - [x] display schema name on top of detail panel
    - [x] optimize dbclick style
    - [x] persist the tag/ route in url
- 0.12.2
    - [x] add google analytics
- 0.12.3
    - [x] fix bug in `update_forward_refs`, class should not be skipped if it's parent class has been visited.
- 0.12.4
    - [x] fix logger exception 
- 0.12.5
    - [x] fix nested cluster with same color
    - [x] refactor fe with store based on reactive
    - [x] fix duplicated focus toggle
- 0.12.6
    - [x] fix overlapped edges
    - [x] click link(edge) to highlight related nodes
    - [x] on hover cursor effect
- 0.12.7
    - [x] remove search component, integrated into main page
- 0.12.8
    - [x] optimize ui elements, change icons, update reset behavior
- 0.12.9
    - [x] fix: handle logging exception for forward ref info, preventing crash
- 0.12.10
    - [x] fix: double trigger on reset search
- 0.12.11
    - [x] better ui for schema select
    - [x] fix: pick tag and then pick route directly from another tag will render nothing
    - [x] feat: cancel search schema triggered by shift click will redirect back to previous tag, route selection
    - [x] optimize the node style
- 0.12.12
    - [x] disable `show module cluster` by default

## 0.13
- 0.13.0
    - [x] if er diagram is provided, show it first.
- 0.13.1
    - [x] show more details in er diagram
- 0.13.2
    - [x] show dashed line for link without dataloader
- 0.13.3
    - [x] show field description

## 0.14, integration with pydantic-resolve
- 0.14.0
    - [x] show hint for resolve (>), post fields (<), post default handler (* at title)
    - [x] show expose and collect info
- 0.14.1
    - [x] minor ui enhancement

## 0.15, internal refactor
- 0.15.0
    - [ ] left panel can be toggled.
    - [ ] refactor vue-main.js, move methods to store
    - [ ] refactor render.py
    - [ ] add tests

## 1.0, release 


