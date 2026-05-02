from __future__ import annotations

from collections.abc import Iterable
import math
import random


def _bits(bits: Iterable[int]) -> list[int]:
    values = [int(bit) for bit in bits]
    bad = [bit for bit in values if bit not in (0, 1)]
    if bad:
        raise ValueError(f"Bits must be 0 or 1, got {bad[:4]}")
    return values


def no_noise(bits: Iterable[int]) -> list[int]:
    return _bits(bits)


def flip_positions(bits: Iterable[int], positions: Iterable[int]) -> list[int]:
    values = _bits(bits)
    for pos in positions:
        if pos < 0 or pos >= len(values):
            raise IndexError(f"Flip position out of range: {pos}")
        values[pos] ^= 1
    return values


def burst_error(bits: Iterable[int], start: int, length: int) -> list[int]:
    return flip_positions(bits, range(start, start + length))


def hard_to_soft3(bits: Iterable[int], low: int = 0, high: int = 7) -> list[int]:
    return [high if bit else low for bit in _bits(bits)]


def awgn_soft3(bits: Iterable[int], snr_db: float, seed: int) -> list[int]:
    rng = random.Random(seed)
    sigma = 1.0 / math.sqrt(2.0 * (10.0 ** (snr_db / 10.0)))
    symbols: list[int] = []
    for bit in _bits(bits):
        ideal = 1.0 if bit else -1.0
        noisy = ideal + rng.gauss(0.0, sigma)
        quantized = round((noisy + 1.0) * 3.5)
        symbols.append(max(0, min(7, quantized)))
    return symbols

