#define N 100000
float A = 0;

int main() {
    for (int i = 0; i < N; i++) {
        A = A + 1.0f;  // dependent on previous result
    }
    printf("Final A = %f\n", A);
    return 0;
}