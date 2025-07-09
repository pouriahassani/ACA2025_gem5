#include <stdio.h>
#define SIZE 100000

float result = 1.0;

int main() {
    for (int i = 0; i < SIZE; i++) {
        result = result * 1.00001f - 0.00001f;
    }

    printf("Final result: %f\n", result);
    return 0;
}
