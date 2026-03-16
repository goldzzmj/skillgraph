"""
Fix Matplotlib and Numpy Dependencies

Fix matplotlib and numpy version compatibility.
"""

import subprocess
import sys
import os

def check_and_upgrade_pip():
    """Check and upgrade pip packages."""
    print("=" * 60)
    print("Checking and Upgrading Pip Packages")
    print("=" * 60)
    
    # Current versions
    try:
        import numpy
        print(f"Current NumPy: {numpy.__version__}")
    except ImportError:
        print("NumPy: Not installed")
    
    try:
        import matplotlib
        print(f"Current Matplotlib: {matplotlib.__version__}")
    except ImportError:
        print("Matplotlib: Not installed")
    
    # Upgrade pip
    print("\n[1] Upgrading pip...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    # Install/upgrade required packages
    print("\n[2] Installing required packages...")
    packages = [
        "numpy>=1.23.0",
        "matplotlib>=3.5.0",
        "networkx>=2.8.0",
        "pygraphviz>=0.20.0"
    ]
    
    for package in packages:
        print(f"   Installing {package}...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", package], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✓ {package} installed successfully")
        else:
            print(f"   ✗ {package} failed to install")
            print(f"   Error: {result.stderr}")
    
    # Verify installations
    print("\n[3] Verifying installations...")
    
    try:
        import numpy
        print(f"   ✓ NumPy {numpy.__version__} installed")
    except Exception as e:
        print(f"   ✗ NumPy failed: {e}")
    
    try:
        import matplotlib
        print(f"   ✓ Matplotlib {matplotlib.__version__} installed")
    except Exception as e:
        print(f"   ✗ Matplotlib failed: {e}")
    
    try:
        import networkx
        print(f"   ✓ NetworkX {networkx.__version__} installed")
    except Exception as e:
        print(f"   ✗ NetworkX failed: {e}")
    
    try:
        import pygraphviz
        print(f"   ✓ PyGraphviz {pygraphviz.__version__} installed")
    except Exception as e:
        print(f"   ✗ PyGraphviz failed: {e}")
    
    print("\n" + "=" * 60)
    print("Package Installation Complete!")
    print("=" * 60)
    
    # Now try to import the visualization module
    print("\n[4] Testing visualization module...")
    try:
        # Add tests directory to path
        tests_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, tests_dir)
        
        # Import the visualization module
        from visualise_graph import load_graph_data, visualize_graph, create_test_graph, generate_test_entities, generate_test_operations, generate_test_edges, create_graphviz_graph
        
        print("   ✓ Visualization module imported successfully")
        
        # Test the functions
        print("\n[5] Testing graph data generation...")
        graph_data = generate_test_graph()
        print(f"   ✓ Generated test graph with {len(graph_data['entities'])} entities and {len(graph_data['operations'])} operations")
        
        print("\n[6] Testing graph visualization...")
        visualize_graph(graph_data, output_path='output/test_graph_visualization_fixed.png')
        print("   ✓ Graph visualization saved")
        
        print("\n" + "=" * 60)
        print("All Tests Passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"   ✗ Visualization module test failed: {e}")
        import traceback
        traceback.print_exc()
    
    return True


if __name__ == "__main__":
    success = check_and_upgrade_pip()
    sys.exit(0 if success else 1)
