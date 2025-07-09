// branch_unoptimized.c
#include <stdio.h>
#include <stdlib.h>

#define N 100000
int A[N];

int main() {
    for (int i = 0; i < N; i++)
        A[i] = rand() % 100;

    int sum = 0;
    for (int i = 0; i < N; i++) {
        if (A[i] % 2 == 0)  // unpredictable branch
            sum += A[i];
    }

    printf("Sum = %d\n", sum);
    return 0;
}
