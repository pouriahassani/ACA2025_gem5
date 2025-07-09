#include <stdio.h>
#include <stdlib.h>
#define SIZE 10000

float h[SIZE], w[SIZE];
int idx[SIZE];

int main() {
    for (int i = 0; i < SIZE; i++) {
        h[i] = i;
        w[i] = SIZE - i;
        idx[i] = rand() % SIZE;  // Random access pattern
    }

    for (int i = 0; i < SIZE; i++) {
        h[idx[i]] += w[i];  // Random write – cache unfriendly
    }

    printf("Done.\n");
    return 0;
}
