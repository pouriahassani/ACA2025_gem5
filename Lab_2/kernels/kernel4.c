// tlb_sparse_opt.c
#include <stdio.h>
#include <stdlib.h>

#define STRIDE 4096
#define NUM_ACCESSES 10000
#define BLOCK_SIZE 64
#define ARRAY_SIZE (STRIDE * NUM_ACCESSES)

int A[ARRAY_SIZE];

int main() {
    long long sum = 0;

    // Initialize
    for (int i = 0; i < ARRAY_SIZE; i++)
        A[i] = i;

    // Blocked access to stay within fewer pages at a time
    for (int block = 0; block < NUM_ACCESSES; block += BLOCK_SIZE) {
        for (int i = 0; i < BLOCK_SIZE; i++) {
            sum += A[(block + i) * STRIDE];
        }
    }

    printf("Sum = %lld\n", sum);
    return 0;
}
