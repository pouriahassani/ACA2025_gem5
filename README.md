# ACA2025 Computer Architecture Lab - Student Guide

Welcome to the computer architecture lab! In this assignment, you'll explore cache hierarchy design and application performance optimization using gem5 simulation.

## 🎯 Lab Objectives

By completing this lab, you will:
- Understand how cache size and associativity affect application performance
- Learn to identify cache-sensitive vs cache-insensitive workloads
- Practice code optimization techniques for better cache utilization
- Analyze performance-power trade-offs in cache design
- Gain hands-on experience with professional computer architecture simulation tools

## 📁 Directory Structure

```
student_lab/
├── kernels/                 # Application kernels for testing
│   ├── matrix_mult_unopt.c  # Unoptimized matrix multiplication
│   ├── image_blur_unopt.c   # Unoptimized image processing
│   ├── hash_ops.c           # Hash table operations
│   └── stream_bench.c       # Memory streaming benchmark
├── scripts/                 # Analysis and automation scripts
│   ├── cache_experiment.py  # gem5 configuration script
│   ├── analyze_results.py   # Tabular data analysis script
│   ├── plot_results.py      # Visual plotting script (optional)
│   └── run_cache_sweep.sh   # Automated experiment runner
├── results/                 # Your simulation results will go here
└── README.md               # This file
```

## 🚀 Quick Start Guide

### Step 1: Environment Setup

Make sure you're running inside the gem5 container:

```bash
# If using Apptainer on ZiTiPool
apptainer shell --bind $(pwd):/workspace -B /run /shares/ziti-opt/software/cat/aca2025.sif

# If using Docker
docker run -it -v $(pwd):/workspace gem5-lab
```

Verify gem5 is available:
```bash
which gem5.opt
# Should show: /opt/ACA2025/gem5/build/X86/gem5.opt
```

### Step 2: Compile the Kernels

```bash
cd kernels

# Compile all kernels
gcc -O2 -o matrix_mult_unopt matrix_mult_unopt.c
gcc -O2 -o image_blur_unopt image_blur_unopt.c
gcc -O2 -o hash_ops hash_ops.c
gcc -O2 -o stream_bench stream_bench.c

# Verify they work
./matrix_mult_unopt
./image_blur_unopt

cd ..
```

### Step 3: Run Your First Simulation

```bash
# Test a single configuration
gem5.opt scripts/cache_experiment.py \
    --l1d_size 32kB \
    --l1d_assoc 2 \
    --binary kernels/matrix_mult_unopt \
    --out_dir results/test_run

# Check results
ls results/test_run/
# Should see: stats.txt, config.ini, etc.
```

### Step 4: Run Cache Size Sweep

Use the automated script to test multiple cache sizes:

```bash
# Run cache size sweep for matrix multiplication
./scripts/run_cache_sweep.sh -b kernels/matrix_mult_unopt

# This will test cache sizes: 8kB, 16kB, 32kB, 64kB, 128kB
# Results saved in: results/matrix_mult_unopt/
```

### Step 5: Analyze Results

```bash
# Option 1: Tabular analysis (always works)
python3 scripts/analyze_results.py results/matrix_mult_unopt l1d_size ipc
python3 scripts/analyze_results.py results/matrix_mult_unopt l1d_size l1d_miss_rate

# Get detailed analysis summary
python3 scripts/analyze_results.py results/matrix_mult_unopt l1d_size ipc --summary

# Option 2: Visual plots (requires matplotlib)
python3 scripts/plot_results.py results/matrix_mult_unopt l1d_size ipc -o ipc_plot.png
python3 scripts/plot_results.py results/matrix_mult_unopt l1d_size l1d_miss_rate -o miss_rate_plot.png
```

## 📊 Assignment Tasks

### Task 1: Cache Size Sensitivity Analysis (60%)

**Objective:** Analyze how different cache sizes affect the performance of memory-intensive applications.

**Applications to test:**
- `matrix_mult_unopt` - Matrix multiplication (cache-sensitive)
- `image_blur_unopt` - Image convolution (cache-sensitive)  
- `hash_ops` - Hash table operations (irregular access)
- `stream_bench` - Memory streaming (bandwidth-limited)

**What to do:**
1. Run cache size sweeps for each application
2. Analyze IPC, miss rates, and execution time vs cache size
3. Identify which applications are cache-sensitive
4. Calculate working set sizes
5. Explain performance differences using cache theory

**Commands:**
```bash
# Run for all applications
./scripts/run_cache_sweep.sh -b kernels/matrix_mult_unopt
./scripts/run_cache_sweep.sh -b kernels/image_blur_unopt
./scripts/run_cache_sweep.sh -b kernels/hash_ops
./scripts/run_cache_sweep.sh -b kernels/stream_bench

# Analyze each one
python3 scripts/analyze_results.py results/matrix_mult_unopt l1d_size ipc
python3 scripts/analyze_results.py results/image_blur_unopt l1d_size ipc
python3 scripts/analyze_results.py results/hash_ops l1d_size ipc
python3 scripts/analyze_results.py results/stream_bench l1d_size ipc
```

