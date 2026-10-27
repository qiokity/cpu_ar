# PROJECT DEVELOPMENT PROMPT: CPU ARCHITECTURE AND INSTRUCTION EXECUTION VISUALIZER

You are an expert Python developer, computer architecture educator, GUI designer, and software tester. Your task is to build a complete, working, polished Python mini-project titled:

**“Visualization of CPU Architecture and How Instructions Get Executed: An Interactive CPU Simulator”**

I am a BTech Computer Science student submitting this as a Python mini-project. The application must be understandable, visually impressive, educationally accurate for its simplified CPU model, and achievable as a small project.

Do not merely explain how to implement the project or provide isolated code snippets. Inspect the current workspace, create the required files, implement the complete application, run the available tests, identify and fix bugs, and leave the workspace in a usable state.

Do not ask me questions. Follow the explicit specifications below and make sensible decisions only where implementation details are unspecified.

## 1. PRIMARY OBJECTIVE

Create a desktop application that visually explains CPU architecture and demonstrates how machine instructions are executed internally.

The application must let a user enter a small assembly-like program, load it into a simulated instruction memory, and observe its execution step by step.

The application must show:

- The Program Counter (PC).
- The Instruction Register (IR).
- Eight general-purpose registers, R0 through R7.
- The Arithmetic Logic Unit (ALU).
- The Control Unit.
- Instruction memory.
- Data memory.
- Data paths and buses between CPU components.
- The current instruction and execution stage.
- Changes to registers, memory, flags, and the Program Counter.
- A chronological execution log explaining what happens during execution.

The central feature is an interactive graphical visualization of the CPU, with components and data paths highlighted as instructions progress through the instruction cycle.

This must be a real, functional simulator. Do not implement a static diagram with fake register values, predetermined animations, or hardcoded execution results.

## 2. TECHNOLOGY AND PROJECT CONSTRAINTS

Use the following technology stack:

- Python 3.10 or later.
- Tkinter and tkinter.ttk for the desktop GUI.
- Tkinter Canvas for drawing the CPU architecture, buses, arrows, and visual highlights.
- Python's standard library for the CPU simulator and assembler.
- Python's unittest framework for automated tests.

Do not require third-party packages.

Do not use a browser interface, Flask, Django, Streamlit, Pygame, React, a database, an online service, or an external API.

The application must run locally and work without an internet connection.

Use a modular architecture that separates CPU execution logic, assembly parsing, GUI code, and tests.

Use clear names, sensible type hints, dataclasses where useful, and comments that explain educationally important details. Avoid unnecessary abstractions and excessive complexity.

## 3. REQUIRED PROJECT STRUCTURE

Create the following project structure:

cpu-architecture-visualizer/
├── main.py
├── cpu.py
├── assembler.py
├── README.md
└── tests/
    └── test_cpu.py

Responsibilities:

- `main.py`: Tkinter application, CPU architecture diagram, controls, animation, registers display, memory display, stage indicator, and execution log.
- `cpu.py`: CPU state, registers, flags, instruction execution, execution stages, program counter, and data memory.
- `assembler.py`: Assembly source parsing, label resolution, instruction validation, and useful error messages.
- `tests/test_cpu.py`: Automated tests for the assembler and CPU execution engine.
- `README.md`: Project overview, features, architecture, instruction set, requirements, setup, usage, examples, testing, and limitations.

You may add a small supporting module only if it is genuinely necessary. Prefer the structure above.

## 4. DEFINE THE CPU MODEL EXPLICITLY

Implement a simplified educational 16-bit CPU.

The application must clearly explain that this is a teaching simulator, not a cycle-accurate simulation of an actual Intel, AMD, ARM, or RISC-V processor.

Use this specification consistently throughout the entire codebase.

### 4.1 Word size

The CPU uses 16-bit unsigned register values.

The legal value range is:

0 through 65535, inclusive.

Arithmetic results are stored modulo 65536.

For example:

65535 + 1 produces 0 in the destination register, with the Carry Flag set.

### 4.2 Registers

Implement eight general-purpose registers:

R0, R1, R2, R3, R4, R5, R6, R7.

All eight registers are writable. R0 is NOT a hardwired zero register.

All registers initially contain zero.

Display their values in decimal and four-digit hexadecimal, for example:

R1 = 30 | 0x001E

