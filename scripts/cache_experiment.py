import argparse
import sys
import os

import m5
from m5.objects import *
from m5.params import *
from m5.util import addToPath, fatal

sys.path.append("/opt/ACA2025/gem5/configs")
addToPath("/opt/ACA2025/gem5/configs")

from common import SimpleOpts

# Add command line options for cache configuration
SimpleOpts.add_option("--l1d_size", default="64kB", help="L1 data cache size")
SimpleOpts.add_option("--l1d_assoc", default="2", help="L1 data cache associativity")
SimpleOpts.add_option("--l1i_size", default="16kB", help="L1 instruction cache size")
SimpleOpts.add_option("--l1i_assoc", default="2", help="L1 instruction cache associativity")
SimpleOpts.add_option("--l2_size", default="256kB", help="L2 cache size")
SimpleOpts.add_option("--l2_assoc", default="8", help="L2 cache associativity")
SimpleOpts.add_option("--binary", required=True, help="Binary to run")
SimpleOpts.add_option("--out_dir", default="m5out", help="Output directory")

# Custom cache classes
class L1Cache(Cache):
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 4
    tgts_per_mshr = 20

class L1ICache(L1Cache):
    size = "16kB"
    assoc = 2

class L1DCache(L1Cache):
    size = "64kB"
    assoc = 2

class L2Cache(Cache):
    size = "256kB"
    assoc = 8
    tag_latency = 20
    data_latency = 20
    response_latency = 20
    mshrs = 20
    tgts_per_mshr = 12

def create_system():
    # Create the system
    system = System()
    
    # Set the clock and voltage
    system.clk_domain = SrcClockDomain()
    system.clk_domain.clock = "2GHz"
    system.clk_domain.voltage_domain = VoltageDomain()
    
    # Set up memory mode and ranges
    system.mem_mode = "timing"
    system.mem_ranges = [AddrRange("512MB")]
    
    # Create a simple timing CPU
    system.cpu = TimingSimpleCPU()
    
    # Create L1 caches
    system.cpu.icache = L1ICache()
    system.cpu.dcache = L1DCache()
    
    # Connect CPU to L1 caches
    system.cpu.icache.cpu_side = system.cpu.icache_port
    system.cpu.dcache.cpu_side = system.cpu.dcache_port
    
    # Create L2 cache
    system.l2cache = L2Cache()
    
    # Create L2 bus
    system.l2bus = L2XBar()
    
    # Connect L1 caches to L2 bus
    system.cpu.icache.mem_side = system.l2bus.cpu_side_ports
    system.cpu.dcache.mem_side = system.l2bus.cpu_side_ports
    
    # Connect L2 cache to L2 bus
    system.l2cache.cpu_side = system.l2bus.mem_side_ports
    
    # Create system bus
    system.membus = SystemXBar()
    
    # Connect L2 cache to memory bus
    system.l2cache.mem_side = system.membus.cpu_side_ports
    
    # Connect CPU interrupt ports (needed for TimingSimpleCPU)
    system.cpu.createInterruptController()
    system.cpu.interrupts[0].pio = system.membus.mem_side_ports
    system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
    system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports
    
    # Create memory controller
    system.mem_ctrl = MemCtrl()
    system.mem_ctrl.dram = DDR3_1600_8x8()
    system.mem_ctrl.dram.range = system.mem_ranges[0]
    system.mem_ctrl.port = system.membus.mem_side_ports
    
    # Set up system port
    system.system_port = system.membus.cpu_side_ports
    
    return system

def main():
    args = SimpleOpts.parse_args()
    
    # Create the system
    system = create_system()
    
    # Configure cache sizes based on command line arguments
    system.cpu.icache.size = args.l1i_size
    system.cpu.icache.assoc = int(args.l1i_assoc)
    system.cpu.dcache.size = args.l1d_size
    system.cpu.dcache.assoc = int(args.l1d_assoc)
    system.l2cache.size = args.l2_size
    system.l2cache.assoc = int(args.l2_assoc)
    
    # Set up the workload
    system.workload = SEWorkload.init_compatible(args.binary)
    
    # Set up the process
    process = Process()
    process.cmd = [args.binary]
    system.cpu.workload = process
    system.cpu.createThreads()
    
    # Create the root object
    root = Root(full_system=False, system=system)
    
    # Instantiate the simulation
    m5.instantiate()
    
    print(f"Beginning simulation with:")
    print(f"  L1D Cache: {args.l1d_size}, {args.l1d_assoc}-way")
    print(f"  L1I Cache: {args.l1i_size}, {args.l1i_assoc}-way") 
    print(f"  L2 Cache: {args.l2_size}, {args.l2_assoc}-way")
    print(f"  Binary: {args.binary}")
    
    # Run the simulation
    exit_event = m5.simulate()
    
    print(f"Simulation completed: {exit_event.getCause()}")

if __name__ == "__main__":
    main()