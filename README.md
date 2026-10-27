# CPU Architecture & Instruction Execution Visualizer

An interactive Python desktop simulator for exploring how a small CPU fetches,
decodes, executes, accesses memory, and writes back instructions. Write assembly
in the editor, assemble it, then observe real CPU state changes one stage or one
instruction at a time.

## Problem and objectives

CPU components and instruction execution can be difficult to understand from
static diagrams alone. This project provides a hands-on, deterministic model
with visible registers, flags, separate instruction/data memories, an annotated
datapath, and a chronological execution log.

## Features and technology

- Python 3.10+, standard-library Tkinter/ttk/Canvas, and `unittest`.
- Two-pass assembler with case-insensitive register/opcode names, comments,
  labels, decimal and hexadecimal literals, and line-numbered errors.
- Eight editable general-purpose registers, PC, IR, ZF/CF, and 256 data words.
- Five explicit execution stages, stepped independently or animated with
  Tkinter's event loop.
- Resizable dark GUI with source-line highlighting, stage explanations,
  registers, memory inspection, and execution log.
- Three runnable example programs.

No third-party packages, network connection, database, or external service is
required.

## Simplified CPU architecture

This is a teaching simulator, not a cycle-accurate model of Intel, AMD, ARM,
RISC-V, or any other commercial processor. It is a 16-bit unsigned,
non-pipelined CPU: one instruction moves through all five stages before another
instruction starts.

```text
                         instruction path
   PC (next index) ──> Instruction Memory ──> IR ──> Control Unit
      ↑                                               │
      └──────────── branch target/control ────────────┘
                                                     │
   Registers R0-R7 ── operands ──> ALU ── result ───┤
          ↑                         │                │
          └──── LOAD data ── Data Memory <── STORE ─┘
                                  │
                             Flags: ZF, CF
```

- **PC:** zero-based instruction index of the next instruction to fetch. Fetch
  copies that instruction to IR, then increments PC. Branches may replace PC.
- **IR:** textual form of the currently fetched instruction; displayed
  separately from the incremented PC.
- **Registers:** R0–R7 are all writable and start at zero. Values range from
  0 through 65535.
- **Control Unit:** interprets instructions and resolves branch decisions.
- **ALU:** performs unsigned arithmetic and comparisons.
- **ZF / CF:** Zero and Carry flags; both initially clear.
- **Instruction Memory:** stores assembled instructions and is separate from
  the 256-word **Data Memory** (a simplified Harvard-style organization).
  Data addresses are 0–255; words start at zero.

### Five instruction-cycle stages

1. **Fetch** — read instruction at PC into IR and increment PC; reaching the
   end of instruction memory completes normally.
2. **Decode** — interpret operands and capture source values in latches.
3. **Execute** — calculate an ALU result, compare operands, or decide a branch.
4. **Memory Access** — LOAD reads data memory or STORE writes it exactly once.
5. **Write Back** — commit destination register and pending arithmetic flags;
   HALT takes effect at the end of this stage.

This is not a pipeline: the five stage labels describe the sequential lifecycle
of one instruction, not simultaneous work on five instructions.

## Instruction set

Opcodes and register names are case-insensitive. Labels occupy their own lines,
are case-insensitive, and match `[A-Za-z_][A-Za-z0-9_]*`. Comments begin with
`;`. Decimal and `0x`/`0X` hexadecimal unsigned literals are supported.

| Instruction | Syntax | Meaning |
| --- | --- | --- |
| MOV | `MOV Rd, operand` | Copy an unsigned 16-bit immediate or register value. |
| LOAD | `LOAD Rd, [address]` | Read data memory (address 0–255). |
| STORE | `STORE Rs, [address]` | Write a register value to data memory. |
| ADD | `ADD Rd, Ra, Rb` | Add unsigned register values, modulo 65536. |
| SUB | `SUB Rd, Ra, Rb` | Subtract unsigned values, modulo 65536. |
| MUL | `MUL Rd, Ra, Rb` | Multiply and retain the low 16 bits. |
| CMP | `CMP Ra, Rb` | Compare unsigned values without changing registers. |
| JMP | `JMP label` | Unconditional branch. |
| JZ | `JZ label` | Branch if the committed ZF is set. |
| JNZ | `JNZ label` | Branch if the committed ZF is clear. |
| HALT | `HALT` | Stop after the instruction's Write Back stage. |

ADD sets CF when its full sum exceeds 65535; SUB sets CF when the left operand
is less than the right (CF is a borrow flag for SUB); MUL sets CF when its full
product exceeds 65535. Arithmetic sets ZF when the stored 16-bit result is zero.
CMP sets ZF when operands are equal and CF when the first operand is smaller.
Arithmetic and CMP flags are committed at Write Back. MOV, LOAD, STORE, branches,
and HALT leave flags unchanged. Signed arithmetic and signed comparison are
not implemented.

## Requirements and launch

Use Python 3.10 or later. Tkinter is included with many Python distributions;
some Linux installations require a separate OS package (often named
`python3-tk`).

From this project directory:

```bash
python main.py
```

Choose an example or edit the source, select **Assemble**, then use **Step
Stage**, **Step Instruction**, **Run**, **Pause**, and **Reset**. The speed
slider controls the delay between animated stages. The memory tab shows the
first 16 cells and cells touched by the program; use its inspector for any
address from 0 to 255.

The three examples are checked by running them through the CPU engine:

1. **Arithmetic and memory:** R1=10, R2=20, R3=30, memory[100]=30, then halted.
2. **Loop and conditional branch:** R1=0, R2=15, R3=1, memory[100]=15, and ZF
   is set by the final CMP before the loop exits.
3. **Load and reuse memory:** R1=42, memory[10]=42, R2=42, R3=8, R4=50, then
   halted.

## Tests

Run the automated engine and assembler tests without starting the GUI:

```bash
python -m unittest discover -s tests -v
```

## Project structure

```text
cpu-architecture-visualizer/
├── main.py          # Tkinter interface and Canvas datapath
├── cpu.py           # CPU state and five-stage execution engine
├── assembler.py     # Source validation and two-pass label resolution
├── samples.py       # Shared sample programs for GUI and tests
├── README.md
└── tests/
    └── test_cpu.py
```

## Limitations and future extensions

This compact simulator has only the listed instructions, eight general-purpose
registers, unsigned 16-bit words, and fixed 256-word data memory. It has no
interrupts, stack, addressing modes, directives, macros, pipelining, or
cycle-accurate timing. Possible extensions include a larger instruction set,
configurable memory, and additional educational views of control signals.