### 4.3 Program Counter

The Program Counter identifies an instruction by its zero-based instruction index in instruction memory.

It is not a byte address.

Before fetching an instruction, PC identifies the next instruction to fetch.

During the Fetch stage:

1. Read the instruction at the current PC.
2. Copy it into the Instruction Register.
3. Increment PC by one.

If a branch instruction executes, it may replace PC with the target instruction index.

Display the PC value and the currently executing instruction separately. This is important because PC normally points to the next instruction after a fetch.

### 4.4 Instruction Register

IR stores the currently fetched instruction.

Display its textual assembly representation in the GUI.

### 4.5 Instruction memory and data memory

Use separate instruction memory and data memory. This is a simplified Harvard-style educational model.

Instruction memory contains the assembled program.

Data memory contains exactly 256 words, addressed from 0 to 255. Each word is a 16-bit unsigned value.

All data memory cells initially contain zero.

The architecture diagram and README must clearly identify instruction memory and data memory as separate components.

## 5. IMPLEMENT A REAL ASSEMBLER

Implement an assembler that converts user-entered assembly source into validated instruction objects.

Do not execute raw, unvalidated text directly.

The assembler must support:

- Case-insensitive opcodes and register names.
- Blank lines.
- Comments beginning with a semicolon (`;`).
- Labels written on separate lines, such as `LOOP:`.
- Labels as branch targets.
- Decimal integer literals.
- Hexadecimal integer literals prefixed with `0x` or `0X`.
- Clear validation errors containing the source line number and the reason for the error.

Label names must follow this pattern:

`^[A-Za-z_][A-Za-z0-9_]*$`

Labels are case-insensitive. Duplicate labels must be rejected.

For simplicity, labels must occupy their own lines. Do not support directives, macros, indirect addressing, or multiple instructions on a single line.

The assembler must perform the required passes to resolve labels and validate instructions before execution begins.

Each assembled instruction must retain enough source information to display its instruction index, original instruction text, and source line number.

Reject malformed syntax, unsupported instructions, undefined labels, duplicate labels, invalid register names, invalid operand counts, and invalid numeric values.

Do not silently ignore mistakes or silently convert malformed input to a different instruction.

### 5.1 Instruction set

Implement these instructions with precisely the following syntax.

**MOV — Copy an immediate value or register**

`MOV Rd, operand`

Examples:

`MOV R1, 10`

`MOV R2, 0x002A`

`MOV R3, R1`

The destination must be a register. The operand may be a register or an unsigned 16-bit integer.

**LOAD — Read data memory**

`LOAD Rd, [address]`

Example:

`LOAD R1, [100]`

Read the value at the specified data memory address and write it to Rd.

**STORE — Write data memory**

`STORE Rs, [address]`

Example:

`STORE R1, [100]`

Write the value of Rs to the specified data memory address.

The address must be an integer from 0 through 255, inclusive.

**ADD — Addition**

`ADD Rd, Ra, Rb`

Example:

`ADD R3, R1, R2`

Calculate Ra + Rb and write the 16-bit result into Rd.

**SUB — Subtraction**

`SUB Rd, Ra, Rb`

Example:

`SUB R3, R1, R2`

Calculate Ra - Rb and write the 16-bit result into Rd, using modulo-65536 arithmetic.

**MUL — Multiplication**

`MUL Rd, Ra, Rb`

Example:

`MUL R3, R1, R2`

Calculate Ra × Rb and write the lower 16 bits into Rd.

**CMP — Compare**

`CMP Ra, Rb`

Example:

`CMP R1, R2`

Compare the two register values without modifying either register.

Update the Zero Flag and Carry Flag according to the flag rules specified below.

**JMP — Unconditional jump**

`JMP label`

Example:

`JMP LOOP`

Set PC to the resolved instruction index of the label.

**JZ — Jump if zero**

`JZ label`

Jump if the Zero Flag is set.

**JNZ — Jump if not zero**

`JNZ label`

Jump if the Zero Flag is not set.

**HALT — Stop execution**

`HALT`

Finish the program execution and prevent further instruction stages from executing until the program is reset.

No other instructions are required. Do not claim to support instructions that have not been implemented.

## 6. DEFINE FLAGS AND ARITHMETIC PRECISELY

Implement two flags:

- ZF: Zero Flag.
- CF: Carry Flag.

