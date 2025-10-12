"""Command line interface for fastapi-voyager."""
import argparse
import sys
import importlib.util
import importlib
import os
from typing import Optional

from fastapi import FastAPI
from fastapi_voyager.voyager import Voyager
from fastapi_voyager.version import __version__
from fastapi_voyager import server as viz_server


def load_fastapi_app_from_file(module_path: str, app_name: str = "app") -> Optional[FastAPI]:
    """Load FastAPI app from a Python module file."""
    try:
        # Convert relative path to absolute path
        if not os.path.isabs(module_path):
            module_path = os.path.abspath(module_path)
        
        # Load the module
        spec = importlib.util.spec_from_file_location("app_module", module_path)
        if spec is None or spec.loader is None:
            print(f"Error: Could not load module from {module_path}")
            return None
            
        module = importlib.util.module_from_spec(spec)
        sys.modules["app_module"] = module
        spec.loader.exec_module(module)
        
        # Get the FastAPI app instance
        if hasattr(module, app_name):
            app = getattr(module, app_name)
            if isinstance(app, FastAPI):
                return app
            else:
                print(f"Error: '{app_name}' is not a FastAPI instance")
                return None
        else:
            print(f"Error: No attribute '{app_name}' found in the module")
            return None
            
    except Exception as e:
        print(f"Error loading FastAPI app: {e}")
        return None


def load_fastapi_app_from_module(module_name: str, app_name: str = "app") -> Optional[FastAPI]:
    """Load FastAPI app from a Python module name."""
    try:
        # Temporarily add the current working directory to sys.path
        current_dir = os.getcwd()
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
            path_added = True
        else:
            path_added = False
        
        try:
            # Import the module by name
            module = importlib.import_module(module_name)
            
            # Get the FastAPI app instance
            if hasattr(module, app_name):
                app = getattr(module, app_name)
                if isinstance(app, FastAPI):
                    return app
                else:
                    print(f"Error: '{app_name}' is not a FastAPI instance")
                    return None
            else:
                print(f"Error: No attribute '{app_name}' found in module '{module_name}'")
                return None
        finally:
            # Cleanup: if we added the path, remove it
            if path_added and current_dir in sys.path:
                sys.path.remove(current_dir)
            
    except ImportError as e:
        print(f"Error: Could not import module '{module_name}': {e}")
        return None
    except Exception as e:
        print(f"Error loading FastAPI app from module '{module_name}': {e}")
        return None


def generate_visualization(
    app: FastAPI,
    output_file: str = "router_viz.dot", tags: list[str] | None = None,
    schema: str | None = None,
    show_fields: bool = False,
    module_color: dict[str, str] | None = None,
    route_name: str | None = None,
):

    """Generate DOT file for FastAPI router visualization."""
    analytics = Voyager(
        include_tags=tags,
        schema=schema,
        show_fields=show_fields,
        module_color=module_color,
        route_name=route_name,
    )

    analytics.analysis(app)

    dot_content = analytics.render_dot()
    
    # Optionally write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(dot_content)
    print(f"DOT file generated: {output_file}")
    print("To render the graph, use: dot -Tpng router_viz.dot -o router_viz.png")
    print("Or view online: https://dreampuf.github.io/GraphvizOnline/")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Visualize FastAPI application's routing tree and dependencies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  voyager app.py                                                             # Load 'app' from app.py
  voyager -m tests.demo                                                      # Load 'app' from demo module
  voyager -m tests.demo --app=app                                            # Load 'app' from tests.demo
  voyager -m tests.demo --schema=NodeA                                       # [str] filter nodes by schema name
  voyager -m tests.demo --tags=page restful                                  # list[str] filter nodes route's tags
  voyager -m tests.demo --module_color=tests.demo:red --module_color=tests.service:yellow  # list[str] filter nodes route's tags
  voyager -m tests.demo -o my_graph.dot                                      # Output to my_graph.dot
  voyager -m tests.demo --server                                             # start a local server to preview
  voyager -m tests.demo --server --port=8001                                 # start a local server to preview
