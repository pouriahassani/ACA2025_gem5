#!/usr/bin/env python3

import os
import shutil
import argparse
import m5
from m5.objects import *

# Add gem5 configs to path
m5.util.addToPath("/opt/ACA2025/gem5/configs/")
from caches import *
from common import SimpleOpts

def create_cache_size_config():
    """Create gem5 configuration for cache size sensitivity experiment"""
    
    # Get current directory for kernels
    thispath = os.path.dirname(os.path.realpath(__file__))
    
    # Add cache size specific options (avoid conflicts with caches.py)
    SimpleOpts.add_option("--binary", 
                         default=os.path.join(thispath, "kernels/cache_size_sensitive"), 
                         help="Path to cache size sensitive kernel binary")
    SimpleOpts.add_option("--optimized", 
                         default="0", 
                         help="Run optimized version (0=unoptimized, 1=optimized)")
    SimpleOpts.add_option("--clock", 
                         default="2GHz", 
                         help="CPU clock rate")
    SimpleOpts.add_option("--cpu_type", 
                         default="X86TimingSimpleCPU", 
                         help="CPU model (X86TimingSimpleCPU, X86O3CPU)")
    SimpleOpts.add_option("--memory_size", 
                         default="512MB", 
                         help="System memory size")
    SimpleOpts.add_option("--out_dir", 
                         default="cache_size_results", 
                         help="Output directory for stats")
    
    # Cache associativity options (sizes are handled by caches.py)
    SimpleOpts.add_option("--l1d_assoc", 
                         default="2", 
                         help="L1 data cache associativity")
    SimpleOpts.add_option("--l2_assoc", 
                         default="8", 
                         help="L2 cache associativity")
    
    # Cache line/block size options - commented out for now
    # In gem5, cache line size is typically set at system level
    # SimpleOpts.add_option("--l1d_block_size", 
    #                      default="64", 
    #                      help="L1 data cache block/line size in bytes (default: 64)")
    # SimpleOpts.add_option("--l2_block_size", 
    #                      default="64", 
    #                      help="L2 cache block/line size in bytes (default: 64)")
    
    # Parse arguments
    args = SimpleOpts.parse_args()
    
    # Build the system
    system = System()
    system.clk_domain = SrcClockDomain()
    system.clk_domain.clock = args.clock
    system.clk_domain.voltage_domain = VoltageDomain()
    system.mem_mode = "timing"
    system.mem_ranges = [AddrRange(args.memory_size)]
    
    # Create CPU
    cpu_class = eval(args.cpu_type)
    system.cpu = cpu_class()
    
    # Create custom L1 caches with enhanced parameters for matrix workload
    class CustomL1DCache(L1DCache):
        def __init__(self, opts):
            super().__init__(opts)
            if hasattr(opts, 'l1d_assoc'):
                self.assoc = int(opts.l1d_assoc)
            # Note: Cache line size is typically set at system level in gem5
            # For now, we'll skip this parameter until we find the correct way
            # Optimize for matrix multiplication workload
            self.mshrs = 8  # More MSHRs for better parallelism
            self.tgts_per_mshr = 16
    
    class CustomL2Cache(L2Cache):
        def __init__(self, opts):
            super().__init__(opts)
            if hasattr(opts, 'l2_assoc'):
                self.assoc = int(opts.l2_assoc)
            # Note: Cache line size is typically set at system level in gem5
            # Enhanced L2 for matrix workload
            self.mshrs = 20
            self.tgts_per_mshr = 12
    
    # Create and connect L1 caches (use existing classes from caches.py)
    system.cpu.icache = L1ICache(args)
    system.cpu.dcache = CustomL1DCache(args)
    system.cpu.icache.connectCPU(system.cpu)
    system.cpu.dcache.connectCPU(system.cpu)
    
    # Create L2 bus
    system.l2bus = L2XBar()
    system.cpu.icache.connectBus(system.l2bus)
    system.cpu.dcache.connectBus(system.l2bus)
    
    # Create L2 cache
    system.l2cache = CustomL2Cache(args)
    system.l2cache.connectCPUSideBus(system.l2bus)
    
    # Create memory bus
    system.membus = SystemXBar()
    system.l2cache.connectMemSideBus(system.membus)
    
    # Create interrupt controller
    system.cpu.createInterruptController()
    system.cpu.interrupts[0].pio = system.membus.mem_side_ports
    system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
    system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports
    
    # Connect system port
    system.system_port = system.membus.cpu_side_ports
    
    # Create memory controller
    system.mem_ctrl = MemCtrl()
    system.mem_ctrl.dram = DDR3_1600_8x8()
    system.mem_ctrl.dram.range = system.mem_ranges[0]
    system.mem_ctrl.port = system.membus.mem_side_ports
    
    # Set up the workload
    system.workload = SEWorkload.init_compatible(args.binary)
    process = Process()
    process.cmd = [args.binary, args.optimized]  # Pass optimized flag to kernel
    system.cpu.workload = process
    system.cpu.createThreads()
    
    return system, args