Both flags initially contain false.

Use these rules:

For ADD:

- Calculate the full, unmasked sum.
- Store the sum modulo 65536.
- Set CF if the full sum exceeds 65535.
- Set ZF if the stored result is zero.

For SUB:

- Store the result modulo 65536.
- Set CF if the unsigned left operand is smaller than the unsigned right operand. In this simulator, CF represents borrow for subtraction.
- Set ZF if the stored result is zero.

For MUL:

- Calculate the full product.
- Store the lower 16 bits.
- Set CF if the full product exceeds 65535.
- Set ZF if the stored result is zero.

For CMP:

- Set ZF if the operands are equal.
- Set CF if the first unsigned operand is less than the second operand.

MOV, LOAD, STORE, JMP, JZ, JNZ, and HALT leave both flags unchanged.

When an arithmetic or comparison instruction finishes its Write Back stage, commit its pending flag changes.

Conditional jumps use the committed flags from earlier instructions.

Document these semantics in the README. Do not implement signed arithmetic or signed comparison.

## 7. MODEL THE FIVE INSTRUCTION-CYCLE STAGES

Every instruction must be processed sequentially through these five educational stages:

1. Fetch
2. Decode
3. Execute
4. Memory Access
5. Write Back

This is a non-pipelined teaching model. Only one instruction is processed at a time. Do not imply that five instructions execute simultaneously in a real processor pipeline.

The GUI must make these stages visible and explain what happens during each one.

### Stage 1: Fetch

- Fetch the instruction at PC from instruction memory.
- Update IR.
- Increment PC.
- Highlight the Program Counter, instruction memory, and Instruction Register.
- Highlight the corresponding data path from PC through instruction memory to IR.
- Update the instruction listing to identify the currently executing instruction.
- Append a meaningful event to the execution log.

If PC is outside the valid instruction range when a fetch is attempted, mark the program as completed normally rather than crashing.

### Stage 2: Decode

- Decode the current instruction and its operands.
- Read the required source register values into temporary operand latches.
- Resolve any operands needed for the current instruction.
- Highlight the Control Unit and Instruction Register.
- Display an explanation of what the instruction means.

For an immediate operand, explain that the value comes directly from the instruction.

For a label-based branch, show its resolved target instruction index.

### Stage 3: Execute

- For MOV, prepare the value to be transferred to the destination register.
- For ADD, SUB, and MUL, perform the appropriate ALU operation and prepare the result and pending flags.
- For CMP, perform the comparison and prepare the pending flags.
- For JMP, JZ, and JNZ, evaluate the branch and update PC when appropriate.
- For LOAD and STORE, prepare the memory address and source/destination information.
- For HALT, record the pending halt state.

Highlight the ALU when it performs arithmetic or comparison.

Highlight the Control Unit when it handles control-flow instructions.

Show the current operands, operation, and result when applicable.

### Stage 4: Memory Access

- LOAD reads the requested data memory cell and stores the retrieved value in a temporary result latch.
- STORE writes the source register value into the specified data memory cell.
- Instructions that do not access data memory complete this stage without modifying memory.

Highlight data memory and the corresponding data path when a memory operation occurs.

The diagram must visibly distinguish data-memory activity from instruction-memory fetching.

### Stage 5: Write Back

- MOV writes its pending value to the destination register.
- ADD, SUB, and MUL write their pending result and flags.
- LOAD writes the value retrieved during Memory Access to the destination register.
- CMP commits its pending flags without modifying general-purpose registers.
- Instructions that do not write a register or flags do not modify them.
- A pending HALT takes effect at the end of this stage.

Highlight the destination register and the active data path when a register is updated.

After Write Back, prepare the CPU for the Fetch stage of the next instruction.

Do not implement overlapping instruction execution or a speculative pipeline.

### Stage transition behavior

The CPU core must implement a method that advances exactly one stage at a time, along with a method that finishes the current instruction by advancing through the remaining stages.

The GUI's **Step Stage** button must advance exactly one of the five stages.

The GUI's **Step Instruction** button must advance to the completion of the current instruction. If part of the instruction has already executed, it must finish that instruction rather than start a different one.

Do not duplicate execution effects when advancing through stages.

A STORE must write exactly once. A LOAD must read its value during Memory Access and commit the result during Write Back. Arithmetic register writes must occur during Write Back.

