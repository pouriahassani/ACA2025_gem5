#!/bin/bash

# Cache Size Sweep Script
# This script runs multiple gem5 simulations with different cache configurations

set -e  # Exit on any error

# Default values
BINARY=""
OUTPUT_BASE="results"
CACHE_SIZES="8kB 16kB 32kB 64kB 128kB"
ASSOCIATIVITIES="2"
L2_SIZE="256kB"
L2_ASSOC="8"
DRY_RUN=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

usage() {
    echo "Usage: $0 -b <binary> [options]"
    echo ""
    echo "Required:"
    echo "  -b <binary>           Path to the application binary to simulate"
    echo ""
    echo "Options:"
    echo "  -o <output_dir>       Base output directory (default: results)"
    echo "  -s <sizes>            Cache sizes to test (default: \"8kB 16kB 32kB 64kB 128kB\")"
    echo "  -a <associativities>  Associativities to test (default: \"2\")"
    echo "  -l <l2_size>          L2 cache size (default: 256kB)"
    echo "  -L <l2_assoc>         L2 cache associativity (default: 8)"
    echo "  -d                    Dry run - show commands without executing"
    echo "  -h                    Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -b kernels/matrix_mult_unopt"
    echo "  $0 -b kernels/image_blur_unopt -o my_results -s \"16kB 32kB 64kB\""
    echo "  $0 -b kernels/hash_ops -a \"2 4 8\" -d"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parse command line arguments
while getopts "b:o:s:a:l:L:dh" opt; do
    case $opt in
        b)
            BINARY="$OPTARG"
            ;;
        o)
            OUTPUT_BASE="$OPTARG"
            ;;
        s)
            CACHE_SIZES="$OPTARG"
            ;;
        a)
            ASSOCIATIVITIES="$OPTARG"
            ;;
        l)
            L2_SIZE="$OPTARG"
            ;;
        L)
            L2_ASSOC="$OPTARG"
            ;;
        d)
            DRY_RUN=true
            ;;
        h)
            usage
            exit 0
            ;;
        \?)
            log_error "Invalid option: -$OPTARG"
            usage
            exit 1
            ;;
    esac
done

# Check required arguments
if [ -z "$BINARY" ]; then
    log_error "Binary path is required"
    usage
    exit 1
fi

# Check if binary exists
if [ ! -f "$BINARY" ]; then
    log_error "Binary not found: $BINARY"
    log_info "Make sure to compile your kernels first:"
    log_info "  cd kernels && gcc -O2 -o matrix_mult_unopt matrix_mult_unopt.c"
    exit 1
fi

# Check if gem5.opt is available
if ! command -v gem5.opt &> /dev/null; then
    log_error "gem5.opt not found in PATH"
    log_info "Make sure you're running inside the gem5 container or have gem5 installed"
    exit 1
fi

# Extract application name from binary path
APP_NAME=$(basename "$BINARY")
APP_OUTPUT_DIR="$OUTPUT_BASE/$APP_NAME"

log_info "Starting cache size sweep for $APP_NAME"
log_info "Output directory: $APP_OUTPUT_DIR"
log_info "Cache sizes: $CACHE_SIZES"
log_info "Associativities: $ASSOCIATIVITIES"

# Create output directory
if [ "$DRY_RUN" = false ]; then
    mkdir -p "$APP_OUTPUT_DIR"
fi

# Counter for progress tracking
TOTAL_RUNS=0
CURRENT_RUN=0

# Count total number of runs
for size in $CACHE_SIZES; do
    for assoc in $ASSOCIATIVITIES; do
        ((TOTAL_RUNS++))
    done
done

log_info "Total simulations to run: $TOTAL_RUNS"

# Run the experiments
for size in $CACHE_SIZES; do
    for assoc in $ASSOCIATIVITIES; do
        ((CURRENT_RUN++))
        
        # Create descriptive directory name
        RUN_DIR="${APP_OUTPUT_DIR}/${size}_assoc${assoc}"
        
        # Prepare the command
        CMD="gem5.opt scripts/cache_experiment.py \
            --l1d_size $size \
            --l1d_assoc $assoc \
            --l2_size $L2_SIZE \
            --l2_assoc $L2_ASSOC \
            --binary $BINARY \
            --out_dir $RUN_DIR"
        
        log_info "[$CURRENT_RUN/$TOTAL_RUNS] Running: L1D=${size}, Assoc=${assoc}"
        
        if [ "$DRY_RUN" = true ]; then
            echo "Would run: $CMD"
        else
            # Create run directory
            mkdir -p "$RUN_DIR"
            
            # Run the simulation
            if $CMD > "$RUN_DIR/simulation.log" 2>&1; then
                log_success "Completed: L1D=${size}, Assoc=${assoc}"
            else
                log_error "Failed: L1D=${size}, Assoc=${assoc}"
                log_info "Check log file: $RUN_DIR/simulation.log"
            fi
        fi
    done
done

if [ "$DRY_RUN" = false ]; then
    log_success "All simulations completed!"
    log_info "Results saved in: $APP_OUTPUT_DIR"
    log_info ""
    log_info "To analyze results, run:"
    log_info "  python3 scripts/analyze_results.py $APP_OUTPUT_DIR l1d_size ipc"
    log_info "  python3 scripts/analyze_results.py $APP_OUTPUT_DIR l1d_size l1d_miss_rate"
else
    log_info "Dry run completed. Use -d flag to see commands without executing."
fi