def run_simulation():
    """Run the gem5 simulation"""
    system, args = create_cache_size_config()
    
    # Create simulation root
    root = Root(full_system=False, system=system)
    m5.instantiate()
    
    print(f"Starting cache size sensitivity experiment...")
    print(f"Binary: {args.binary}")
    print(f"Optimized: {'Yes' if args.optimized == '1' else 'No'}")
    print(f"L1D Cache: {getattr(args, 'l1d_size', '64kB')} (assoc={getattr(args, 'l1d_assoc', '2')})")
    print(f"L2 Cache: {getattr(args, 'l2_size', '256kB')} (assoc={getattr(args, 'l2_assoc', '8')})")
    print(f"CPU: {args.cpu_type} @ {args.clock}")
    print("-" * 50)
    
    # Reset stats and run simulation
    m5.stats.reset()
    exit_event = m5.simulate()
    
    print(f"Simulation finished @ tick {m5.curTick()}")
    print(f"Exit reason: {exit_event.getCause()}")
    
    # Dump stats
    m5.stats.dump()
    
    # Save stats with descriptive filename
    save_stats(args)

def save_stats(args):
    """Save simulation statistics with descriptive filename"""
    
    # Create output directory
    if not os.path.exists(args.out_dir):
        os.makedirs(args.out_dir)
    
    # Extract binary name and determine optimization
    binary_name = os.path.basename(args.binary)
    
    # Determine optimization status from both binary name and argument
    is_optimized = (args.optimized == "1") or ("optimized" in binary_name)
    opt_str = "opt" if is_optimized else "unopt"
    cpu_str = args.cpu_type.replace("X86", "").replace("CPU", "")
    
    # Get actual cache sizes from args (these come from caches.py)
    l1d_size = getattr(args, 'l1d_size', '64kB')
    l2_size = getattr(args, 'l2_size', '256kB')
    
    stats_filename = (f"stats_{binary_name}_{opt_str}_"
                     f"L1D{l1d_size}_L2{l2_size}_"
                     f"{cpu_str}_{args.clock.replace('GHz', 'G')}.txt")
    
    # Clean filename
    stats_filename = stats_filename.replace(" ", "").replace(",", "")
    stats_path = os.path.join(args.out_dir, stats_filename)
    
    # Copy stats file
    if os.path.exists("m5out/stats.txt"):
        shutil.copyfile("m5out/stats.txt", stats_path)
        print(f"✅ Stats saved to: {stats_path}")
    else:
        print("❌ Stats file not found!")

def print_usage():
    """Print usage examples"""
    print("\n" + "="*60)
    print("CACHE SIZE SENSITIVITY EXPERIMENT")
    print("="*60)
    print("\nUsage Examples:")
    print("="*30)
    
    print("\n1. Basic run (unoptimized kernel, 32KB L1D):")
    print("   python3 cache_size_experiment.py")
    
    print("\n2. Test different L1D cache sizes:")
    print("   python3 cache_size_experiment.py --l1d_size 16kB")
    print("   python3 cache_size_experiment.py --l1d_size 64kB")
    print("   python3 cache_size_experiment.py --l1d_size 128kB")
    
    print("\n3. Compare optimized vs unoptimized:")
    print("   python3 cache_size_experiment.py --optimized 0 --l1d_size 32kB")
    print("   python3 cache_size_experiment.py --optimized 1 --l1d_size 32kB")
    
    print("\n4. Test different L2 cache sizes:")
    print("   python3 cache_size_experiment.py --l2_size 128kB")
    print("   python3 cache_size_experiment.py --l2_size 512kB")
    print("   python3 cache_size_experiment.py --l2_size 1MB")
    
    print("\n5. Different CPU models:")
    print("   python3 cache_size_experiment.py --cpu_type X86O3CPU")
    
    print("\nKey Parameters:")
    print("  --l1d_size: 16kB, 32kB, 64kB, 128kB")
    print("  --l2_size: 128kB, 256kB, 512kB, 1MB")
    print("  --optimized: 0 (unoptimized), 1 (cache-friendly)")
    print("  --cpu_type: X86TimingSimpleCPU, X86O3CPU")
    
    print("\nExpected Results:")
    print("  • Unoptimized kernel: Benefits significantly from larger caches")
    print("  • Optimized kernel: Less sensitive to cache size")
    print("  • L1D cache size has more impact than L2 for this workload")

if len(os.sys.argv) == 1:
    print_usage()
else:
    run_simulation()
