#include <stdio.h>
#define SIZE 10000

float A[SIZE], B[SIZE];
float sum = 0;

int main() {
    for (int i = 0; i < SIZE; i++) {
        A[i] = i * 0.5f;
        B[i] = SIZE - i * 0.5f;
    }

    for (int i = 0; i < SIZE; i++) {
        float diff = A[i] - B[i];
        if (diff > 0)
            sum += diff;
    }

    printf("Result: %f\n", sum);
    return 0;
}