A HALT must finish its current cycle and then stop the program.

## 8. BUILD A VISUAL CPU ARCHITECTURE DIAGRAM

Use Tkinter Canvas to render the CPU architecture.

The main visualization must contain clearly labelled components:

- Program Counter (PC).
- Instruction Memory.
- Instruction Register (IR).
- Control Unit.
- General-Purpose Registers (R0–R7).
- Arithmetic Logic Unit (ALU).
- Flags (ZF and CF).
- Data Memory.
- Data paths and directional arrows.

Draw the components as separate boxes with readable labels.

Draw directional arrows connecting the components according to the simulated architecture. Add short labels to important paths where useful.

At minimum, distinguish:

- Instruction fetching: PC → Instruction Memory → IR.
- Operand transfer: Registers → ALU.
- Arithmetic result transfer: ALU → destination register during Write Back.
- LOAD data transfer: Data Memory → destination register.
- STORE data transfer: source register → Data Memory.
- Control-flow transfer: Control Unit/branch decision → PC.

These paths must correspond to the simplified CPU model and the instruction currently being executed.

### Dynamic highlighting

The diagram must react to execution state.

Use visual highlights to identify the active components and paths in each stage.

For example:

- Fetch: highlight PC, instruction memory, IR, and the instruction-fetch path.
- Decode: highlight IR and the Control Unit.
- Execute: highlight ALU for arithmetic, or the Control Unit and PC path for branches.
- Memory Access: highlight data memory and the relevant data path for LOAD or STORE.
- Write Back: highlight the destination register and its incoming result path.

Components that are not active should return to their normal appearance.

Do not use colors as the only indication of activity. Keep component labels readable and show the current stage in text.

Use a coherent, attractive, dark-themed color palette with high contrast. Avoid excessive gradients, clutter, distracting effects, and tiny text.

The Canvas must resize sensibly with the window. Use a redraw function that takes the current Canvas dimensions into account. Do not place controls on top of the diagram or allow labels to overlap.

Ensure the diagram remains usable at common desktop window sizes.

## 9. CREATE A COMPLETE DESKTOP INTERFACE

Build a polished Tkinter application, not a terminal-only simulator.

Set the window title to:

`CPU Architecture & Instruction Execution Visualizer`

Use a reasonable initial window size, such as approximately 1400 × 850 pixels, with a minimum size that keeps the important controls accessible.

Use Tkinter grid weights, PanedWindow, frames, or another suitable layout technique so resizing works sensibly.

### 9.1 Header

Show the project title and a concise status indicator, such as:

- Ready
- Program Loaded
- Running
- Paused
- Halted
- Completed
- Error

The status must reflect the real simulator state.

### 9.2 Assembly editor

Provide a multiline text editor where the user can write or modify assembly instructions.

Include a sample-program selector and a Load Example button.

Include an Assemble button that validates the code and loads the assembled instruction list.

Show assembly errors clearly, including line numbers, without terminating the application.

Highlight the source line corresponding to the current instruction when execution is in progress.

Do not edit the program text automatically during execution.

### 9.3 Execution controls

Provide these working controls:

- Assemble
- Run
- Pause
- Step Stage
- Step Instruction
- Reset

The buttons must perform their stated actions.

Run must advance one stage at a time using a configurable animation delay. Use Tkinter's `after()` mechanism. Never use `time.sleep()` or another blocking wait in the GUI thread.

Pause must stop scheduled execution and retain the current state.

Step Stage and Step Instruction must work when the program is paused.

Reset must stop scheduled callbacks and restore the CPU state to its initial state for the currently assembled program: PC zero, registers zero, flags clear, memory zero, and execution state reset.

Assembling a new program must validate it and begin execution from a clean CPU state.

Do not allow multiple simultaneous animation loops. Track and cancel scheduled callback identifiers safely.

A completed or halted program must not continue executing. The user should be able to reset it and run it again.

Show a configurable execution-speed control with a reasonable range. The speed must actually affect the delay between execution stages.

### 9.4 Registers panel

Show all eight registers in a table or grid.

For every register, show:

- Register name.
- Current decimal value.
- Four-digit hexadecimal value.

Update the display immediately when the simulator state changes.

Visually distinguish the register updated by the latest stage. Remove stale highlights when a different component or register becomes active.

