// mmm_naive.c
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define N 128
float A[N][N], B[N][N], C[N][N];

void init_matrices() {
    for (int i = 0; i < N; i++)
        for (int j = 0; j < N; j++) {
            A[i][j] = (float)(i + j);
            B[i][j] = (float)(i - j);
            C[i][j] = 0.0f;
        }
}

void matrix_multiply_naive() {
    for (int i = 0; i < N; i++)         // row of A
        for (int j = 0; j < N; j++)     // col of B
            for (int k = 0; k < N; k++) // dot product
                C[i][j] += A[i][k] * B[k][j]; // B accessed column-wise (cache unfriendly)
}

int main() {
    clock_t start = clock();
    init_matrices();
    matrix_multiply_naive();
    clock_t end = clock();

    printf("Done MMM Naive. C[0][0]=%f Time=%.2f ms\n",
           C[0][0], 1000.0 * (end - start) / CLOCKS_PER_SEC);
    return 0;
}
