from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from math import inf

from .trellis import CodeSpec, build_trellis, pair_symbols


@dataclass(frozen=True)
class DecodeResult:
    decoded_bits: list[int]
    final_state: int
    path_metric: int


def _hamming_metric(rx_symbol: tuple[int, ...], expected: tuple[int, ...]) -> int:
    return sum(int(a != b) for a, b in zip(rx_symbol, expected))


def _soft3_metric(rx_symbol: tuple[int, ...], expected: tuple[int, ...]) -> int:
    return sum(abs(int(value) - (7 if bit else 0)) for value, bit in zip(rx_symbol, expected))


def decode(
    received: Iterable[int],
    spec: CodeSpec,
    decision_mode: str = "hard",
    decoded_length: int | None = None,
    path_metric_width: int | None = None,
    normalization: str = "none",
) -> DecodeResult:
    symbols = pair_symbols(received, spec.output_count)
    trellis = build_trellis(spec)
    metrics = [inf] * spec.state_count
    metrics[0] = 0
    survivors: list[list[tuple[int, int] | None]] = []

    if decision_mode == "hard":
        branch_metric = _hamming_metric
    elif decision_mode == "soft3":
        branch_metric = _soft3_metric
    else:
        raise ValueError(f"Unsupported decision mode: {decision_mode}")

    for rx_symbol in symbols:
        next_metrics = [inf] * spec.state_count
        next_survivors: list[tuple[int, int] | None] = [None] * spec.state_count
        for state, metric in enumerate(metrics):
            if metric == inf:
                continue
            for input_bit, step in trellis[state].items():
                candidate = metric + branch_metric(rx_symbol, step.output_bits)
                old = next_metrics[step.next_state]
                if candidate < old:
                    next_metrics[step.next_state] = candidate
                    next_survivors[step.next_state] = (state, input_bit)
        if path_metric_width is not None:
            max_metric = (1 << path_metric_width) - 1
            next_metrics = [
                min(value, max_metric) if value != inf else value
                for value in next_metrics
            ]
        if normalization == "subtract_min":
            finite = [value for value in next_metrics if value != inf]
            if finite:
                minimum = min(finite)
                next_metrics = [
                    value - minimum if value != inf else value
                    for value in next_metrics
                ]
        elif normalization != "none":
            raise ValueError(f"Unsupported normalization: {normalization}")
        metrics = next_metrics
        survivors.append(next_survivors)

    if spec.tail_termination == "zero_tail":
        final_state = 0
    else:
        final_state = min(range(spec.state_count), key=lambda state: metrics[state])

    decoded_reversed: list[int] = []
    state = final_state
    for step_survivors in reversed(survivors):
        item = step_survivors[state]
        if item is None:
            raise ValueError(f"No survivor path for state {state}")
        prev_state, input_bit = item
        decoded_reversed.append(input_bit)
        state = prev_state
    decoded_bits = list(reversed(decoded_reversed))
    if decoded_length is not None:
        decoded_bits = decoded_bits[:decoded_length]
    return DecodeResult(
        decoded_bits=decoded_bits,
        final_state=final_state,
        path_metric=int(metrics[final_state]),
    )


def decode_hard(
    received: Iterable[int],
    spec: CodeSpec,
    decoded_length: int | None = None,
    path_metric_width: int | None = None,
    normalization: str = "none",
) -> DecodeResult:
    return decode(
        received,
        spec,
        decision_mode="hard",
        decoded_length=decoded_length,
        path_metric_width=path_metric_width,
        normalization=normalization,
    )


def decode_soft3(
    received: Iterable[int],
    spec: CodeSpec,
    decoded_length: int | None = None,
    path_metric_width: int | None = None,
    normalization: str = "none",
) -> DecodeResult:
    return decode(
        received,
        spec,
        decision_mode="soft3",
        decoded_length=decoded_length,
        path_metric_width=path_metric_width,
        normalization=normalization,
    )