### 9.5 CPU-state panel

Display:

- PC.
- IR.
- Current instruction index.
- Current instruction text.
- Current execution stage.
- ZF.
- CF.
- CPU status.

Clearly distinguish the current instruction from the next instruction to be fetched.

### 9.6 Data-memory viewer

Provide a memory table that shows addresses and their values.

Show the first 16 addresses by default, plus any additional addresses that have been read or modified during execution.

Avoid displaying all 256 rows at once if doing so makes the interface difficult to use.

Provide an address inspector that lets the user enter an address from 0 through 255 and inspect its current value.

Show memory values in decimal and hexadecimal.

Update the memory viewer immediately when a STORE instruction modifies memory.

Visually distinguish modified cells where practical, but do not permanently show stale highlights after Reset.

Validate memory-inspector input and display a readable error for invalid addresses.

### 9.7 Instruction-cycle stage indicator

Show five visible stage labels:

FETCH → DECODE → EXECUTE → MEMORY ACCESS → WRITE BACK

Highlight the stage that was just executed.

Display a short explanation of the current stage and the action taken.

For example:

`EXECUTE: The ALU added the values in R1 and R2. The result is pending and will be written to R3 during Write Back.`

Ensure that explanations match the actual instruction and execution state. Do not show hardcoded explanations that contradict what the CPU did.

### 9.8 Execution log

Provide a scrollable log containing chronological events.

Examples:

- Fetched `MOV R1, 10` from instruction index 0.
- Decoded immediate value 10 and destination register R1.
- Prepared result 10 for R1.
- Wrote 10 to R1 during Write Back.
- Loaded value 30 from data memory address 100.
- Branch taken to instruction index 2.
- Program halted.

Log actual events and values from the CPU state.

Clear or reset the log when Reset is used, and add a fresh message indicating that the CPU has been reset.

The log must not invent actions or claim that a register was updated before the Write Back stage actually occurs.

## 10. PROVIDE WORKING SAMPLE PROGRAMS

Supply at least three sample programs accessible through the sample selector.

### Example A: Arithmetic and memory storage

```asm
; Calculate 10 + 20 and store the answer at memory address 100
MOV R1, 10
MOV R2, 20
ADD R3, R1, R2
STORE R3, [100]
HALT
```

Expected final state:

- R1 = 10
- R2 = 20
- R3 = 30
- Data memory[100] = 30
- CPU status = Halted

### Example B: Loop and conditional branch

```asm
; Calculate 5 + 4 + 3 + 2 + 1
MOV R1, 5
MOV R2, 0
MOV R3, 1
LOOP:
ADD R2, R2, R1
SUB R1, R1, R3
CMP R1, R0
JNZ LOOP
STORE R2, [100]
HALT
```

Expected final state:

- R1 = 0
- R2 = 15
- R3 = 1
- Data memory[100] = 15
- ZF = true after the final CMP
- CPU status = Halted

Explain that the branch depends on the Zero Flag produced by CMP.

### Example C: Load and reuse memory

```asm
; Store 42, load it back, then add 8
MOV R1, 42
STORE R1, [10]
LOAD R2, [10]
MOV R3, 8
ADD R4, R2, R3
HALT
```

Expected final state:

- R1 = 42
- Data memory[10] = 42
- R2 = 42
- R3 = 8
- R4 = 50
- CPU status = Halted

Check these expected results against the actual simulator, not by simply showing them as predetermined output.

## 11. CPU ENGINE DESIGN REQUIREMENTS

Keep the CPU execution engine independent of Tkinter.

Implement sensible classes and methods, for example:

- `Instruction`
- `AssemblyProgram`
- `Assembler`
- `CPU`
- `AssemblyError`
- `ExecutionError`

You may use slightly different names if the separation of responsibilities remains clear.

The CPU should expose its current state through ordinary Python attributes or well-defined read-only properties.

Provide appropriate methods such as:

- Loading a validated program.
- Resetting the processor.
- Advancing one execution stage.
- Completing the current instruction.
- Reading the current execution state.
- Determining whether execution has halted, completed, or encountered an error.

Do not place GUI-specific logic inside the CPU engine.

Use temporary latches to preserve values between the Decode, Execute, Memory Access, and Write Back stages.

For example, the value read by LOAD during Memory Access must be preserved until Write Back.

