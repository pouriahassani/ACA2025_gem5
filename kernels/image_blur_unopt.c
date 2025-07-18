#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define WIDTH 512
#define HEIGHT 512
#define KERNEL_SIZE 5

// Cache-unfriendly image blur
// Students need to optimize this for better cache performance
void image_blur(unsigned char **input, unsigned char **output, int width, int height) {
    int kernel[KERNEL_SIZE][KERNEL_SIZE] = {
        {1, 1, 1, 1, 1},
        {1, 2, 2, 2, 1},
        {1, 2, 3, 2, 1},
        {1, 2, 2, 2, 1},
        {1, 1, 1, 1, 1}
    };
    int kernel_sum = 35;
    int offset = KERNEL_SIZE / 2;
    
    // Column-major access pattern for poor cache locality
    for (int x = offset; x < width - offset; x++) {
        for (int y = offset; y < height - offset; y++) {  // Swapped loops
            int sum = 0;
            
            // Apply convolution kernel with poor access pattern
            for (int kx = -offset; kx <= offset; kx++) {  // Swapped kernel loops too
                for (int ky = -offset; ky <= offset; ky++) {
                    sum += input[y + ky][x + kx] * kernel[ky + offset][kx + offset];
                }
            }
            
            output[y][x] = sum / kernel_sum;
        }
    }
}

unsigned char** allocate_image(int width, int height) {
    unsigned char **image = (unsigned char**)malloc(height * sizeof(unsigned char*));
    for (int i = 0; i < height; i++) {
        image[i] = (unsigned char*)malloc(width * sizeof(unsigned char));
    }
    return image;
}

void free_image(unsigned char **image, int height) {
    for (int i = 0; i < height; i++) {
        free(image[i]);
    }
    free(image);
}

void initialize_image(unsigned char **image, int width, int height) {
    // Column-major initialization for poor locality
    for (int x = 0; x < width; x++) {
        for (int y = 0; y < height; y++) {
            image[y][x] = (x + y) % 256;  // Deterministic pattern
        }
    }
}

int main() {
    unsigned char **input = allocate_image(WIDTH, HEIGHT);
    unsigned char **output = allocate_image(WIDTH, HEIGHT);
    
    initialize_image(input, WIDTH, HEIGHT);
    
    clock_t start = clock();
    image_blur(input, output, WIDTH, HEIGHT);
    clock_t end = clock();
    
    double time_taken = ((double)(end - start)) / CLOCKS_PER_SEC;
    printf("Image blur completed in %f seconds\n", time_taken);
    printf("Result checksum: output[100][100] = %d, output[200][200] = %d\n", 
           output[100][100], output[200][200]);
    
    free_image(input, HEIGHT);
    free_image(output, HEIGHT);
    
    return 0;
}