from __future__ import annotations

from collections.abc import Iterable

from .trellis import CodeSpec, transition


def _validate_bits(bits: Iterable[int]) -> list[int]:
    values = [int(bit) for bit in bits]
    bad = [bit for bit in values if bit not in (0, 1)]
    if bad:
        raise ValueError(f"Bits must be 0 or 1, got {bad[:4]}")
    return values


def encode_bits(bits: Iterable[int], spec: CodeSpec, terminate: bool = True) -> list[int]:
    payload = _validate_bits(bits)
    stream = payload + (spec.tail_bits if terminate else [])
    state = 0
    encoded: list[int] = []
    for bit in stream:
        step = transition(bit, state, spec)
        encoded.extend(step.output_bits)
        state = step.next_state
    return encoded


def terminated_payload(bits: Iterable[int], spec: CodeSpec) -> list[int]:
    return _validate_bits(bits) + spec.tail_bits

