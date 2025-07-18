#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define SIZE 256

// Cache-unfriendly matrix multiplication
// Students need to optimize this for better cache performance
void matrix_multiply(double **A, double **B, double **C, int n) {
    // Poor cache locality - accessing B column-wise
    for (int i = 0; i < n; i++) {
        for (int k = 0; k < n; k++) {
            for (int j = 0; j < n; j++) {
                C[i][j] += A[i][k] * B[k][j];  // B[k][j] has poor spatial locality
            }
        }
    }
}

double** allocate_matrix(int n) {
    double **matrix = (double**)malloc(n * sizeof(double*));
    for (int i = 0; i < n; i++) {
        matrix[i] = (double*)malloc(n * sizeof(double));
    }
    return matrix;
}

void free_matrix(double **matrix, int n) {
    for (int i = 0; i < n; i++) {
        free(matrix[i]);
    }
    free(matrix);
}

void initialize_matrix(double **matrix, int n) {
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            matrix[i][j] = (double)(rand() % 100) / 10.0;
        }
    }
}

void zero_matrix(double **matrix, int n) {
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            matrix[i][j] = 0.0;
        }
    }
}

int main() {
    srand(42);  // Fixed seed for reproducible results
    
    double **A = allocate_matrix(SIZE);
    double **B = allocate_matrix(SIZE);
    double **C = allocate_matrix(SIZE);
    
    initialize_matrix(A, SIZE);
    initialize_matrix(B, SIZE);
    zero_matrix(C, SIZE);
    
    clock_t start = clock();
    matrix_multiply(A, B, C, SIZE);
    clock_t end = clock();
    
    double time_taken = ((double)(end - start)) / CLOCKS_PER_SEC;
    printf("Matrix multiplication completed in %f seconds\n", time_taken);
    printf("Result checksum: C[0][0] = %f, C[100][100] = %f\n", C[0][0], C[100][100]);
    
    free_matrix(A, SIZE);
    free_matrix(B, SIZE);
    free_matrix(C, SIZE);
    
    return 0;
}