Decode must capture the source operand values required by the current instruction so later stages use the decoded operands consistently.

Maintain the instruction being executed separately from PC, because branches modify PC.

The GUI must observe the real CPU state rather than maintaining an independent, contradictory copy of register or memory values.

Use an explicit state machine instead of implementing the stages as five unrelated animations.

## 12. ERROR HANDLING AND RELIABILITY

The application must not crash because a user enters invalid assembly or an invalid memory-inspector value.

Handle these situations with helpful messages:

- Unknown opcode.
- Incorrect operand count.
- Invalid register name.
- Invalid or out-of-range integer.
- Invalid memory address.
- Incorrect bracket syntax for memory operands.
- Invalid label syntax.
- Duplicate label.
- Undefined branch target.
- Empty program.
- Invalid or incomplete instruction.
- Attempts to step after the program has halted or completed.
- Attempting to run an unassembled or invalid program.
- Unexpected runtime errors.

Do not silently ignore invalid source lines.

For assembly errors, show the offending source line number and a concise explanation.

For ordinary usage errors, use an inline error/status area or an appropriate dialog. Do not show a raw Python traceback to the user for normal validation failures.

If an unexpected internal exception occurs during scheduled execution, stop the animation safely, update the error status, and display useful diagnostic information without leaving duplicate scheduled callbacks active.

Avoid broad exception handling that conceals programming errors.

Check empty programs and program completion explicitly.

## 13. AUTOMATED TESTS ARE REQUIRED

Create automated tests using `unittest` in `tests/test_cpu.py`.

Tests must not require launching the GUI or interacting with a mouse.

At minimum, test the following:

1. The assembler parses valid MOV instructions.
2. Register names are case-insensitive.
3. Comments and blank lines are handled.
4. Labels resolve to the correct instruction indexes.
5. Duplicate and undefined labels produce errors.
6. Invalid opcodes and incorrect operand counts produce errors.
7. Invalid registers produce errors.
8. Out-of-range immediates and memory addresses are rejected.
9. MOV copies immediate values and register values correctly.
10. ADD produces the correct result.
11. ADD overflow wraps to 16 bits and sets CF correctly.
12. SUB produces the correct result.
13. SUB borrow and zero conditions set the flags correctly.
14. MUL produces the correct result and flags.
15. CMP sets ZF and CF according to the defined rules.
16. LOAD retrieves a value from data memory.
17. STORE modifies the correct data memory cell.
18. JMP transfers execution to the correct target.
19. JZ branches when ZF is true.
20. JNZ branches when ZF is false.
21. A non-taken conditional branch falls through correctly.
22. HALT stops execution.
23. A program that reaches the end of instruction memory without HALT completes normally.
24. Reset restores registers, PC, flags, memory, and execution state.
25. Step Stage advances exactly one stage.
26. Step Instruction completes the current instruction without duplicating side effects.
27. STORE writes only once during the Memory Access stage.
28. LOAD retrieves its value during Memory Access and writes its register during Write Back.
29. Branch decisions use the correct previously committed flags.
30. All three sample programs reach their expected final states.

Tests should be isolated and repeatable. Each test must construct its own program and CPU instance. Do not let one test depend on execution performed by another test.

Use clear test names and meaningful assertions.

Fix all failing tests before declaring the project complete.

## 14. README DOCUMENTATION

Write a complete but concise README.md containing:

1. Project title and description.
2. Problem statement and project objectives.
3. Features.
4. Technologies used.
5. A clear explanation of the simplified CPU architecture.
6. A description of PC, IR, registers, Control Unit, ALU, flags, instruction memory, and data memory.
7. A diagram or readable text diagram of the instruction/data paths.
8. The five instruction-cycle stages and what happens in each.
9. The complete supported instruction set and syntax.
10. Register, memory, arithmetic, and flag semantics.
11. System requirements.
12. Installation and run instructions.
13. Instructions for launching the GUI.
14. Instructions for using the editor, assembler, controls, and sample programs.
15. Instructions for running automated tests.
16. Expected results for all three examples.
17. Project file structure.
18. Limitations and possible future extensions.

Include commands for launching the application:

`python main.py`

Include the automated test command:

`python -m unittest discover -s tests -v`

Explain that Tkinter is normally included with many Python distributions but may need to be installed separately on some Linux systems.

