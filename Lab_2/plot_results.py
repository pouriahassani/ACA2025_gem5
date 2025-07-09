#!/usr/bin/env python3
"""
Universal gem5 Results Plotting Script
Supports all configurable parameters as X/Y axes with flexible result directories
"""

import os
import sys
import re
import argparse
import glob
from collections import defaultdict

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not available. Using text-only output.")

def parse_stats_file(filepath):
    """Extract performance metrics from gem5 stats file"""
    stats = {}
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Key performance metrics
        patterns = {
            'sim_seconds': r'simSeconds\s+([\d\.]+)',
            'sim_ticks': r'simTicks\s+([\d]+)',
            'host_seconds': r'hostSeconds\s+([\d\.]+)',
            'sim_insts': r'simInsts\s+([\d]+)',
            'ipc': r'system\.cpu\.ipc\s+([\d\.]+)',
            'cpi': r'system\.cpu\.cpi\s+([\d\.]+)',
            'num_cycles': r'system\.cpu\.numCycles\s+([\d]+)',
            
            # Cache statistics
            'l1d_hits': r'system\.cpu\.dcache\.overallHits::total\s+([\d]+)',
            'l1d_misses': r'system\.cpu\.dcache\.overallMisses::total\s+([\d]+)',
            'l1d_miss_rate': r'system\.cpu\.dcache\.overallMissRate::total\s+([\d\.]+)',
            'l1d_miss_latency': r'system\.cpu\.dcache\.overallMissLatency::total\s+([\d]+)',
            
            'l1i_hits': r'system\.cpu\.icache\.overallHits::total\s+([\d]+)',
            'l1i_misses': r'system\.cpu\.icache\.overallMisses::total\s+([\d]+)',
            'l1i_miss_rate': r'system\.cpu\.icache\.overallMissRate::total\s+([\d\.]+)',
            
            'l2_hits': r'system\.l2cache\.overallHits::total\s+([\d]+)',
            'l2_misses': r'system\.l2cache\.overallMisses::total\s+([\d]+)',
            'l2_miss_rate': r'system\.l2cache\.overallMissRate::total\s+([\d\.]+)',
            
            'l3_hits': r'system\.l3cache\.overallHits::total\s+([\d]+)',
            'l3_misses': r'system\.l3cache\.overallMisses::total\s+([\d]+)',
            'l3_miss_rate': r'system\.l3cache\.overallMissRate::total\s+([\d\.]+)',
            
            # Memory controller statistics
            'mem_reads': r'system\.mem_ctrl\.dram\.readReqs\s+([\d]+)',
            'mem_writes': r'system\.mem_ctrl\.dram\.writeReqs\s+([\d]+)',
            'mem_bandwidth': r'system\.mem_ctrl\.dram\.avgBW::total\s+([\d\.]+)',
            
            # Branch predictor statistics (O3CPU)
            'branch_pred_accuracy': r'system\.cpu\.branchPred\.condPredicted\s+([\d]+)',
            'branch_mispreds': r'system\.cpu\.branchPred\.condIncorrect\s+([\d]+)',
        }
        
        for metric, pattern in patterns.items():
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                try:
                    stats[metric] = float(match.group(1))
                except ValueError:
                    stats[metric] = match.group(1)
        
        # Calculate derived metrics
        if 'l1d_hits' in stats and 'l1d_misses' in stats:
            total_accesses = stats['l1d_hits'] + stats['l1d_misses']
            if total_accesses > 0:
                stats['l1d_miss_rate'] = stats['l1d_misses'] / total_accesses
        
        if 'branch_pred_accuracy' in stats and 'branch_mispreds' in stats:
            total_branches = stats['branch_pred_accuracy'] + stats['branch_mispreds']
            if total_branches > 0:
                stats['branch_accuracy'] = stats['branch_pred_accuracy'] / total_branches
                
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        
    return stats

