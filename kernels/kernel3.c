#include <stdio.h>
#define SIZE 10000

float A[SIZE], B[SIZE], C[SIZE], D[SIZE], E[SIZE];
float out1 = 0, out2 = 0, out3 = 0, out4 = 0, out5 = 0;

int main() {
    for (int i = 0; i < SIZE; i++) {
        A[i] = i * 0.1f;
        B[i] = i * 0.2f;
        C[i] = i * 0.3f;
        D[i] = i * 0.4f;
        E[i] = i * 0.5f;
    }

    for (int i = 0; i < SIZE; i++) {
        out1 += A[i] * 1.1f;
        out2 += B[i] * 1.2f;
        out3 += C[i] * 1.3f;
        out4 += D[i] * 1.4f;
        out5 += E[i] * 1.5f;
    }

    float final = out1 + out2 + out3 + out4 + out5;
    printf("Final result: %f\n", final);
    return 0;
}