### Task 2: Code Optimization Challenge (40%)

**Objective:** Optimize the matrix multiplication and image processing kernels to improve cache performance.

**What to do:**
1. **Analyze** the unoptimized code to identify cache performance issues
2. **Create optimized versions:**
   - `matrix_mult_opt.c` - Your optimized matrix multiplication
   - `image_blur_opt.c` - Your optimized image processing
3. **Apply optimization techniques:**
   - Loop interchange for better spatial locality
   - Cache blocking/tiling for large datasets
   - Memory access pattern optimization
4. **Measure improvements** using gem5
5. **Verify correctness** (same checksum values as unoptimized)

**Example optimization workflow:**
```bash
# 1. Study the unoptimized code
cd kernels
cat matrix_mult_unopt.c
# Identify the cache performance issues

# 2. Create optimized version
cp matrix_mult_unopt.c matrix_mult_opt.c
# Edit matrix_mult_opt.c with your optimizations

# 3. Compile and test
gcc -O2 -o matrix_mult_opt matrix_mult_opt.c
./matrix_mult_opt  # Verify it produces correct results

# 4. Run performance comparison
cd ..
./scripts/run_cache_sweep.sh -b kernels/matrix_mult_opt
python3 scripts/analyze_results.py results/matrix_mult_opt l1d_size ipc

# 5. Compare optimized vs unoptimized
python3 scripts/analyze_results.py results/matrix_mult_unopt l1d_size ipc
python3 scripts/analyze_results.py results/matrix_mult_opt l1d_size ipc
```

## 🛠 Script Reference

### cache_experiment.py

The main gem5 configuration script with these options:

```bash
gem5.opt scripts/cache_experiment.py \
    --l1d_size <size>      # L1D cache size (default: 64kB)
    --l1d_assoc <assoc>    # L1D associativity (default: 2)
    --l1i_size <size>      # L1I cache size (default: 16kB)
    --l1i_assoc <assoc>    # L1I associativity (default: 2)
    --l2_size <size>       # L2 cache size (default: 256kB)
    --l2_assoc <assoc>     # L2 associativity (default: 8)
    --binary <path>        # Binary to simulate (required)
    --out_dir <dir>        # Output directory (default: m5out)
```

### run_cache_sweep.sh

Automated script to run multiple cache configurations:

```bash
./scripts/run_cache_sweep.sh [options]

Required:
  -b <binary>           Path to the application binary

Options:
  -o <output_dir>       Base output directory (default: results)
  -s <sizes>            Cache sizes to test (default: "8kB 16kB 32kB 64kB 128kB")
  -a <associativities>  Associativities to test (default: "2")
  -l <l2_size>          L2 cache size (default: 256kB)
  -L <l2_assoc>         L2 cache associativity (default: 8)
  -d                    Dry run - show commands without executing
  -h                    Show help

Examples:
  ./scripts/run_cache_sweep.sh -b kernels/matrix_mult_unopt
  ./scripts/run_cache_sweep.sh -b kernels/hash_ops -s "16kB 32kB 64kB"
  ./scripts/run_cache_sweep.sh -b kernels/stream_bench -a "2 4 8" -d
```

### analyze_results.py

Data analysis script with tabular output (recommended - always works):

```bash
python3 scripts/analyze_results.py <results_dir> <x_metric> <y_metric> [--summary]

X metrics (independent variable):
  l1d_size              L1D cache size
  l1d_assoc             L1D cache associativity

Y metrics (dependent variable):
  ipc                   Instructions per cycle
  l1d_miss_rate         L1D cache miss rate
  l2_miss_rate          L2 cache miss rate
  execution_time        Total execution time

Options:
  --summary             Print detailed analysis summary

Examples:
  python3 scripts/analyze_results.py results/matrix_mult_unopt l1d_size ipc
  python3 scripts/analyze_results.py results/hash_ops l1d_size l1d_miss_rate --summary
```

### plot_results.py

Visual plotting script (optional - requires matplotlib):

```bash
python3 scripts/plot_results.py <results_dir> <x_metric> <y_metric> [-o output_file]

Same metrics as analyze_results.py

Options:
  -o output_file        Save plot to file (e.g., plot.png)

Examples:
  python3 scripts/plot_results.py results/matrix_mult_unopt l1d_size ipc
  python3 scripts/plot_results.py results/hash_ops l1d_size l1d_miss_rate -o miss_rate.png

Note: If matplotlib is not available, the script will suggest using analyze_results.py instead.
```

