"""Deterministic, non-pipelined CPU execution engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from assembler import AssemblyProgram, Instruction


WORD_MASK = 0xFFFF
MEMORY_SIZE = 256
STAGES = ("FETCH", "DECODE", "EXECUTE", "MEMORY ACCESS", "WRITE BACK")


class ExecutionError(RuntimeError):
    """Raised when an invalid CPU operation is requested."""


@dataclass
class Latches:
    decoded: dict[str, object] = field(default_factory=dict)
    pending_register: Optional[tuple[str, int]] = None
    pending_flags: Optional[tuple[bool, bool]] = None
    memory_value: Optional[int] = None
    pending_halt: bool = False


class CPU:
    """A 16-bit teaching CPU with explicit five-stage instruction execution."""

    def __init__(self, program: Optional[AssemblyProgram] = None) -> None:
        self.program: Optional[AssemblyProgram] = None
        self.registers: dict[str, int] = {}
        self.data_memory: list[int] = []
        self.pc = 0
        self.ir: Optional[str] = None
        self.current_instruction: Optional[Instruction] = None
        self.current_instruction_index: Optional[int] = None
        self.zf = False
        self.cf = False
        self.stage_index = 0
        self.last_stage: Optional[str] = None
        self.status = "Ready"
        self.latches = Latches()
        self.memory_touched: set[int] = set()
        if program is not None:
            self.load_program(program)
        else:
            self._initialize_state()

    def _initialize_state(self) -> None:
        self.registers = {f"R{i}": 0 for i in range(8)}
        self.data_memory = [0] * MEMORY_SIZE
        self.pc = 0
        self.ir = None
        self.current_instruction = None
        self.current_instruction_index = None
        self.zf = False
        self.cf = False
        self.stage_index = 0
        self.last_stage = None
        self.status = "Ready"
        self.latches = Latches()
        self.memory_touched = set()

    @property
    def current_stage(self) -> str:
        """Stage that will run next, unless the CPU has stopped."""
        return STAGES[self.stage_index]

    @property
    def halted(self) -> bool:
        return self.status == "Halted"

    @property
    def completed(self) -> bool:
        return self.status == "Completed"

    @property
    def stopped(self) -> bool:
        return self.status in {"Halted", "Completed", "Error"}

    def load_program(self, program: AssemblyProgram) -> None:
        if not program.instructions:
            raise ExecutionError("Cannot load an empty program.")
        self.program = program
        self._initialize_state()

    def reset(self) -> None:
        if self.program is None:
            raise ExecutionError("No assembled program is loaded.")
        self._initialize_state()

    def advance_stage(self) -> str:
        """Execute exactly one stage and return a truthful event description."""
        if self.program is None:
            raise ExecutionError("Assemble a program before executing.")
        if self.stopped:
            raise ExecutionError(f"Execution has already {self.status.lower()}.")

        stage = STAGES[self.stage_index]
        self.last_stage = stage
        if stage == "FETCH":
            event = self._fetch()
            if self.completed:
                return event
        elif stage == "DECODE":
            event = self._decode()
        elif stage == "EXECUTE":
            event = self._execute()
        elif stage == "MEMORY ACCESS":
            event = self._memory_access()
        else:
            event = self._write_back()

        if stage == "WRITE BACK":
            if self.halted:
                return event
            self.stage_index = 0
        else:
            self.stage_index += 1
        self.status = "Running"
        return event

    def finish_instruction(self) -> list[str]:
        """Advance through the current instruction's remaining stages."""
        if self.program is None:
            raise ExecutionError("Assemble a program before executing.")
        if self.stopped:
            raise ExecutionError(f"Execution has already {self.status.lower()}.")
        events: list[str] = []
        for _ in range(len(STAGES)):
            stage = self.current_stage
            events.append(self.advance_stage())
            if stage == "WRITE BACK" or self.stopped:
                break
        return events

    def _fetch(self) -> str:
        assert self.program is not None
        if not 0 <= self.pc < len(self.program.instructions):
            self.ir = None
            self.current_instruction = None
            self.current_instruction_index = None
            self.status = "Completed"
            return f"Program completed normally: PC {self.pc} is outside instruction memory."

        index = self.pc
        instruction = self.program.instructions[index]
        self.current_instruction_index = index
        self.current_instruction = instruction
        self.ir = instruction.text
        self.pc += 1
        self.latches = Latches()
        return f"Fetched {instruction.text!r} from instruction index {index}; PC is now {self.pc}."

    def _decode(self) -> str:
        instruction = self._require_instruction()
        op = instruction.opcode
        args = instruction.operands
        values: dict[str, object] = {}
        if op == "MOV":
            destination, source = args
            values["destination"] = destination
            if source[0] == "register":
                values["value"] = self.registers[source[1]]
                values["source_register"] = source[1]
                detail = f"register {source[1]} value {values['value']}"
            else:
                values["value"] = source[1]
                detail = f"immediate value {source[1]} from the instruction"
        elif op in {"LOAD", "STORE"}:
            register, address = args
            values.update(register=register, address=address)
            if op == "STORE":
                values["value"] = self.registers[register]
                detail = f"{register} value {values['value']} and data address {address}"
            else:
                detail = f"destination {register} and data address {address}"
        elif op in {"ADD", "SUB", "MUL"}:
            destination, left, right = args
            values.update(
                destination=destination,
                left_register=left,
                right_register=right,
                left=self.registers[left],
                right=self.registers[right],
            )
            detail = f"{left}={values['left']}, {right}={values['right']} -> {destination}"
        elif op == "CMP":
            left, right = args
            values.update(
                left_register=left,
                right_register=right,
                left=self.registers[left],
                right=self.registers[right],
            )
            detail = f"compare {left}={values['left']} with {right}={values['right']}"
        elif op in {"JMP", "JZ", "JNZ"}:
            target, label = args
            values.update(target=target, label=label)
            detail = f"label {label} resolves to instruction index {target}"
        else:
            detail = "halt request"

        self.latches.decoded = values
        return f"Decoded {op}: {detail}."

    def _execute(self) -> str:
        instruction = self._require_instruction()
        op = instruction.opcode
        data = self.latches.decoded
        if op == "MOV":
            self.latches.pending_register = (data["destination"], data["value"])
            return f"Prepared value {data['value']} for {data['destination']}; register write is pending."
        if op in {"ADD", "SUB", "MUL"}:
            left, right = data["left"], data["right"]
            if op == "ADD":
                full = left + right
                result = full & WORD_MASK
                carry = full > WORD_MASK
                operation = f"{left} + {right}"
            elif op == "SUB":
                result = (left - right) & WORD_MASK
                carry = left < right
                operation = f"{left} - {right}"
            else:
                full = left * right
                result = full & WORD_MASK
                carry = full > WORD_MASK
                operation = f"{left} * {right}"
            self.latches.pending_register = (data["destination"], result)
            self.latches.pending_flags = (result == 0, carry)
            return (
                f"ALU calculated {operation} = {result} (0x{result:04X}); "
                f"pending ZF={result == 0}, CF={carry}."
            )
        if op == "CMP":
            left, right = data["left"], data["right"]
            self.latches.pending_flags = (left == right, left < right)
            return (
                f"ALU compared {left} and {right}; pending "
                f"ZF={left == right}, CF={left < right}."
            )
        if op in {"JMP", "JZ", "JNZ"}:
            taken = op == "JMP" or (op == "JZ" and self.zf) or (op == "JNZ" and not self.zf)
            if taken:
                self.pc = data["target"]
                return f"Branch taken to instruction index {self.pc} (label {data['label']})."
            return f"Branch not taken; execution continues at instruction index {self.pc}."
        if op == "LOAD":
            return f"Prepared data-memory address {data['address']} for LOAD into {data['register']}."
        if op == "STORE":
            return f"Prepared {data['value']} from {data['register']} for data-memory address {data['address']}."
        self.latches.pending_halt = True
        return "HALT recorded; execution will stop at the end of Write Back."

    def _memory_access(self) -> str:
        instruction = self._require_instruction()
        data = self.latches.decoded
        if instruction.opcode == "LOAD":
            address = data["address"]
            self.latches.memory_value = self.data_memory[address]
            self.memory_touched.add(address)
            return f"Loaded value {self.latches.memory_value} from data memory address {address}; register write is pending."
        if instruction.opcode == "STORE":
            address, value = data["address"], data["value"]
            self.data_memory[address] = value
            self.memory_touched.add(address)
            return f"Stored value {value} at data memory address {address}."
        return f"No data-memory operation for {instruction.opcode}."

    def _write_back(self) -> str:
        instruction = self._require_instruction()
        messages: list[str] = []
        if instruction.opcode == "LOAD":
            assert self.latches.memory_value is not None
            self.latches.pending_register = (
                self.latches.decoded["register"],
                self.latches.memory_value,
            )
        if self.latches.pending_register is not None:
            register, value = self.latches.pending_register
            self.registers[register] = value
            messages.append(f"Wrote {value} (0x{value:04X}) to {register} during Write Back.")
            self.latches.pending_register = None
        if self.latches.pending_flags is not None:
            self.zf, self.cf = self.latches.pending_flags
            messages.append(f"Committed flags ZF={self.zf}, CF={self.cf} during Write Back.")
            self.latches.pending_flags = None
        if self.latches.pending_halt:
            self.status = "Halted"
            messages.append("Program halted.")
        if not messages:
            messages.append(f"No register or flag write was required for {instruction.opcode}.")
        return " ".join(messages)

    def _require_instruction(self) -> Instruction:
        if self.current_instruction is None:
            raise ExecutionError("There is no fetched instruction to advance.")
        return self.current_instruction
