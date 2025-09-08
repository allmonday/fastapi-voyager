"""Command line interface for fastapi-router-viz."""
import argparse
import sys
import importlib.util
import importlib
import os
from typing import Optional

from fastapi import FastAPI
from fastapi_router_viz.graph import Analytics
from fastapi_router_viz.version import __version__


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
        # 临时将当前工作目录添加到 Python 路径中
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
            # 清理：如果我们添加了路径，则移除它
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
        model_prefixs: list[str] | None = None,
        schema: str | None = None,
        show_fields: bool = False):

    """Generate DOT file for FastAPI router visualization."""
    analytics = Analytics(model_prefixs=model_prefixs, schema=schema, show_fields=show_fields)
    analytics.analysis(app, include_tags=tags)
    
    dot_content = analytics.generate_dot()
    
    # Write to file
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
  router-viz app.py                    # Load 'app' from app.py
  router-viz -m demo                   # Load 'app' from demo module
  router-viz main.py --app main_app    # Load 'main_app' from main.py
  router-viz -m mypackage.main --app my_app  # Load 'my_app' from mypackage.main
  router-viz app.py -o my_graph.dot    # Output to my_graph.dot
        """
    )
    
    # Create mutually exclusive group for module loading options
    group = parser.add_mutually_exclusive_group(required=True)
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
        "--version", "-v",
        action="version",
        version=f"fastapi-router-viz {__version__}"
    )
    parser.add_argument(
        "--tags",
        nargs="+",
        help="Only include routes whose first tag is in the provided list"
    )
    parser.add_argument(
        "--model_prefixs",
        nargs="+",
        help="Filter schemas belongs to model entities"
    )
    parser.add_argument(
        "--schema",
        default=None,
        help="Filter schemas by name"
    )
    parser.add_argument(
        "--show_fields",
        action="store_true",
        help="Include field details in the visualization"
    )

    
    
    args = parser.parse_args()
    
    # Load FastAPI app based on the input method
    if args.module_name:
        # Load from module name
        app = load_fastapi_app_from_module(args.module_name, args.app)
    else:
        # Load from file path
        if not os.path.exists(args.module):
            print(f"Error: File '{args.module}' not found")
            sys.exit(1)
        app = load_fastapi_app_from_file(args.module, args.app)
    
    if app is None:
        sys.exit(1)
    
    # Generate visualization
    print(args.tags)
    try:
        generate_visualization(
            app, 
            args.output, 
            tags=args.tags, 
            model_prefixs=args.model_prefixs,
            schema=args.schema,
            show_fields=args.show_fields  # Pass the new argument
        )
    except Exception as e:
        print(f"Error generating visualization: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
