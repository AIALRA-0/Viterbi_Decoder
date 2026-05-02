from __future__ import annotations

from pathlib import Path

from model.channel import flip_positions, hard_to_soft3, no_noise
from model.conv_encoder import encode_bits, terminated_payload
from model.trellis import load_code_spec
from model.viterbi_golden import decode_hard, decode_soft3


SPEC_PATH = Path("spec/viterbi_spec.json")


def first_mismatch(expected: list[int], actual: list[int]) -> int | None:
    for idx, (left, right) in enumerate(zip(expected, actual)):
        if left != right:
            return idx
    if len(expected) != len(actual):
        return min(len(expected), len(actual))
    return None


def assert_zero_mismatch(expected: list[int], actual: list[int]) -> None:
    mismatch = first_mismatch(expected, actual)
    assert mismatch is None, f"first mismatch at bit {mismatch}: expected={expected[mismatch]} actual={actual[mismatch]}"


def test_k3_smoke_no_noise_zero_mismatch():
    spec = load_code_spec(SPEC_PATH, "smoke_test")
    payload = [1, 0, 1, 1, 0, 0, 1]
    encoded = encode_bits(payload, spec)
    decoded = decode_hard(no_noise(encoded), spec, decoded_length=len(payload)).decoded_bits
    assert_zero_mismatch(payload, decoded)


def test_k3_smoke_soft3_no_noise_zero_mismatch():
    spec = load_code_spec(SPEC_PATH, "smoke_test")
    payload = [1, 1, 0, 1, 0, 1]
    encoded = encode_bits(payload, spec)
    soft = hard_to_soft3(encoded)
    decoded = decode_soft3(soft, spec, decoded_length=len(payload)).decoded_bits
    assert_zero_mismatch(payload, decoded)


def test_k7_formal_no_noise_zero_mismatch():
    spec = load_code_spec(SPEC_PATH, "code")
    payload = [
        1, 0, 0, 1, 1, 0, 1, 0,
        1, 1, 1, 0, 0, 0, 1, 0,
        1, 0, 1, 1, 0, 1, 0, 0,
        1, 1, 0, 0, 1, 0, 1, 1,
    ]
    encoded = encode_bits(payload, spec)
    decoded = decode_hard(no_noise(encoded), spec, decoded_length=len(payload)).decoded_bits
    assert_zero_mismatch(payload, decoded)


def test_k7_formal_tail_termination_returns_to_zero_state():
    spec = load_code_spec(SPEC_PATH, "code")
    payload = [1, 0, 1, 1, 1, 0, 0, 1]
    encoded = encode_bits(payload, spec)
    expected = terminated_payload(payload, spec)
    result = decode_hard(encoded, spec, decoded_length=len(expected))
    assert result.final_state == 0
    assert_zero_mismatch(expected, result.decoded_bits)


def test_k7_single_encoded_bit_error_is_corrected_for_small_case():
    spec = load_code_spec(SPEC_PATH, "code")
    payload = [1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1]
    encoded = encode_bits(payload, spec)
    received = flip_positions(encoded, [7])
    decoded = decode_hard(received, spec, decoded_length=len(payload)).decoded_bits
    assert_zero_mismatch(payload, decoded)
