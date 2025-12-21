# Idea

## backlog
- [ ] user can generate nodes/edges manually and connect to generated ones
    - [ ] eg: add owner
    - [ ] add extra info for schema
- [ ] optimize static resource (allow manually config url)
- [ ] improve search dialog
    - [ ] add route/tag list
- [ ] type alias should not be kept as node instead of compiling to original type
- [ ] how to correctly handle the generic type ?
    - for example `Page[Student]` of `Page[T]` will be marked in `Page[T]`'s module
- [ ] sort field name in nodes (only table inside right panel)
- [ ] set max limit for fields in nodes (? need further thinking)
- [ ] minimap (good to have)
    - ref: https://observablehq.com/@rabelais/d3-js-zoom-minimap
- [ ] ~~debug mode~~
    - [ ] export dot content, load dot content
- [ ] abstract voyager-core
    - [ ] support fastapi-voyager
    - [ ] support django-ninja-voyager


## in analysis
- [ ] upgrade network algorithm (optional, for example networkx)
- [ ] click field to highlight links or click link to highlight related nodes
- [ ] animation effect for edges
- [ ] display standard ER diagram spec. `hard but important`
    - [ ] display potential invalid links
    - [ ] highlight relationship belongs to ER diagram
