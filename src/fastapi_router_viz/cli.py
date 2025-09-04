"""Command line interface for fastapi-router-viz."""
import argparse
import sys
import importlib.util
import os
from typing import Optional

from fastapi import FastAPI
from fastapi_router_viz.graph import Analytics
from fastapi_router_viz.version import __version__


def load_fastapi_app(module_path: str, app_name: str = "app") -> Optional[FastAPI]:
    """Load FastAPI app from a Python module."""
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


def generate_visualization(app: FastAPI, output_file: str = "router_viz.dot"):
    """Generate DOT file for FastAPI router visualization."""
    analytics = Analytics()
    analytics.analysis(app)
    
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
  router-viz main.py --app main_app    # Load 'main_app' from main.py
  router-viz app.py -o my_graph.dot    # Output to my_graph.dot
        """
    )
    
    parser.add_argument(
        "module",
        help="Python file containing the FastAPI application"
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
    
    args = parser.parse_args()
    
    # Check if the module file exists
    if not os.path.exists(args.module):
        print(f"Error: File '{args.module}' not found")
        sys.exit(1)
    
    # Load FastAPI app
    app = load_fastapi_app(args.module, args.app)
    if app is None:
        sys.exit(1)
    
    # Generate visualization
    try:
        generate_visualization(app, args.output)
    except Exception as e:
        print(f"Error generating visualization: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
