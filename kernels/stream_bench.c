#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define ARRAY_SIZE (1024 * 1024)  // 1M elements
#define REPEAT_COUNT 10

// Stream benchmark - tests memory bandwidth
void stream_copy(double *a, double *b, int n) {
    for (int i = 0; i < n; i++) {
        b[i] = a[i];
    }
}

void stream_scale(double *a, double *b, double scalar, int n) {
    for (int i = 0; i < n; i++) {
        b[i] = scalar * a[i];
    }
}

void stream_add(double *a, double *b, double *c, int n) {
    for (int i = 0; i < n; i++) {
        c[i] = a[i] + b[i];
    }
}

void stream_triad(double *a, double *b, double *c, double scalar, int n) {
    for (int i = 0; i < n; i++) {
        a[i] = b[i] + scalar * c[i];
    }
}

void initialize_arrays(double *a, double *b, double *c, int n) {
    for (int i = 0; i < n; i++) {
        a[i] = 1.0;
        b[i] = 2.0;
        c[i] = 0.0;
    }
}

int main() {
    double *a = (double*)malloc(ARRAY_SIZE * sizeof(double));
    double *b = (double*)malloc(ARRAY_SIZE * sizeof(double));
    double *c = (double*)malloc(ARRAY_SIZE * sizeof(double));
    
    if (!a || !b || !c) {
        printf("Memory allocation failed\n");
        return 1;
    }
    
    initialize_arrays(a, b, c, ARRAY_SIZE);
    
    clock_t start = clock();
    
    // Run stream operations multiple times
    for (int rep = 0; rep < REPEAT_COUNT; rep++) {
        stream_copy(a, c, ARRAY_SIZE);
        stream_scale(c, b, 2.5, ARRAY_SIZE);
        stream_add(a, b, c, ARRAY_SIZE);
        stream_triad(a, b, c, 1.5, ARRAY_SIZE);
    }
    
    clock_t end = clock();
    
    double time_taken = ((double)(end - start)) / CLOCKS_PER_SEC;
    printf("Stream benchmark completed in %f seconds\n", time_taken);
    printf("Final result checksum: a[100] = %f, b[100] = %f\n", a[100], b[100]);
    
    // Calculate approximate memory bandwidth
    long long total_bytes = (long long)ARRAY_SIZE * sizeof(double) * 10 * REPEAT_COUNT;  // 10 arrays accessed per repeat
    double bandwidth_gb_s = (total_bytes / (1024.0 * 1024.0 * 1024.0)) / time_taken;
    printf("Approximate memory bandwidth: %.2f GB/s\n", bandwidth_gb_s);
    
    free(a);
    free(b);
    free(c);
    
    return 0;
}