"""
    )
    
    # Create mutually exclusive group for module loading options
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        "module",
        nargs="?",
        help="Python file containing the FastAPI application"
    )
    group.add_argument(
        "-m", "--module",
        dest="module_name",
        help="Python module name containing the FastAPI application (like python -m)"
    )
    
    parser.add_argument(
        "--app", "-a",
        default="app",
        help="Name of the FastAPI app variable (default: app)"
    )
    
    parser.add_argument(
        "--output", "-o",
        default="router_viz.dot",
        help="Output DOT file name (default: router_viz.dot)"
    )
    parser.add_argument(
        "--server",
        action="store_true",
        help="Start a local server to preview the generated DOT graph"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for the preview server when --server is used (default: 8000)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host/IP for the preview server when --server is used (default: 127.0.0.1). Use 0.0.0.0 to listen on all interfaces."
    )
    parser.add_argument(
        "--module_prefix",
        type=str,
        default=None,
        help="Prefix routes with module name when rendering brief view (only valid with --server)"
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"fastapi-voyager {__version__}"
    )
    parser.add_argument(
        "--tags",
        nargs="+",
        help="Only include routes whose first tag is in the provided list"
    )
    parser.add_argument(
        "--module_color",
        action="append",
        metavar="KEY:VALUE",
        help="Module color mapping as key1:value1 key2:value2 (module name to Graphviz color)"
    )
    # removed service_prefixes option
    parser.add_argument(
        "--schema",
        default=None,
        help="Filter schemas by name"
    )
    parser.add_argument(
        "--show_fields",
        choices=["single", "object", "all"],
        default="object",
        help="Field display mode: single (no fields), object (only object-like fields), all (all fields). Default: object"
    )
    parser.add_argument(
        "--route_name",
        type=str,
        default=None,
        help="Filter by route id (format: <endpoint>_<path with _>)"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run built-in demo (equivalent to: --module tests.demo --server --module_color=tests.service:blue --module_color=tests.demo:tomato)"
    )
    
    args = parser.parse_args()
    
    # Handle demo mode: override module_name and defaults
    if args.demo:
        # Force module loading path
        args.module_name = "tests.demo"
        # Ensure server mode on
        args.server = True
        # Inject default module colors if absent / merge
        demo_defaults = ["tests.service:blue", "tests.demo:tomato"]
        existing = set(args.module_color or [])
        for d in demo_defaults:
            # only add if same key not already provided
            key = d.split(":", 1)[0]
            if not any(mc.startswith(key + ":") for mc in existing):
                args.module_color = (args.module_color or []) + [d]

    if args.module_prefix and not args.server:
        parser.error("--module_prefix can only be used together with --server")

    # Validate required target if not demo
    if not args.demo and not (args.module_name or args.module):
        parser.error("You must provide a module file, -m module name, or use --demo")

    # Load FastAPI app based on the input method (module_name takes precedence)
    if args.module_name:
        app = load_fastapi_app_from_module(args.module_name, args.app)
    else:
        if not os.path.exists(args.module):
            print(f"Error: File '{args.module}' not found")
            sys.exit(1)
        app = load_fastapi_app_from_file(args.module, args.app)
    
    if app is None:
        sys.exit(1)
    
    # helper: parse KEY:VALUE pairs into dict
    def parse_kv_pairs(pairs: list[str] | None) -> dict[str, str] | None:
        if not pairs:
            return None
        result: dict[str, str] = {}
        for item in pairs:
            if ":" in item:
                k, v = item.split(":", 1)
                k = k.strip()
                v = v.strip()
                if k:
                    result[k] = v
        return result or None

    try:
        module_color = parse_kv_pairs(args.module_color)
        if args.server:
            # Build a preview server which computes DOT via Analytics using closure state
            try:
                import uvicorn
            except ImportError:
                print("Error: uvicorn is required to run the server. Install via 'pip install uvicorn' or 'uv add uvicorn'.")
                sys.exit(1)
            app_server = viz_server.create_app_with_fastapi(
                app,
                module_color=module_color,
                module_prefix=args.module_prefix,
            )
            print(f"Starting preview server at http://{args.host}:{args.port} ... (Ctrl+C to stop)")
            uvicorn.run(app_server, host=args.host, port=args.port)
        else:
            # Generate and write dot file locally
            generate_visualization(
                app, 
                args.output, 
                tags=args.tags, 
                schema=args.schema,
                show_fields=args.show_fields,
                module_color=module_color,
                route_name=args.route_name,
            )
    except Exception as e:
        print(f"Error generating visualization: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
