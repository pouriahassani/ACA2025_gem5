import os
import shutil
import m5
from m5.objects import *

m5.util.addToPath("/opt/ACA2025/gem5/configs/")
from caches import *
from common import SimpleOpts

# Default binary
thispath = os.path.dirname(os.path.realpath(__file__))
default_binary = os.path.join(
    "/opt/ACA2025/gem5/",
    "tests/test-progs/hello/bin/x86/linux/hello",
)

# CLI options
SimpleOpts.add_option("--binary", default=default_binary, help="Path to binary to run")
SimpleOpts.add_option("--clock", default="1GHz", help="CPU clock rate")
SimpleOpts.add_option("--cpu_type", default="X86TimingSimpleCPU", help="CPU model")
SimpleOpts.add_option("--out_dir", default="two-level-automated", help="Output directory for stats")

# Parse args
args = SimpleOpts.parse_args()

# Build system
system = System()
system.clk_domain = SrcClockDomain()
system.clk_domain.clock = args.clock
system.clk_domain.voltage_domain = VoltageDomain()
system.mem_mode = "timing"
system.mem_ranges = [AddrRange("512MB")]

# CPU
cpu_class = eval(args.cpu_type)
system.cpu = cpu_class()

# L1 caches
system.cpu.icache = L1ICache(args)
system.cpu.dcache = L1DCache(args)
system.cpu.icache.connectCPU(system.cpu)
system.cpu.dcache.connectCPU(system.cpu)

# L2 interconnect
system.l2bus = L2XBar()
system.cpu.icache.connectBus(system.l2bus)
system.cpu.dcache.connectBus(system.l2bus)

# L2 cache
system.l2cache = L2Cache(args)
system.l2cache.connectCPUSideBus(system.l2bus)

# Memory bus
system.membus = SystemXBar()
system.l2cache.connectMemSideBus(system.membus)

# Interrupts
system.cpu.createInterruptController()
system.cpu.interrupts[0].pio = system.membus.mem_side_ports
system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports

# System port
system.system_port = system.membus.cpu_side_ports

# Memory controller
system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

# Binary + process
system.workload = SEWorkload.init_compatible(args.binary)
process = Process()
process.cmd = [args.binary]
system.cpu.workload = process
system.cpu.createThreads()

# Simulate
root = Root(full_system=False, system=system)
m5.instantiate()
print(f"Starting simulation...")
m5.stats.reset()
exit_event = m5.simulate()
print(f"Exiting @ tick {m5.curTick()} because {exit_event.getCause()}")
m5.stats.dump()

# Save stats file using param values
def get_attr(name, fallback):
    return getattr(args, name, fallback) or fallback

l1i = get_attr("l1i_size", "default")
l1d = get_attr("l1d_size", "default")
l2  = get_attr("l2_size",  "default")
clk = get_attr("clock", "default")
cpu = get_attr("cpu_type", "default")
out_dir = args.out_dir

# Extract binary name (without path or extension)
bin_label = os.path.splitext(os.path.basename(args.binary))[0]

# Construct and sanitize output filename
stats_file = f"stats_binary{bin_label}_CPU{cpu}_L1I{l1i}_L1D{l1d}_L2{l2}_{clk}.txt"
stats_file = stats_file.replace(" ", "").replace(",", "")
stats_path = os.path.join(out_dir, stats_file)

# Save stats
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

if os.path.exists("m5out/stats.txt"):
    print(f"Copying stats to: {stats_path}")
    shutil.copyfile("m5out/stats.txt", stats_path)
    print(f"✅ Stats copied to: {stats_path}")
else:
    print("❌ m5out/stats.txt not found. Cannot copy stats.")