def extract_config_from_filename(filename):
    """Extract all configuration parameters from comprehensive filename"""
    config = {}
    
    # Extract kernel name and optimization
    kernel_match = re.search(r'stats_([^_]+)_(opt|unopt)', filename)
    if kernel_match:
        config['kernel'] = kernel_match.group(1)
        config['optimized'] = kernel_match.group(2) == 'opt'
    
    # Extract cache configurations
    cache_patterns = {
        'l1i_size': r'L1I(\d+[kKmMgG][bB]?)(?:A(\d+))?',
        'l1d_size': r'L1D(\d+[kKmMgG][bB]?)(?:A(\d+))?', 
        'l2_size': r'L2(\d+[kKmMgG][bB]?|None)(?:A(\d+))?',
        'l3_size': r'L3(\d+[kKmMgG][bB]?)(?:A(\d+))?'
    }
    
    for cache_type, pattern in cache_patterns.items():
        match = re.search(pattern, filename)
        if match:
            size_value = match.group(1)
            config[cache_type] = size_value if size_value != 'None' else '256kB'  # Default for None
            if len(match.groups()) > 1 and match.group(2):  # Associativity is optional
                config[cache_type.replace('_size', '_assoc')] = int(match.group(2))
    
    # Extract CPU type
    cpu_match = re.search(r'_(Timing|Atomic|O3)_', filename)
    if cpu_match:
        config['cpu_type'] = cpu_match.group(1) + 'CPU'
    
    # Extract clock frequency
    clock_match = re.search(r'_(\d+[GM])_', filename)
    if clock_match:
        freq_str = clock_match.group(1)
        if freq_str.endswith('G'):
            config['clock_ghz'] = float(freq_str[:-1])
        elif freq_str.endswith('M'):
            config['clock_ghz'] = float(freq_str[:-1]) / 1000
    
    # Extract memory type
    mem_match = re.search(r'_(DDR[34]_\d+_\d+x\d+|LPDDR\d+_[^_]+)', filename)
    if mem_match:
        config['mem_type'] = mem_match.group(1)
    
    # Extract branch predictor
    bp_match = re.search(r'_(Local|Tournament|BiMode|TAGE|Multiperspective)BP', filename)
    if bp_match:
        config['branch_predictor'] = bp_match.group(1) + 'BP'
    
    return config

def convert_size_to_kb(size_str):
    """Convert size string to KB for numerical comparison"""
    if not size_str:
        return 0
        
    size_str = str(size_str).upper()
    
    # Extract number and unit
    match = re.match(r'(\d+)([KMGT]?B?)', size_str)
    if not match:
        return 0
    
    value = int(match.group(1))
    unit = match.group(2)
    
    if unit.startswith('K'):
        return value
    elif unit.startswith('M'):
        return value * 1024
    elif unit.startswith('G'):
        return value * 1024 * 1024
    elif unit.startswith('T'):
        return value * 1024 * 1024 * 1024
    else:
        return value / 1024  # Assume bytes

def convert_clock_to_ghz(clock_val):
    """Convert clock value to GHz for numerical comparison"""
    if isinstance(clock_val, (int, float)):
        return float(clock_val)
    
    # Handle string values like "2GHz", "1000MHz"
    clock_str = str(clock_val).upper()
    match = re.match(r'(\d+(?:\.\d+)?)([MG]?)HZ?', clock_str)
    if match:
        value = float(match.group(1))
        unit = match.group(2)
        if unit == 'M':
            return value / 1000
        elif unit == 'G' or unit == '':
            return value
    
    return float(clock_val) if clock_val else 0

def load_all_results(results_dir):
    """Load all stats files from results directory"""
    if not os.path.exists(results_dir):
        print(f"Error: Results directory '{results_dir}' not found!")
        return []
    
    # Find all stats files
    stats_files = glob.glob(os.path.join(results_dir, "stats_*.txt"))
    
    if not stats_files:
        print(f"No stats files found in {results_dir}")
        return []
    
    print(f"Found {len(stats_files)} stats files in {results_dir}")
    
    all_data = []
    for filepath in stats_files:
        filename = os.path.basename(filepath)
        
        # Extract stats and configuration
        stats = parse_stats_file(filepath)
        config = extract_config_from_filename(filename)
        
        if stats and config:
            data_point = {**stats, **config, 'filename': filename}
            all_data.append(data_point)
        else:
            print(f"Warning: Could not parse {filename}")
    
    return all_data