## 📈 Expected Results & Analysis Tips

### Cache-Sensitive Applications (matrix_mult, image_blur)
- **Expected behavior:** Performance improves significantly with larger cache sizes
- **Why:** These have predictable access patterns that benefit from spatial locality
- **Working set:** Matrix size affects optimal cache size
- **Optimization potential:** High - loop reordering can dramatically improve performance

### Cache-Insensitive Applications (stream_bench)
- **Expected behavior:** Performance plateaus quickly, minimal improvement with larger caches
- **Why:** Streaming access pattern with little temporal reuse
- **Bottleneck:** Memory bandwidth, not cache capacity
- **Optimization potential:** Low - already has optimal access patterns

### Irregular Access Applications (hash_ops)
- **Expected behavior:** Moderate improvement with larger caches
- **Why:** Random access patterns limit cache effectiveness
- **Characteristics:** Higher miss rates, less predictable performance
- **Optimization potential:** Medium - data structure layout improvements possible

### Key Metrics to Analyze

1. **IPC (Instructions Per Cycle)**
   - Higher is better
   - Shows overall CPU efficiency
   - Most affected by cache misses

2. **L1D Miss Rate**
   - Lower is better
   - Critical for cache-sensitive applications
   - Should decrease with larger cache sizes (if cache-sensitive)

3. **Execution Time**
   - Lower is better
   - Ultimate performance metric
   - Includes all system effects

## 🚨 Troubleshooting

### Common Issues

**"gem5.opt not found"**
```bash
# Check if you're in the container
which gem5.opt
# If not found, make sure you're running inside the gem5 container
```

**"Permission denied" when running scripts**
```bash
chmod +x scripts/run_cache_sweep.sh
```

**Compilation errors**
```bash
# Make sure you're in the kernels directory
cd kernels
# Check if gcc is available
gcc --version
```

**No results found**
```bash
# Check if simulation completed successfully
ls results/matrix_mult_unopt/
# Should see directories like: 8kB_assoc2, 16kB_assoc2, etc.
# Each should contain stats.txt
```

**Same performance across all cache sizes**
```bash
# This suggests the kernel is not cache-sensitive or working set is very small
# Check the kernel working set size vs cache sizes tested
# For matrix_mult_unopt with 256x256 matrices: ~768KB total working set
```

### Performance Tips

1. **Start small:** Test with fewer cache sizes initially to verify setup
2. **Use dry run:** Use `-d` flag with run_cache_sweep.sh to preview commands
3. **Parallel execution:** Run different applications simultaneously
4. **Check logs:** Look at simulation.log files if runs fail

### Getting Help

1. **Check this README** - Most questions are answered here
2. **Review homework assignment PDF** - Contains detailed requirements
3. **Examine example output** - Look at stats.txt files to understand data format
4. **Ask during office hours** - Bring specific error messages or results

## 📝 Report Guidelines

### What to Include

**Task 1 Analysis:**
- Performance tables for each application vs cache size
- Cache sensitivity classification with justification
- Working set size calculations
- Explanation of performance differences using cache theory

**Task 2 Optimization:**
- Description of optimization techniques used
- Before/after performance comparison
- Code snippets showing key changes
- Verification that results are correct
- Analysis of why optimizations worked

### Tables to Generate

Use the analyze_results.py script to generate tables like:

```
Performance Analysis: ipc vs l1d_size
============================================================

MATRIX_MULT_UNOPT RESULTS:
--------------------------------------------------
Config       Average      Min          Max          Count 
--------------------------------------------------
8kB          0.1234       0.1234       0.1234       1     
16kB         0.1456       0.1456       0.1456       1     
32kB         0.1789       0.1789       0.1789       1     
64kB         0.1888       0.1888       0.1888       1     
128kB        0.1890       0.1890       0.1890       1     
```

### Analysis Framework

For each application, answer:
1. **Is it cache-sensitive?** (Does performance improve with larger caches?)
2. **What's the working set size?** (Where does performance plateau?)
3. **What's the bottleneck?** (Cache capacity, bandwidth, computation?)
4. **How much improvement is possible?** (Compare smallest vs largest cache)

## ✅ Submission Checklist

- [ ] Completed Task 1: Cache size analysis for all 4 applications
- [ ] Completed Task 2: Optimized matrix_mult_opt.c and image_blur_opt.c
- [ ] Generated performance analysis tables
- [ ] Verified optimized code produces correct results
- [ ] Written report with analysis and explanations
- [ ] Organized files according to submission structure
- [ ] Double-checked that all simulations completed successfully

## 🎓 Academic Integrity

- Complete all work individually
- Write original analysis and explanations
- Cite any external sources used
- Do not share code or results with other students
- Follow university academic integrity policies

Good luck with your cache performance analysis!