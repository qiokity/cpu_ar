"""Two-pass assembler for the educational 16-bit CPU."""

from __future__ import annotations

from dataclasses import dataclass
import re


REGISTER_PATTERN = re.compile(r"R[0-7]\Z", re.IGNORECASE)
LABEL_PATTERN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
NUMBER_PATTERN = re.compile(r"(?:[0-9]+|0[xX][0-9A-Fa-f]+)\Z")
WORD_MAX = 0xFFFF
MEMORY_SIZE = 256


class AssemblyError(ValueError):
    """An assembly source error with its original line number."""

    def __init__(self, line_number: int, message: str) -> None:
        self.line_number = line_number
        self.message = message
        super().__init__(f"Line {line_number}: {message}")


@dataclass(frozen=True)
class Instruction:
    opcode: str
    operands: tuple[object, ...]
    index: int
    text: str
    source_line: int


@dataclass(frozen=True)
class AssemblyProgram:
    instructions: tuple[Instruction, ...]
    labels: dict[str, int]


class Assembler:
    """Validates source and resolves labels before producing instructions."""

    def assemble(self, source: str) -> AssemblyProgram:
        if not isinstance(source, str):
            raise TypeError("Assembly source must be text.")

        lines: list[tuple[int, str]] = []
        labels: dict[str, int] = {}

        for line_number, original in enumerate(source.splitlines(), start=1):
            text = original.split(";", 1)[0].strip()
            if not text:
                continue

            if ":" in text:
                if not text.endswith(":") or text.count(":") != 1:
                    raise AssemblyError(
                        line_number, "Labels must appear alone on a line, e.g. LOOP:"
                    )
                label = text[:-1].strip()
                if not LABEL_PATTERN.fullmatch(label):
                    raise AssemblyError(line_number, f"Invalid label name {label!r}.")
                key = label.upper()
                if key in labels:
                    raise AssemblyError(line_number, f"Duplicate label {label!r}.")
                labels[key] = len(lines)
                continue

            lines.append((line_number, text))

        if not lines:
            raise AssemblyError(1, "Program is empty; enter at least one instruction.")

        instructions: list[Instruction] = []
        for index, (line_number, text) in enumerate(lines):
            instructions.append(
                self._parse_instruction(text, line_number, index, labels)
            )
        return AssemblyProgram(tuple(instructions), labels)

    def _parse_instruction(
        self,
        text: str,
        line_number: int,
        index: int,
        labels: dict[str, int],
    ) -> Instruction:
        pieces = text.split(None, 1)
        opcode = pieces[0].upper()
        operand_text = pieces[1].strip() if len(pieces) == 2 else ""
        operands = self._split_operands(operand_text, line_number)

        if opcode == "HALT":
            self._expect_count(opcode, operands, 0, line_number)
            parsed: tuple[object, ...] = ()
        elif opcode == "MOV":
            self._expect_count(opcode, operands, 2, line_number)
            destination = self._register(operands[0], line_number)
            source = operands[1].strip()
            if REGISTER_PATTERN.fullmatch(source):
                parsed = (destination, ("register", source.upper()))
            else:
                parsed = (destination, ("immediate", self._number(source, line_number, WORD_MAX)))
        elif opcode in {"LOAD", "STORE"}:
            self._expect_count(opcode, operands, 2, line_number)
            register = self._register(operands[0], line_number)
            address = self._memory_address(operands[1], line_number)
            parsed = (register, address)
        elif opcode in {"ADD", "SUB", "MUL"}:
            self._expect_count(opcode, operands, 3, line_number)
            parsed = tuple(self._register(value, line_number) for value in operands)
        elif opcode == "CMP":
            self._expect_count(opcode, operands, 2, line_number)
            parsed = tuple(self._register(value, line_number) for value in operands)
        elif opcode in {"JMP", "JZ", "JNZ"}:
            self._expect_count(opcode, operands, 1, line_number)
            target = operands[0].strip()
            if not LABEL_PATTERN.fullmatch(target):
                raise AssemblyError(line_number, f"Invalid branch label {target!r}.")
            key = target.upper()
            if key not in labels:
                raise AssemblyError(line_number, f"Undefined label {target!r}.")
            parsed = (labels[key], target)
        else:
            raise AssemblyError(line_number, f"Unknown opcode {pieces[0]!r}.")

        return Instruction(opcode, parsed, index, text, line_number)

    @staticmethod
    def _split_operands(text: str, line_number: int) -> list[str]:
        if not text:
            return []
        values = text.split(",")
        if any(not value.strip() for value in values):
            raise AssemblyError(line_number, "Malformed operand list; check commas.")
        return [value.strip() for value in values]

    @staticmethod
    def _expect_count(
        opcode: str, operands: list[str], expected: int, line_number: int
    ) -> None:
        if len(operands) != expected:
            raise AssemblyError(
                line_number,
                f"{opcode} expects {expected} operand(s), received {len(operands)}.",
            )

    @staticmethod
    def _register(value: str, line_number: int) -> str:
        register = value.strip().upper()
        if not REGISTER_PATTERN.fullmatch(register):
            raise AssemblyError(line_number, f"Invalid register {value!r}; use R0-R7.")
        return register

    @staticmethod
    def _number(value: str, line_number: int, maximum: int) -> int:
        value = value.strip()
        if not NUMBER_PATTERN.fullmatch(value):
            raise AssemblyError(line_number, f"Invalid unsigned integer {value!r}.")
        number = int(value, 16 if value.lower().startswith("0x") else 10)
        if number > maximum:
            raise AssemblyError(
                line_number, f"Value {value!r} is out of range (0-{maximum})."
            )
        return number

    @classmethod
    def _memory_address(cls, operand: str, line_number: int) -> int:
        match = re.fullmatch(r"\[\s*(.*?)\s*\]", operand)
        if not match:
            raise AssemblyError(
                line_number, f"Invalid memory operand {operand!r}; expected [address]."
            )
        return cls._number(match.group(1), line_number, MEMORY_SIZE - 1)
