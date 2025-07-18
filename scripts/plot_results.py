#!/usr/bin/env python3

"""
Optional plotting script for students who want to create visual charts.
This script generates plots from gem5 simulation results.

Note: This requires matplotlib. If not available, use analyze_results.py for tabular output.
"""

import os
import sys
import argparse
import re
from collections import defaultdict

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

def parse_stats_file(filepath):
    """Parse gem5 stats.txt file and extract relevant metrics"""
    stats = {}
    
    if not os.path.exists(filepath):
        print(f"Warning: Stats file not found: {filepath}")
        return stats
    
    try:
        with open(filepath, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip comments and empty lines
                if line.startswith('#') or not line:
                    continue
                
                # Parse stat lines (format: stat_name value # comment)
                parts = line.split()
                if len(parts) >= 2:
                    stat_name = parts[0]
                    stat_value = parts[1]
                    
                    # Convert to float if possible
                    try:
                        stats[stat_name] = float(stat_value)
                    except ValueError:
                        stats[stat_name] = stat_value
                        
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
    
    return stats

def extract_config_from_path(result_path):
    """Extract configuration parameters from result path"""
    config = {}
    
    # Try to extract from directory name
    dirname = os.path.basename(result_path)
    
    # Look for cache size patterns (e.g., "8kB", "32kB", "128kB")
    cache_size_match = re.search(r'(\d+)[kK][bB]', dirname)
    if cache_size_match:
        config['cache_size'] = cache_size_match.group(0)
        config['cache_size_kb'] = int(cache_size_match.group(1))
    
    # Look for associativity patterns (e.g., "assoc2", "assoc4")
    assoc_match = re.search(r'assoc(\d+)', dirname)
    if assoc_match:
        config['associativity'] = int(assoc_match.group(1))
    
    # Extract application name from path
    path_parts = result_path.split('/')
    for part in path_parts:
        if any(app in part for app in ['matrix_mult', 'image_blur', 'hash_ops', 'stream_bench']):
            config['application'] = part
            break
    
    return config

def collect_results(results_dir):
    """Collect all simulation results from directory structure"""
    results = []
    
    if not os.path.exists(results_dir):
        print(f"Results directory not found: {results_dir}")
        return results
    
    # Walk through all subdirectories
    for root, dirs, files in os.walk(results_dir):
        if 'stats.txt' in files:
            stats_path = os.path.join(root, 'stats.txt')
            stats = parse_stats_file(stats_path)
            
            if stats:
                config = extract_config_from_path(root)
                result = {
                    'path': root,
                    'stats': stats,
                    'config': config
                }
                results.append(result)
    
    return results

def calculate_ipc(stats):
    """Calculate IPC from stats"""
    if 'sim_insts' in stats and 'sim_ticks' in stats:
        if stats['sim_ticks'] > 0:
            return stats['sim_insts'] / stats['sim_ticks']
    return 0

def calculate_miss_rate(stats, cache_type='l1d'):
    """Calculate cache miss rate"""
    if cache_type == 'l1d':
        misses_key = 'system.cpu.dcache.overall_misses::total'
        accesses_key = 'system.cpu.dcache.overall_accesses::total'
    elif cache_type == 'l1i':
        misses_key = 'system.cpu.icache.overall_misses::total'
        accesses_key = 'system.cpu.icache.overall_accesses::total'
    elif cache_type == 'l2':
        misses_key = 'system.l2cache.overall_misses::total'
        accesses_key = 'system.l2cache.overall_accesses::total'
    else:
        return 0
    
    if misses_key in stats and accesses_key in stats:
        if stats[accesses_key] > 0:
            return stats[misses_key] / stats[accesses_key]
    return 0

def get_execution_time(stats):
    """Get execution time in seconds"""
    if 'sim_seconds' in stats:
        return stats['sim_seconds']
    elif 'sim_ticks' in stats:
        # Assume 1 tick = 0.5 ns (2GHz)
        return stats['sim_ticks'] * 0.5e-9
    return 0

def create_plot(results, x_metric, y_metric, output_file=None):
    """Create a plot from the results"""
    
    if not MATPLOTLIB_AVAILABLE:
        print("Error: matplotlib not available. Install with: pip install matplotlib")
        print("Alternatively, use: python3 scripts/analyze_results.py for tabular output")
        return False
    
    # Group results by application
    by_app = defaultdict(list)
    for result in results:
        app_name = result['config'].get('application', 'unknown')
        by_app[app_name].append(result)
    
    plt.figure(figsize=(10, 6))
    
    colors = ['blue', 'red', 'green', 'orange', 'purple']
    
    for i, (app_name, app_results) in enumerate(by_app.items()):
        x_values = []
        y_values = []
        
        for result in app_results:
            stats = result['stats']
            config = result['config']
            
            # Get X value
            if x_metric == 'l1d_size':
                x_val = config.get('cache_size_kb', 0)
            elif x_metric == 'l1d_assoc':
                x_val = config.get('associativity', 0)
            else:
                continue
            
            # Calculate Y value
            if y_metric == 'ipc':
                y_val = calculate_ipc(stats)
            elif y_metric == 'l1d_miss_rate':
                y_val = calculate_miss_rate(stats, 'l1d')
            elif y_metric == 'l2_miss_rate':
                y_val = calculate_miss_rate(stats, 'l2')
            elif y_metric == 'execution_time':
                y_val = get_execution_time(stats)
            else:
                continue
            
            if x_val > 0 and y_val > 0:
                x_values.append(x_val)
                y_values.append(y_val)
        
        if x_values and y_values:
            # Sort by x values for cleaner lines
            sorted_data = sorted(zip(x_values, y_values))
            x_sorted, y_sorted = zip(*sorted_data)
            
            plt.plot(x_sorted, y_sorted, 'o-', 
                    color=colors[i % len(colors)], 
                    label=app_name, 
                    linewidth=2, 
                    markersize=6)
    
    # Set labels and title
    x_label_map = {
        'l1d_size': 'L1D Cache Size (kB)',
        'l1d_assoc': 'L1D Cache Associativity'
    }
    
    y_label_map = {
        'ipc': 'Instructions Per Cycle (IPC)',
        'l1d_miss_rate': 'L1D Cache Miss Rate',
        'l2_miss_rate': 'L2 Cache Miss Rate',
        'execution_time': 'Execution Time (seconds)'
    }
    
    plt.xlabel(x_label_map.get(x_metric, x_metric))
    plt.ylabel(y_label_map.get(y_metric, y_metric))
    plt.title(f'{y_label_map.get(y_metric, y_metric)} vs {x_label_map.get(x_metric, x_metric)}')
    
    if x_metric == 'l1d_size':
        plt.xscale('log', base=2)
    
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Plot saved to: {output_file}")
    else:
        plt.show()
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Create plots from gem5 simulation results')
    parser.add_argument('results_dir', help='Directory containing simulation results')
    parser.add_argument('x_metric', choices=['l1d_size', 'l1d_assoc'], 
                       help='X-axis metric (independent variable)')
    parser.add_argument('y_metric', choices=['ipc', 'l1d_miss_rate', 'l2_miss_rate', 'execution_time'],
                       help='Y-axis metric (dependent variable)')
    parser.add_argument('-o', '--output', help='Output file for plot (e.g., plot.png)')
    
    args = parser.parse_args()
    
    print(f"Creating plot: {args.y_metric} vs {args.x_metric}")
    print(f"Data source: {args.results_dir}")
    
    # Collect results
    results = collect_results(args.results_dir)
    
    if not results:
        print("No simulation results found!")
        print("\nMake sure you have:")
        print("1. Run gem5 simulations that create stats.txt files")
        print("2. Organized results in subdirectories")
        print("3. Used the correct results directory path")
        return 1
    
    # Create plot
    success = create_plot(results, args.x_metric, args.y_metric, args.output)
    
    if success:
        print(f"\nPlot created successfully!")
        if not args.output:
            print("Close the plot window to continue.")
    else:
        print("Failed to create plot. Use analyze_results.py for tabular output instead.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())