def get_axis_value(data_point, axis_param):
    """Get numerical value for axis parameter"""
    
    # Size parameters
    if axis_param.endswith('_size'):
        return convert_size_to_kb(data_point.get(axis_param, 0))
    
    # Clock parameters
    elif 'clock' in axis_param:
        return convert_clock_to_ghz(data_point.get(axis_param, 0))
    
    # Direct numerical parameters
    elif axis_param in data_point:
        return float(data_point[axis_param])
    
    # String parameters - return as category
    else:
        return data_point.get(axis_param, 'Unknown')

def create_plot(all_data, x_param, y_param, output_dir):
    """Create plot with matplotlib or text output"""
    
    if not all_data:
        print("No data to plot!")
        return
    
    # Separate optimized and unoptimized data
    opt_data = [d for d in all_data if d.get('optimized', False)]
    unopt_data = [d for d in all_data if not d.get('optimized', False)]
    
    # Get x and y values
    def get_plot_data(data_list):
        x_vals = []
        y_vals = []
        for dp in data_list:
            x_val = get_axis_value(dp, x_param)
            y_val = get_axis_value(dp, y_param)
            if x_val is not None and y_val is not None:
                x_vals.append(x_val)
                y_vals.append(y_val)
        return x_vals, y_vals
    
    unopt_x, unopt_y = get_plot_data(unopt_data)
    opt_x, opt_y = get_plot_data(opt_data)
    
    # Generate axis labels
    x_label = x_param.replace('_', ' ').title()
    y_label = y_param.replace('_', ' ').title()
    
    if x_param.endswith('_size'):
        x_label += ' (KB)'
    elif 'clock' in x_param:
        x_label += ' (GHz)'
    
    if HAS_MATPLOTLIB:
        # Create matplotlib plot
        plt.figure(figsize=(10, 6))
        
        if unopt_x and unopt_y:
            plt.plot(unopt_x, unopt_y, 'b-o', label='Unoptimized', linewidth=2, markersize=6)
        
        if opt_x and opt_y:
            plt.plot(opt_x, opt_y, 'r-s', label='Optimized', linewidth=2, markersize=6)
        
        plt.xlabel(x_label, fontsize=12)
        plt.ylabel(y_label, fontsize=12)
        plt.title(f'{y_label} vs {x_label}', fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.legend(fontsize=11)
        
        # Save plot
        plot_filename = f"plot_{x_param}_vs_{y_param}.png"
        plot_path = os.path.join(output_dir, plot_filename)
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 Plot saved to: {plot_path}")
        
    else:
        # Text-based output
        print(f"\n{'='*60}")
        print(f"PLOT: {x_label} vs {y_label}")
        print(f"{'='*60}")
        
        if unopt_data:
            print(f"\nUNOPTIMIZED DATA:")
            print(f"{'='*40}")
            for i, (x, y) in enumerate(zip(unopt_x, unopt_y)):
                print(f"{x_param}={x}, {y_param}={y}")
        
        if opt_data:
            print(f"\nOPTIMIZED DATA:")
            print(f"{'='*40}")
            for i, (x, y) in enumerate(zip(opt_x, opt_y)):
                print(f"{x_param}={x}, {y_param}={y}")

def get_available_parameters(all_data):
    """Get list of all available parameters for plotting"""
    all_params = set()
    
    for data_point in all_data:
        all_params.update(data_point.keys())
    
    # Remove non-plottable parameters
    exclude = {'filename', 'optimized'}
    plottable_params = sorted([p for p in all_params if p not in exclude])
    
    return plottable_params

def main():
    """Main plotting function"""
    parser = argparse.ArgumentParser(description='Universal gem5 Results Plotting Script')
    
    parser.add_argument('--results-dir', '-d', 
                       required=True,
                       help='Directory containing stats files')
    
    parser.add_argument('--x-axis', '-x',
                       required=True, 
                       help='X-axis parameter')
    
    parser.add_argument('--y-axis', '-y',
                       required=True,
                       help='Y-axis parameter')
    
    parser.add_argument('--output-dir', '-o',
                       default=None,
                       help='Output directory for plots (default: same as results-dir)')
    
    parser.add_argument('--list-params', '-l',
                       action='store_true',
                       help='List all available parameters')
    
    args = parser.parse_args()
    
    # Set output directory
    if args.output_dir is None:
        args.output_dir = args.results_dir
    
    # Load all results
    all_data = load_all_results(args.results_dir)
    
    if not all_data:
        print("No valid data found!")
        return
    
    # List available parameters if requested
    if args.list_params:
        available_params = get_available_parameters(all_data)
        print(f"\nAvailable parameters for plotting:")
        print(f"{'='*50}")
        for param in available_params:
            sample_values = [str(d.get(param, 'N/A')) for d in all_data[:3]]
            print(f"{param:25} (e.g., {', '.join(sample_values)})")
        return
    
    # Validate parameters
    available_params = get_available_parameters(all_data)
    
    if args.x_axis not in available_params:
        print(f"Error: X-axis parameter '{args.x_axis}' not found!")
        print(f"Available parameters: {', '.join(available_params)}")
        return
    
    if args.y_axis not in available_params:
        print(f"Error: Y-axis parameter '{args.y_axis}' not found!")
        print(f"Available parameters: {', '.join(available_params)}")
        return
    
    # Create plot
    create_plot(all_data, args.x_axis, args.y_axis, args.output_dir)
    
    # Print summary
    print(f"\nSummary:")
    print(f"Results directory: {args.results_dir}")
    print(f"Data points: {len(all_data)}")
    print(f"X-axis: {args.x_axis}")
    print(f"Y-axis: {args.y_axis}")
    print(f"Output directory: {args.output_dir}")

def print_usage_examples():
    """Print comprehensive usage examples"""
    print("="*60)
    print("USAGE EXAMPLES")
    print("="*60)
    
    print("\n1. Basic cache size vs performance:")
    print("   python3 plot_results.py -d results -x l1d_size -y ipc")
    
    print("\n2. Associativity vs miss rate:")
    print("   python3 plot_results.py -d my_results -x l1d_assoc -y l1d_miss_rate")
    
    print("\n3. Clock frequency vs execution time:")
    print("   python3 plot_results.py -d results -x clock_ghz -y sim_seconds")
    
    print("\n4. Memory bandwidth utilization:")
    print("   python3 plot_results.py -d results -x l2_size -y mem_bandwidth")
    
    print("\n5. Branch predictor comparison:")
    print("   python3 plot_results.py -d results -x branch_predictor -y branch_accuracy")
    
    print("\n6. List all available parameters:")
    print("   python3 plot_results.py -d results --list-params")
    
    print("\n7. Save plots to different directory:")
    print("   python3 plot_results.py -d results -x l1d_size -y ipc -o plots/")
    
    print("\nCOMMON PARAMETERS:")
    print("="*40)
    print("X-axis options:")
    print("  Cache sizes:     l1i_size, l1d_size, l2_size, l3_size")
    print("  Associativity:   l1i_assoc, l1d_assoc, l2_assoc, l3_assoc") 
    print("  System:          clock_ghz, cpu_type, mem_type")
    print("  Other:           kernel, branch_predictor")
    
    print("\nY-axis options:")
    print("  Performance:     ipc, cpi, sim_seconds")
    print("  Cache behavior:  l1d_miss_rate, l2_miss_rate, l1d_misses")
    print("  Memory:          mem_reads, mem_writes, mem_bandwidth")
    print("  Branches:        branch_accuracy, branch_mispreds")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print_usage_examples()
    else:
        main()