Clearly state that the CPU is an educational simulation, uses separate instruction and data memories, is non-pipelined, and does not emulate a real commercial processor's instruction set or timing.

Do not claim that the model implements features it does not support.

## 15. IMPLEMENTATION AND VISUAL QUALITY

The finished project must look like a deliberate educational application rather than a collection of unstyled widgets.

Prioritize:

- A clean, dark interface.
- Strong contrast and readable text.
- A clearly visible architecture diagram.
- Consistent spacing and alignment.
- Easy-to-understand controls.
- Immediate feedback when a stage executes.
- Useful visual highlights.
- Readable decimal and hexadecimal values.
- A well-organized log.
- A visible status indicator.
- A layout that remains usable when resized.

Use Tkinter and ttk styles consistently. Use Canvas for the diagram, not for every interface element.

Do not create complex 3D effects, elaborate graphics, external image dependencies, or features that substantially increase implementation time without improving the learning objective.

Make reasonable choices that prioritize reliability and completion.

## 16. FINAL ACCEPTANCE CRITERIA

The project is complete only when all of these conditions are satisfied:

- All required source files exist in the workspace.
- The application launches with `python main.py`.
- The GUI displays the CPU architecture and all required components.
- The user can edit and assemble an assembly program.
- Invalid assembly produces helpful errors instead of a crash.
- The five instruction-cycle stages are visible and operational.
- Step Stage advances exactly one stage.
- Step Instruction finishes exactly one instruction, unless execution terminates earlier.
- Run executes the program automatically without freezing the GUI.
- Pause stops automatic execution without resetting the CPU.
- Reset reliably restores a clean initial state.
- Registers, PC, IR, flags, and data memory display actual simulator values.
- Architecture highlights reflect the real instruction and current stage.
- The execution log describes the actual operations performed.
- All three sample programs work and produce their specified results.
- Automated tests run without requiring a GUI.
- All automated tests pass.
- The README contains accurate setup, usage, architecture, and testing instructions.
- No required feature is represented by a nonfunctional placeholder.

## 17. REQUIRED WORKFLOW

Follow this workflow:

**Step 1 — Inspect.** Inspect the existing workspace before creating files. Preserve unrelated user files and integrate with existing project content where appropriate.

**Step 2 — Implement the core.** Build the assembler and CPU engine first, with the defined instruction semantics and stage state machine.

**Step 3 — Test the core.** Create the required unit tests. Run them and fix any failures.

**Step 4 — Build the GUI.** Implement the editor, controls, architecture diagram, active-path visualization, register panel, flags, memory viewer, stage indicator, and log.

**Step 5 — Integrate.** Ensure the GUI uses the real CPU engine and assembler, not duplicate or simulated GUI-only execution state.

**Step 6 — Verify.** Run the test suite and perform available application checks. Verify the sample programs against their expected outcomes and check that Run, Pause, Reset, Step Stage, and Step Instruction work consistently.

**Step 7 — Review.** Look for syntax errors, incorrect state transitions, inconsistent flags, stale highlights, incorrect PC behavior, duplicate scheduled callbacks, memory corruption, and discrepancies between the diagram and actual CPU behavior.

**Step 8 — Document.** Complete README.md with accurate commands, supported instructions, and limitations.

**Step 9 — Report.** Provide a concise summary of the files created, implemented features, test command, test results, launch command, and any issue that could not be resolved.

Do not say a test passed unless you actually ran it and observed the result. Do not claim the GUI was tested if the environment did not permit launching it.

If a dependency or environment issue prevents a particular check, explain the exact limitation and perform the remaining checks.

Do not stop after writing a plan. Carry out the implementation in the current workspace. Do not leave TODOs, pseudocode, placeholder handlers, or unimplemented required controls.

## FINAL INSTRUCTION

Produce the smallest complete, reliable, working application that satisfies this specification.

Prioritize correct CPU behavior first, then correct stage-by-stage visualization, then GUI polish.

Keep all CPU state transitions deterministic and testable. Make every displayed value and animation correspond to the real simulated execution.

The final result must be suitable for demonstrating to a college instructor how a simplified CPU fetches, decodes, executes, accesses memory, and writes back instructions.

Begin by inspecting the workspace, then implement the project. Do not respond with only a proposed design or a list of instructions.