#!/usr/bin/env python3

import os
import sys
import argparse
import re
from collections import defaultdict

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

def print_tabular_results(results, x_metric, y_metric):
    """Print results in tabular format"""
    
    print(f"\n{'='*70}")
    print(f"Performance Analysis: {y_metric} vs {x_metric}")
    print(f"{'='*70}")
    
    # Group results by application and configuration
    grouped = defaultdict(lambda: defaultdict(list))
    
    for result in results:
        stats = result['stats']
        config = result['config']
        
        app_name = config.get('application', 'unknown')
        
        # Get X value
        if x_metric == 'l1d_size':
            x_val = config.get('cache_size', 'unknown')
        elif x_metric == 'l1d_assoc':
            x_val = config.get('associativity', 'unknown')
        else:
            x_val = 'unknown'
        
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
            y_val = 0
        
        grouped[app_name][x_val].append(y_val)
    
    # Print results for each application
    for app_name in sorted(grouped.keys()):
        print(f"\n{app_name.upper()} RESULTS:")
        print("-" * 50)
        print(f"{'Config':<12} {'Average':<12} {'Min':<12} {'Max':<12} {'Count':<6}")
        print("-" * 50)
        
        # Sort configurations
        app_configs = grouped[app_name]
        sorted_configs = sorted(app_configs.keys(), key=lambda x: (
            int(x.replace('kB', '').replace('KB', '')) if 'kB' in str(x) or 'KB' in str(x) 
            else float('inf') if x == 'unknown' else int(x)
        ))
        
        for config in sorted_configs:
            values = app_configs[config]
            if values:
                avg_val = sum(values) / len(values)
                min_val = min(values)
                max_val = max(values)
                count = len(values)
                
                print(f"{str(config):<12} {avg_val:<12.4f} {min_val:<12.4f} {max_val:<12.4f} {count:<6}")
    
    print(f"\nSUMMARY:")
    print("-" * 50)
    print(f"Total results: {len(results)}")
    print(f"Applications: {len(grouped)}")
    print(f"Total configurations: {sum(len(app_configs) for app_configs in grouped.values())}")

def print_analysis_summary(results):
    """Print a summary analysis of all results"""
    print(f"\n{'='*70}")
    print("ANALYSIS SUMMARY")
    print(f"{'='*70}")
    
    # Group by application
    by_app = defaultdict(list)
    for result in results:
        app_name = result['config'].get('application', 'unknown')
        by_app[app_name].append(result)
    
    for app_name, app_results in by_app.items():
        print(f"\n{app_name.upper()}:")
        
        if len(app_results) < 2:
            print("  Not enough data points for analysis")
            continue
        
        # Calculate IPC range
        ipcs = [calculate_ipc(r['stats']) for r in app_results]
        min_ipc = min(ipcs)
        max_ipc = max(ipcs)
        
        if max_ipc > 0:
            improvement = ((max_ipc - min_ipc) / min_ipc) * 100
            print(f"  IPC range: {min_ipc:.4f} to {max_ipc:.4f}")
            print(f"  Max improvement: {improvement:.1f}%")
        
        # Cache sensitivity analysis
        cache_sizes = [r['config'].get('cache_size', '') for r in app_results]
        unique_sizes = set(cache_sizes)
        if len(unique_sizes) > 1:
            print(f"  Cache sizes tested: {', '.join(sorted(unique_sizes))}")
            
            # Find best and worst performing cache sizes
            size_performance = defaultdict(list)
            for result in app_results:
                size = result['config'].get('cache_size', 'unknown')
                ipc = calculate_ipc(result['stats'])
                if ipc > 0:
                    size_performance[size].append(ipc)
            
            if size_performance:
                avg_performance = {size: sum(ipcs)/len(ipcs) for size, ipcs in size_performance.items()}
                best_size = max(avg_performance, key=avg_performance.get)
                worst_size = min(avg_performance, key=avg_performance.get)
                
                print(f"  Best cache size: {best_size} (IPC: {avg_performance[best_size]:.4f})")
                print(f"  Worst cache size: {worst_size} (IPC: {avg_performance[worst_size]:.4f})")

def main():
    parser = argparse.ArgumentParser(description='Analyze gem5 simulation results')
    parser.add_argument('results_dir', help='Directory containing simulation results')
    parser.add_argument('x_metric', choices=['l1d_size', 'l1d_assoc'], 
                       help='X-axis metric (independent variable)')
    parser.add_argument('y_metric', choices=['ipc', 'l1d_miss_rate', 'l2_miss_rate', 'execution_time'],
                       help='Y-axis metric (dependent variable)')
    parser.add_argument('--summary', action='store_true', 
                       help='Print analysis summary in addition to tabular results')
    
    args = parser.parse_args()
    
    print(f"Analyzing results in: {args.results_dir}")
    print(f"X-axis: {args.x_metric}")
    print(f"Y-axis: {args.y_metric}")
    
    # Collect results
    results = collect_results(args.results_dir)
    
    if not results:
        print("No simulation results found!")
        print("\nMake sure you have:")
        print("1. Run gem5 simulations that create stats.txt files")
        print("2. Organized results in subdirectories")
        print("3. Used the correct results directory path")
        return 1
    
    # Print tabular analysis
    print_tabular_results(results, args.x_metric, args.y_metric)
    
    # Print summary analysis if requested
    if args.summary:
        print_analysis_summary(results)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())