#ifndef VITERBI_ZU4EV_VECTORS_H
#define VITERBI_ZU4EV_VECTORS_H

#include <stdint.h>

#define VITERBI_MAX_INPUT_LENGTH 204U
#define VITERBI_MAX_OUTPUT_LENGTH 96U

typedef struct {
    const char *name;
    const char *run_id;
    uint32_t input_length;
    uint32_t output_length;
    const int16_t *input;
    const int16_t *golden;
} viterbi_vector_case_t;

extern const int16_t viterbi_case_no_noise_input[204];
extern const int16_t viterbi_case_no_noise_golden[96];

extern const int16_t viterbi_case_single_bit_error_input[204];
extern const int16_t viterbi_case_single_bit_error_golden[96];

extern const int16_t viterbi_case_soft_awgn_2db_input[204];
extern const int16_t viterbi_case_soft_awgn_2db_golden[96];

extern const viterbi_vector_case_t g_viterbi_vector_cases[3];
extern const uint32_t g_viterbi_vector_case_count;

#endif
