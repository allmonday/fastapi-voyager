import inspect

import pydantic_resolve.constant as const
from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_resolve.utils.collector import ICollector, SendToInfo
from pydantic_resolve.utils.er_diagram import LoaderInfo
from pydantic_resolve.utils.expose import ExposeInfo


def analysis_pydantic_resolve_fields(schema: type[BaseModel], field: str):
    """
    get information for pydantic resolve specific info
    in future, this function will be provide by pydantic-resolve package

    is_resolve: bool = False
    - check existence of def resolve_{field} method
    - check existence of LoaderInfo in field.metadata

    is_post: bool = False
    - check existence of def post_{field} method

    expose_as_info: str | None = None
    - check ExposeInfo in field.metadata
    - check field in schema.__pydantic_resolve_expose__ (const.EXPOSE_TO_DESCENDANT)

    send_to_info: list[str] | None = None
    - check SendToInfo in field.metadata
    - check field in schema.__pydantic_resolve_collect__ (const.COLLECTOR_CONFIGURATION)

    collect_info: list[str] | None = None
    - 1. check existence of def post_{field} method
    - 2. get the signature of this method
    - 3. extrace the collector names from the parameters with ICollector metadata
    


    return dict in form of 
    {
        "is_resolve": True,
        ...
    }
    """
    has_meta = False
    field_info: FieldInfo = schema.model_fields.get(field)
    
    is_resolve = hasattr(schema, f'{const.RESOLVE_PREFIX}{field}')
    is_post = hasattr(schema, f'{const.POST_PREFIX}{field}')
    expose_as_info = None
    send_to_info = None
    post_collector = []

    send_to_info_list = []

    if field_info:
        # Check metadata
        for meta in field_info.metadata:
            if isinstance(meta, LoaderInfo):
                is_resolve = True
            if isinstance(meta, ExposeInfo):
                expose_as_info = meta.alias
            if isinstance(meta, SendToInfo):
                if isinstance(meta.collector_name, str):
                    send_to_info_list.append(meta.collector_name)
                else:
                    send_to_info_list.extend(list(meta.collector_name))

    # Check class attributes
    expose_dict = getattr(schema, const.EXPOSE_TO_DESCENDANT, {})
    if field in expose_dict:
        expose_as_info = expose_dict[field]

    collect_dict = getattr(schema, const.COLLECTOR_CONFIGURATION, {})

    for keys, collectors in collect_dict.items():
        target_keys = [keys] if isinstance(keys, str) else list(keys)
        if field in target_keys:
            if isinstance(collectors, str):
                send_to_info_list.append(collectors)
            else:
                send_to_info_list.extend(list(collectors))
    
    if send_to_info_list:
        send_to_info = list(set(send_to_info_list))  # unique collectors
    
    if is_post:
        post_method = getattr(schema, f'{const.POST_PREFIX}{field}')
        for _, param in inspect.signature(post_method).parameters.items():
            if isinstance(param.default, ICollector):
                post_collector.append(param.default.alias)
    
    has_meta = any([is_resolve, is_post, expose_as_info, send_to_info])

    return {
        "has_pydantic_resolve_meta": has_meta,
        "is_resolve": is_resolve,
        "is_post": is_post,
        "expose_as_info": expose_as_info,
        "send_to_info": send_to_info,
        "collect_info": None if len(post_collector) == 0 else post_collector
    }


def extract_query_mutation_methods(entity: type) -> tuple[list[dict], list[dict]]:
    """
    Extract all @query and @mutation decorated methods from an Entity.

    Returns:
        A tuple of (queries, mutations), each is a list of dicts:
        - name: GraphQL name (from decorator or method name)
        - return_type: Return type annotation as string

    Each list is sorted alphabetically by name.
    """
    # Lazy import to avoid circular dependency
    from fastapi_voyager.type_helper import get_type_name

    queries = []
    mutations = []

    for name, method in entity.__dict__.items():
        # Handle classmethod - access underlying function
        actual_method = method
        if isinstance(method, classmethod):
            actual_method = method.__func__

        is_query = hasattr(actual_method, '_pydantic_resolve_query')
        is_mutation = hasattr(actual_method, '_pydantic_resolve_mutation')

        if is_query or is_mutation:
            # Get GraphQL name
            if is_query:
                gql_name = getattr(actual_method, '_pydantic_resolve_query_name', None)
            else:
                gql_name = getattr(actual_method, '_pydantic_resolve_mutation_name', None)

            # Use method name if no GraphQL name specified
            display_name = gql_name or name

            # Get return type from signature
            return_type = 'Unknown'
            try:
                sig = inspect.signature(actual_method)
                if sig.return_annotation != inspect.Signature.empty:
                    return_type = get_type_name(sig.return_annotation)
            except Exception:
                pass

            method_info = {
                'name': display_name,
                'return_type': return_type
            }

            if is_query:
                queries.append(method_info)
            else:
                mutations.append(method_info)

    # Sort each list alphabetically by name
    queries.sort(key=lambda m: m['name'])
    mutations.sort(key=lambda m: m['name'])

    return queries, mutations
