# ACA2025 gem5 Lab Instructions

This guide walks you through accessing the Apptainer container, cloning the gem5 lab repository, running simulations, and visualizing results.

---

## 🖥️ 1. Access the System & Container

Make sure you're working on the lab PC. The Apptainer image is already available.

### Open the Apptainer container:
Inside the container:
```bash
apptainer shell \
  --bind $(pwd):/workspace \
  -B /run \
  /shares/ziti-opt/software/cat/aca2025.sif
```
### Clone the Repo
```bash
  cd /workspace \
  git clone https://github.com/pouriahassani/ACA2025_gem5.git \
  cd ACA2025_gem5
```
### Run Simulations
Note: All commands assume you're inside ACA2025_gem5.
First, you need to compile the application you want to run on the simulated system:
```gcc -o hello_world kernels/hello_world.c```

now that you have your binary, you can run your system:
```bash
/opt/ACA2025/gem5/build/X86/gem5.debug \
  simple.py \
  --cpu=X86TimingSimpleCPU \
  --clock=2GHz \
  --l1_size=32kB
```

### Run two_level_automated.py (configurable L1/L2 caches)
```bash
/opt/ACA2025/gem5/build/X86/gem5.debug \
  two_level_automated.py \
  --cpu_type=X86O3CPU \
  --clock=2GHz \
  --l1i_size=32kB \
  --l1d_size=64kB \
  --l2_size=512kB \
  --binary=kernel2 \
  --out_dir=results
```
This saves stats into:
```results/stats_binarykernel2_CPUX86O3CPU_L1I32kB_L1D64kB_L2512kB_2GHz.txt```

###  Plot Results
To plot any available stat (e.g. IPC):
```python3 plot_stats.py system.cpu.ipc --path_dir results```

### To list available stat keys, run:
```python3 plot_stats.py --list_keys --path_dir results```






