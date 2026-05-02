from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class CodeSpec:
    name: str
    rate: str
    constraint_length: int
    polynomials_octal: tuple[int, ...]
    tail_termination: str
    state_count: int

    @property
    def output_count(self) -> int:
        left, right = self.rate.split("/")
        if int(left) != 1:
            raise ValueError(f"Only rate 1/n is supported, got {self.rate}")
        return int(right)

    @property
    def state_mask(self) -> int:
        return self.state_count - 1

    @property
    def tail_bits(self) -> list[int]:
        if self.tail_termination != "zero_tail":
            raise ValueError(f"Unsupported tail termination: {self.tail_termination}")
        return [0] * (self.constraint_length - 1)


@dataclass(frozen=True)
class Transition:
    state: int
    input_bit: int
    next_state: int
    output_bits: tuple[int, ...]


def _parse_octal(value: int | str) -> int:
    return int(str(value), 8)


def load_project_spec(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_code_spec(path: str | Path, section: str = "code") -> CodeSpec:
    data = load_project_spec(path)[section]
    polynomials = tuple(_parse_octal(v) for v in data["polynomials_octal"])
    spec = CodeSpec(
        name=section,
        rate=data["rate"],
        constraint_length=int(data["constraint_length"]),
        polynomials_octal=polynomials,
        tail_termination=data["tail_termination"],
        state_count=int(data["state_count"]),
    )
    expected_states = 1 << (spec.constraint_length - 1)
    if spec.state_count != expected_states:
        raise ValueError(
            f"{section} state_count={spec.state_count} does not match K={spec.constraint_length}"
        )
    if len(spec.polynomials_octal) != spec.output_count:
        raise ValueError(f"{section} polynomial count does not match rate {spec.rate}")
    return spec


def parity(value: int) -> int:
    return value.bit_count() & 1


def state_bits(state: int, spec: CodeSpec) -> list[int]:
    return [(state >> i) & 1 for i in range(spec.constraint_length - 1)]


def output_bits(input_bit: int, state: int, spec: CodeSpec) -> tuple[int, ...]:
    register = input_bit | (state << 1)
    mask = (1 << spec.constraint_length) - 1
    register &= mask
    return tuple(parity(register & polynomial) for polynomial in spec.polynomials_octal)


def next_state(input_bit: int, state: int, spec: CodeSpec) -> int:
    return ((state << 1) | input_bit) & spec.state_mask


def transition(input_bit: int, state: int, spec: CodeSpec) -> Transition:
    if input_bit not in (0, 1):
        raise ValueError(f"input_bit must be 0 or 1, got {input_bit}")
    return Transition(
        state=state,
        input_bit=input_bit,
        next_state=next_state(input_bit, state, spec),
        output_bits=output_bits(input_bit, state, spec),
    )


def build_trellis(spec: CodeSpec) -> dict[int, dict[int, Transition]]:
    return {
        state: {bit: transition(bit, state, spec) for bit in (0, 1)}
        for state in range(spec.state_count)
    }


def pair_symbols(bits: Iterable[int], output_count: int) -> list[tuple[int, ...]]:
    values = list(bits)
    if len(values) % output_count != 0:
        raise ValueError(f"Expected a multiple of {output_count} bits, got {len(values)}")
    return [
        tuple(int(v) for v in values[i : i + output_count])
        for i in range(0, len(values), output_count)
    ]

