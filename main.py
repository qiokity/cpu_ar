"""Tkinter interface for the CPU architecture visualizer."""

from __future__ import annotations

import traceback
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional

from assembler import Assembler, AssemblyError
from cpu import CPU, ExecutionError, STAGES
from samples import SAMPLES

STAGE_EXPLANATIONS = {
    "FETCH": "Read instruction memory at PC, load IR, then increment PC.",
    "DECODE": "The Control Unit interprets the instruction and captures source operands.",
    "EXECUTE": "The ALU calculates or compares, or the Control Unit resolves a branch.",
    "MEMORY ACCESS": "LOAD reads or STORE writes data memory; other instructions leave it unchanged.",
    "WRITE BACK": "Commit a pending register result and/or arithmetic flags.",
}

COLORS = {
    "background": "#101722",
    "panel": "#182331",
    "panel_alt": "#202e3e",
    "border": "#34465a",
    "text": "#e6edf5",
    "muted": "#aab9c9",
    "accent": "#5ed4c5",
    "active": "#f6bd60",
    "register": "#8ab4f8",
    "memory": "#b39ddb",
    "danger": "#ff7b83",
    "green": "#86d993",
}


class CPUVisualizer:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("CPU Architecture & Instruction Execution Visualizer")
        self.root.geometry("1440x920")
        self.root.minsize(1100, 760)
        self.root.configure(bg=COLORS["background"])

        self.assembler = Assembler()
        self.cpu: Optional[CPU] = None
        self.after_id: Optional[str] = None
        self.running = False
        self.paused = False
        self.ui_error = False
        self.last_updated_register: Optional[str] = None
        self.selected_example = tk.StringVar(value=next(iter(SAMPLES)))
        self.speed_ms = tk.IntVar(value=650)
        self.status_var = tk.StringVar(value="Ready")
        self.instruction_var = tk.StringVar(value="No instruction loaded")
        self.stage_detail_var = tk.StringVar(value="Assemble a program to begin.")
        self.pc_var = tk.StringVar(value="0")
        self.ir_var = tk.StringVar(value="—")
        self.index_var = tk.StringVar(value="—")
        self.cpu_status_var = tk.StringVar(value="Not assembled")
        self.flags_var = tk.StringVar(value="ZF: 0    CF: 0")
        self.memory_address_var = tk.StringVar(value="0")
        self.memory_inspector_var = tk.StringVar(value="Address 0: 0 | 0x0000")
        self.memory_error_var = tk.StringVar(value="")
        self._build_styles()
        self._build_layout()
        self._update_views()
        self._update_status()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_styles(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", background=COLORS["panel"], foreground=COLORS["text"])
        style.configure("TFrame", background=COLORS["panel"])
        style.configure("Root.TFrame", background=COLORS["background"])
        style.configure("TLabel", background=COLORS["panel"], foreground=COLORS["text"])
        style.configure("Muted.TLabel", foreground=COLORS["muted"])
        style.configure(
            "Title.TLabel",
            background=COLORS["background"],
            foreground=COLORS["text"],
            font=("Segoe UI", 18, "bold"),
        )
        style.configure(
            "Section.TLabel",
            background=COLORS["panel"],
            foreground=COLORS["accent"],
            font=("Segoe UI", 11, "bold"),
        )
        style.configure("TButton", padding=(9, 6), background=COLORS["panel_alt"])
        style.map("TButton", background=[("active", "#33485d")])
        style.configure("Accent.TButton", background="#1f756e", foreground="white")
        style.map("Accent.TButton", background=[("active", "#2b9388")])
        style.configure("TNotebook", background=COLORS["background"], borderwidth=0)
        style.configure("TNotebook.Tab", background=COLORS["panel_alt"], padding=(10, 6))
        style.map(
            "TNotebook.Tab",
            background=[("selected", COLORS["panel"])],
            foreground=[("selected", COLORS["accent"])],
        )
        style.configure(
            "Treeview",
            background=COLORS["panel_alt"],
            fieldbackground=COLORS["panel_alt"],
            foreground=COLORS["text"],
            rowheight=25,
        )
        style.configure(
            "Treeview.Heading",
            background=COLORS["panel"],
            foreground=COLORS["accent"],
            font=("Segoe UI", 9, "bold"),
        )
        style.map("Treeview", background=[("selected", "#31536a")])

    def _build_layout(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        header = ttk.Frame(self.root, style="Root.TFrame", padding=(18, 12, 18, 8))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)
        ttk.Label(
            header, text="CPU Architecture & Instruction Execution Visualizer",
            style="Title.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="A non-pipelined, 16-bit educational CPU",
            style="Muted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))
        self.status_label = tk.Label(
            header, textvariable=self.status_var, bg=COLORS["panel_alt"],
            fg=COLORS["accent"], padx=12, pady=6, font=("Segoe UI", 10, "bold"),
        )
        self.status_label.grid(row=0, column=1, rowspan=2, sticky="e", padx=(10, 0))

        body = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        body.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
        left = ttk.Frame(body, padding=12)
        right = ttk.Frame(body, padding=(10, 10, 10, 6))
        body.add(left, weight=1)
        body.add(right, weight=2)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(2, weight=1)
        self._build_editor(left)
        self._build_controls(left)
        self._build_right_panel(right)

    def _build_editor(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="ASSEMBLY EDITOR", style="Section.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )
        sample_bar = ttk.Frame(parent)
        sample_bar.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        sample_bar.columnconfigure(0, weight=1)
        self.sample_box = ttk.Combobox(
            sample_bar, textvariable=self.selected_example,
            values=list(SAMPLES), state="readonly",
        )
        self.sample_box.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ttk.Button(sample_bar, text="Load Example", command=self._load_example).grid(
            row=0, column=1
        )

        editor_frame = ttk.Frame(parent)
        editor_frame.grid(row=2, column=0, sticky="nsew")
        editor_frame.columnconfigure(0, weight=1)
        editor_frame.rowconfigure(0, weight=1)
        self.editor = tk.Text(
            editor_frame, wrap="none", undo=True, font=("Consolas", 11),
            bg="#111a25", fg=COLORS["text"], insertbackground=COLORS["accent"],
            selectbackground="#31536a", relief="flat", padx=10, pady=8,
        )
        self.editor.grid(row=0, column=0, sticky="nsew")
        yscroll = ttk.Scrollbar(editor_frame, orient="vertical", command=self.editor.yview)
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll = ttk.Scrollbar(editor_frame, orient="horizontal", command=self.editor.xview)
        xscroll.grid(row=1, column=0, sticky="ew")
        self.editor.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.editor.tag_configure("current_instruction", background="#493d24", foreground="#fff3d0")
        self.editor.insert("1.0", SAMPLES["Arithmetic and memory"])
        self.editor.bind("<<Modified>>", self._editor_modified)
        self.editor.edit_modified(False)

        self.editor_error = tk.StringVar(value="Ready to assemble.")
        tk.Label(
            parent, textvariable=self.editor_error, bg=COLORS["panel"], fg=COLORS["muted"],
            anchor="w", justify="left", wraplength=400,
        ).grid(row=3, column=0, sticky="ew", pady=(6, 2))

    def _build_controls(self, parent: ttk.Frame) -> None:
        controls = ttk.LabelFrame(parent, text="Execution controls", padding=10)
        controls.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        for column in range(3):
            controls.columnconfigure(column, weight=1)
        ttk.Button(controls, text="Assemble", style="Accent.TButton", command=self._assemble).grid(
            row=0, column=0, sticky="ew", padx=3, pady=3
        )
        ttk.Button(controls, text="Run", command=self._run).grid(
            row=0, column=1, sticky="ew", padx=3, pady=3
        )
        ttk.Button(controls, text="Pause", command=self._pause).grid(
            row=0, column=2, sticky="ew", padx=3, pady=3
        )
        ttk.Button(controls, text="Step Stage", command=self._step_stage).grid(
            row=1, column=0, sticky="ew", padx=3, pady=3
        )
        ttk.Button(controls, text="Step Instruction", command=self._step_instruction).grid(
            row=1, column=1, sticky="ew", padx=3, pady=3
        )
        ttk.Button(controls, text="Reset", command=self._reset).grid(
            row=1, column=2, sticky="ew", padx=3, pady=3
        )
        ttk.Label(controls, text="Stage delay").grid(row=2, column=0, sticky="w", padx=4, pady=(8, 0))
        self.speed_label = ttk.Label(controls, text="650 ms")
        self.speed_label.grid(row=2, column=2, sticky="e", padx=4, pady=(8, 0))
        ttk.Scale(
            controls, from_=100, to=1500, variable=self.speed_ms,
            command=self._speed_changed,
        ).grid(row=2, column=1, sticky="ew", padx=4, pady=(8, 0))

    def _build_right_panel(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=3)
        parent.rowconfigure(3, weight=4)
        ttk.Label(parent, text="SIMPLIFIED HARVARD-STYLE CPU DATAPATH", style="Section.TLabel").grid(
            row=0, column=0, sticky="nw", pady=(0, 6)
        )
        self.diagram = tk.Canvas(
            parent, height=300, bg="#111a25", highlightthickness=1,
            highlightbackground=COLORS["border"],
        )
        self.diagram.grid(row=1, column=0, sticky="nsew")
        self.diagram.bind("<Configure>", lambda _event: self._draw_diagram())

        stage_frame = ttk.Frame(parent, padding=(0, 10, 0, 8))
        stage_frame.grid(row=2, column=0, sticky="ew")
        stage_frame.columnconfigure(tuple(range(5)), weight=1)
        self.stage_labels: list[tk.Label] = []
        for index, stage in enumerate(STAGES):
            label = tk.Label(
                stage_frame, text=stage, bg=COLORS["panel_alt"], fg=COLORS["muted"],
                padx=4, pady=7, font=("Segoe UI", 8, "bold"),
            )
            label.grid(row=0, column=index, sticky="ew", padx=2)
            self.stage_labels.append(label)
        self.instruction_caption = ttk.Label(
            parent, textvariable=self.instruction_var, style="Muted.TLabel"
        )
        self.instruction_caption.grid(row=3, column=0, sticky="nw", pady=(0, 5))

        self.tabs = ttk.Notebook(parent)
        self.tabs.grid(row=4, column=0, sticky="nsew")
        parent.rowconfigure(4, weight=4)
        state_tab = ttk.Frame(self.tabs, padding=12)
        register_tab = ttk.Frame(self.tabs, padding=12)
        memory_tab = ttk.Frame(self.tabs, padding=12)
        log_tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(state_tab, text="CPU State")
        self.tabs.add(register_tab, text="Registers")
        self.tabs.add(memory_tab, text="Data Memory")
        self.tabs.add(log_tab, text="Execution Log")
        self._build_state_tab(state_tab)
        self._build_register_tab(register_tab)
        self._build_memory_tab(memory_tab)
        self._build_log_tab(log_tab)
        self._draw_diagram()

    def _build_state_tab(self, parent: ttk.Frame) -> None:
        for column in (1, 3):
            parent.columnconfigure(column, weight=1)
        rows = [
            ("Program Counter (next instruction)", self.pc_var),
            ("Instruction Register", self.ir_var),
            ("Current instruction index", self.index_var),
            ("CPU status", self.cpu_status_var),
        ]
        for row, (title, variable) in enumerate(rows):
            ttk.Label(parent, text=title, style="Muted.TLabel").grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=5
            )
            ttk.Label(parent, textvariable=variable, font=("Consolas", 10)).grid(
                row=row, column=1, sticky="w", pady=5
            )
        ttk.Label(parent, text="Flags", style="Muted.TLabel").grid(
            row=4, column=0, sticky="w", padx=(0, 12), pady=5
        )
        ttk.Label(parent, textvariable=self.flags_var, font=("Consolas", 10)).grid(
            row=4, column=1, sticky="w", pady=5
        )
        ttk.Separator(parent).grid(row=5, column=0, columnspan=2, sticky="ew", pady=8)
        ttk.Label(parent, text="Stage explanation", style="Section.TLabel").grid(
            row=6, column=0, columnspan=2, sticky="w"
        )
        ttk.Label(
            parent, textvariable=self.stage_detail_var, wraplength=750, justify="left"
        ).grid(row=7, column=0, columnspan=2, sticky="nw", pady=(5, 0))

    def _build_register_tab(self, parent: ttk.Frame) -> None:
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        self.register_tree = ttk.Treeview(
            parent, columns=("register", "decimal", "hex"), show="headings", height=8
        )
        for column, title, width in (
            ("register", "Register", 100), ("decimal", "Decimal", 160), ("hex", "Hexadecimal", 160)
        ):
            self.register_tree.heading(column, text=title)
            self.register_tree.column(column, width=width, anchor="center")
        self.register_tree.tag_configure("updated", background="#35442f", foreground="#d9ffd1")
        self.register_tree.grid(row=0, column=0, sticky="nsew")
        for index in range(8):
            register = f"R{index}"
            self.register_tree.insert("", "end", iid=register, values=(register, "0", "0x0000"))

    def _build_memory_tab(self, parent: ttk.Frame) -> None:
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)
        inspector = ttk.Frame(parent)
        inspector.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(inspector, text="Inspect address (0-255):").grid(row=0, column=0, sticky="w")
        self.memory_entry = ttk.Entry(
            inspector, textvariable=self.memory_address_var, width=8
        )
        self.memory_entry.grid(row=0, column=1, padx=6)
        ttk.Button(inspector, text="Inspect", command=self._inspect_memory).grid(row=0, column=2)
        ttk.Label(inspector, textvariable=self.memory_inspector_var).grid(
            row=0, column=3, padx=12, sticky="w"
        )
        tk.Label(
            parent, textvariable=self.memory_error_var, bg=COLORS["panel"], fg=COLORS["danger"]
        ).grid(row=0, column=1, sticky="e")
        self.memory_tree = ttk.Treeview(
            parent, columns=("address", "decimal", "hex"), show="headings", height=8
        )
        for column, title, width in (
            ("address", "Address", 120), ("decimal", "Decimal value", 170),
            ("hex", "Hexadecimal value", 180),
        ):
            self.memory_tree.heading(column, text=title)
            self.memory_tree.column(column, width=width, anchor="center")
        self.memory_tree.tag_configure("modified", background="#39402c")
        self.memory_tree.grid(row=1, column=0, columnspan=2, sticky="nsew")

    def _build_log_tab(self, parent: ttk.Frame) -> None:
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        self.log_text = tk.Text(
            parent, state="disabled", wrap="word", font=("Consolas", 9),
            bg="#111a25", fg=COLORS["text"], relief="flat", padx=8, pady=7,
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(parent, orient="vertical", command=self.log_text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scroll.set)
        self._append_log("Ready. Assemble a program to begin.")

    def _editor_modified(self, _event: tk.Event) -> None:
        self.editor.edit_modified(False)
        if hasattr(self, "current_highlight"):
            self._clear_source_highlight()
        if self.cpu is not None:
            self.editor_error.set("Editor changed. Assemble to load the edited program.")

    def _load_example(self) -> None:
        self._pause()
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", SAMPLES[self.selected_example.get()])
        self.editor.edit_modified(False)
        self.editor_error.set(f"Loaded example: {self.selected_example.get()}.")

    def _assemble(self) -> None:
        self._pause()
        source = self.editor.get("1.0", "end-1c")
        try:
            program = self.assembler.assemble(source)
            self.cpu = CPU(program)
        except (AssemblyError, ExecutionError) as error:
            self.cpu = None
            self.last_updated_register = None
            self.ui_error = True
            self.editor_error.set(str(error))
            self.status_var.set("Error")
            self._update_views()
            return
        self.ui_error = False
        self.paused = False
        self.last_updated_register = None
        self.editor_error.set(f"Program loaded: {len(program.instructions)} instructions.")
        self._clear_source_highlight()
        self._clear_log()
        self._append_log(f"Assembled {len(program.instructions)} instruction(s).")
        self.stage_detail_var.set("Program loaded. PC points to instruction index 0.")
        self._update_views()

    def _run(self) -> None:
        if self.cpu is None:
            self.editor_error.set("Assemble a valid program before running.")
            return
        if self.cpu.stopped:
            self.editor_error.set("Execution has stopped. Reset the program before running again.")
            return
        if self.running:
            return
        self.running = True
        self.paused = False
        self._update_status()
        self._schedule_next(0)

    def _schedule_next(self, delay: int) -> None:
        if self.running and self.after_id is None:
            self.after_id = self.root.after(delay, self._run_one_stage)

    def _run_one_stage(self) -> None:
        self.after_id = None
        if not self.running or self.cpu is None:
            return
        try:
            self._advance_one_stage()
        except Exception as error:
            self._report_runtime_error(error)
            return
        if self.cpu.stopped:
            self.running = False
            self._update_status()
            return
        self._schedule_next(max(50, int(self.speed_ms.get())))

    def _pause(self) -> None:
        self.running = False
        self.paused = self.cpu is not None and not self.cpu.stopped
        self._cancel_callback()
        if hasattr(self, "status_var"):
            self._update_status()

    def _cancel_callback(self) -> None:
        if self.after_id is not None:
            try:
                self.root.after_cancel(self.after_id)
            except tk.TclError:
                pass
            self.after_id = None

    def _step_stage(self) -> None:
        self._pause()
        if not self._can_step():
            return
        try:
            self._advance_one_stage()
            self.paused = not self.cpu.stopped
            self._update_views()
        except ExecutionError as error:
            self.editor_error.set(str(error))
        except Exception as error:
            self._report_runtime_error(error)

    def _step_instruction(self) -> None:
        self._pause()
        if not self._can_step():
            return
        try:
            for event in self.cpu.finish_instruction():
                self._append_log(event)
            self._mark_written_register()
            self._after_advance()
            self.paused = not self.cpu.stopped
            self._update_views()
        except ExecutionError as error:
            self.editor_error.set(str(error))
        except Exception as error:
            self._report_runtime_error(error)

    def _report_runtime_error(self, error: Exception) -> None:
        traceback.print_exc()
        self._pause()
        if self.cpu is not None:
            self.cpu.status = "Error"
        self.editor_error.set(f"Execution error: {type(error).__name__}: {error}")
        self._append_log(f"Execution error: {type(error).__name__}: {error}")
        self._update_views()

    def _can_step(self) -> bool:
        if self.cpu is None:
            self.editor_error.set("Assemble a valid program before stepping.")
            return False
        if self.cpu.stopped:
            self.editor_error.set(f"Program has {self.cpu.status.lower()}; reset it to run again.")
            return False
        return True

    def _advance_one_stage(self) -> None:
        assert self.cpu is not None
        event = self.cpu.advance_stage()
        self._append_log(event)
        self._mark_written_register()
        self._after_advance()
        self._update_views()

    def _mark_written_register(self) -> None:
        if self.cpu is None or self.cpu.last_stage != "WRITE BACK":
            self.last_updated_register = None
            return
        instruction = self.cpu.current_instruction
        if instruction is None:
            self.last_updated_register = None
            return
        destination = None
        if instruction.opcode in {"MOV", "ADD", "SUB", "MUL", "LOAD"}:
            destination = instruction.operands[0]
        self.last_updated_register = destination

    def _after_advance(self) -> None:
        if self.cpu is None:
            return
        if self.cpu.last_stage == "FETCH" and self.cpu.current_instruction is not None:
            instruction = self.cpu.current_instruction
            self.instruction_var.set(
                f"Executing instruction {instruction.index} (source line {instruction.source_line}): "
                f"{instruction.text}   |   PC now points to {self.cpu.pc}"
            )
            self._highlight_source_line(instruction.source_line)
        elif self.cpu.completed:
            self.instruction_var.set("Instruction memory exhausted; program completed normally.")
            self._clear_source_highlight()
        if self.cpu.last_stage:
            self.stage_detail_var.set(self._stage_detail())

    def _stage_detail(self) -> str:
        assert self.cpu is not None
        stage = self.cpu.last_stage or "FETCH"
        instruction = self.cpu.current_instruction
        if instruction is None:
            return f"{stage}: {STAGE_EXPLANATIONS[stage]}"
        op = instruction.opcode
        if stage == "EXECUTE" and op in {"ADD", "SUB", "MUL"}:
            return f"EXECUTE: The ALU calculated the {op} result; the destination and flags remain pending until Write Back."
        if stage == "EXECUTE" and op == "CMP":
            return "EXECUTE: The ALU compared the captured unsigned operands; flags will be committed at Write Back."
        if stage == "EXECUTE" and op in {"JMP", "JZ", "JNZ"}:
            return "EXECUTE: The Control Unit evaluated the branch using the committed Zero Flag."
        if stage == "MEMORY ACCESS" and op == "LOAD":
            return "MEMORY ACCESS: Data memory supplied the value; it remains latched until Write Back."
        if stage == "MEMORY ACCESS" and op == "STORE":
            return "MEMORY ACCESS: The source value was written once to the selected data-memory address."
        if stage == "WRITE BACK" and op == "HALT":
            return "WRITE BACK: HALT took effect; no more instruction stages will execute."
        return f"{stage}: {STAGE_EXPLANATIONS[stage]} Instruction: {instruction.text}."

    def _reset(self) -> None:
        self._pause()
        if self.cpu is None:
            self.editor_error.set("Assemble a program before resetting the CPU.")
            return
        self.cpu.reset()
        self.last_updated_register = None
        self.instruction_var.set("No instruction is currently executing; next fetch is at index 0.")
        self.stage_detail_var.set("CPU reset. PC=0, registers and data memory cleared, flags cleared.")
        self.editor_error.set("CPU reset for the currently assembled program.")
        self._clear_source_highlight()
        self._clear_log()
        self._append_log("CPU reset: PC=0, registers=0, flags cleared, all 256 memory words cleared.")
        self._update_views()

    def _speed_changed(self, _value: str) -> None:
        self.speed_label.configure(text=f"{int(self.speed_ms.get())} ms")

    def _inspect_memory(self) -> None:
        raw = self.memory_address_var.get().strip()
        try:
            address = int(raw, 10)
            if not 0 <= address <= 255:
                raise ValueError
        except ValueError:
            self.memory_error_var.set("Enter a decimal address from 0 to 255.")
            return
        self.memory_error_var.set("")
        if self.cpu is None:
            self.memory_inspector_var.set(f"Address {address}: not assembled")
        else:
            self._show_memory_value(address)

    def _show_memory_value(self, address: int) -> None:
        assert self.cpu is not None
        value = self.cpu.data_memory[address]
        self.memory_inspector_var.set(f"Address {address}: {value} | 0x{value:04X}")

    def _update_views(self) -> None:
        self._update_status()
        cpu = self.cpu
        if cpu is None:
            self.pc_var.set("0")
            self.ir_var.set("—")
            self.index_var.set("—")
            self.cpu_status_var.set("Not assembled")
            self.flags_var.set("ZF: 0    CF: 0")
            for index in range(8):
                register = f"R{index}"
                self.register_tree.item(register, values=(register, "0", "0x0000"), tags=())
            self._refresh_memory()
            self._draw_diagram()
            return

        self.pc_var.set(str(cpu.pc))
        self.ir_var.set(cpu.ir or "—")
        self.index_var.set(
            str(cpu.current_instruction_index)
            if cpu.current_instruction_index is not None else "—"
        )
        self.cpu_status_var.set(self._display_cpu_status())
        self.flags_var.set(f"ZF: {int(cpu.zf)}    CF: {int(cpu.cf)}")
        for register, value in cpu.registers.items():
            tags = ("updated",) if register == self.last_updated_register else ()
            self.register_tree.item(
                register, values=(register, str(value), f"0x{value:04X}"), tags=tags
            )
        self._refresh_memory()
        active = cpu.last_stage
        for index, label in enumerate(self.stage_labels):
            label.configure(
                bg=COLORS["active"] if active == STAGES[index] else COLORS["panel_alt"],
                fg="#15202b" if active == STAGES[index] else COLORS["muted"],
            )
        self._draw_diagram()

    def _refresh_memory(self) -> None:
        if not hasattr(self, "memory_tree"):
            return
        for item in self.memory_tree.get_children():
            self.memory_tree.delete(item)
        addresses = set(range(16))
        if self.cpu is not None:
            addresses.update(self.cpu.memory_touched)
        for address in sorted(addresses):
            value = self.cpu.data_memory[address] if self.cpu is not None else 0
            tags = ("modified",) if self.cpu is not None and address in self.cpu.memory_touched else ()
            self.memory_tree.insert(
                "", "end", iid=str(address),
                values=(address, value, f"0x{value:04X}"), tags=tags,
            )
        if self.memory_address_var.get().isdecimal():
            address = int(self.memory_address_var.get())
            if 0 <= address <= 255:
                if self.cpu is not None:
                    self._show_memory_value(address)
                else:
                    self.memory_inspector_var.set(f"Address {address}: not assembled")

    def _display_cpu_status(self) -> str:
        if self.cpu is None:
            return "Error" if self.ui_error else "Not assembled"
        if self.running:
            return "Running"
        if self.paused and not self.cpu.stopped:
            return "Paused"
        return self.cpu.status

    def _update_status(self) -> None:
        if not hasattr(self, "status_var"):
            return
        value = self._display_cpu_status()
        self.status_var.set(value)
        color = COLORS["danger"] if value == "Error" else COLORS["accent"]
        self.status_label.configure(fg=color)

    def _append_log(self, message: str) -> None:
        if not hasattr(self, "log_text"):
            return
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"• {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _clear_log(self) -> None:
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

    def _highlight_source_line(self, line_number: int) -> None:
        self._clear_source_highlight()
        self.current_highlight = f"{line_number}.0"
        self.editor.tag_add("current_instruction", f"{line_number}.0", f"{line_number}.end")
        self.editor.see(f"{line_number}.0")

    def _clear_source_highlight(self) -> None:
        self.editor.tag_remove("current_instruction", "1.0", "end")
        self.current_highlight = None

    def _draw_diagram(self) -> None:
        if not hasattr(self, "diagram"):
            return
        canvas = self.diagram
        width = max(canvas.winfo_width(), 640)
        height = max(canvas.winfo_height(), 260)
        canvas.delete("all")
        boxes = {
            "pc": (0.035, 0.08, 0.19, 0.29, "Program Counter\nPC", "register"),
            "imem": (0.285, 0.08, 0.47, 0.29, "Instruction\nMemory", "memory"),
            "ir": (0.57, 0.08, 0.75, 0.29, "Instruction Register\nIR", "register"),
            "control": (0.78, 0.08, 0.97, 0.29, "Control Unit", "accent"),
            "regs": (0.035, 0.60, 0.23, 0.92, "Registers\nR0 – R7", "register"),
            "alu": (0.34, 0.64, 0.53, 0.88, "ALU", "active"),
            "flags": (0.58, 0.65, 0.74, 0.87, "Flags\nZF · CF", "accent"),
            "dmem": (0.79, 0.60, 0.97, 0.92, "Data Memory\n256 × 16-bit", "memory"),
        }
        rects = {
            key: (x1 * width, y1 * height, x2 * width, y2 * height)
            for key, (x1, y1, x2, y2, _label, _kind) in boxes.items()
        }
        active_components, active_paths = self._active_diagram_parts()
        paths = {
            "fetch_pc": (
                (rects["pc"][2], rects["pc"][1] + 13),
                (rects["imem"][0], rects["imem"][1] + 13), "PC index",
            ),
            "fetch_ir": (
                (rects["imem"][2], rects["imem"][1] + 13),
                (rects["ir"][0], rects["ir"][1] + 13), "instruction",
            ),
            "decode": (
                (rects["ir"][2], rects["ir"][1] + 26),
                (rects["control"][0], rects["control"][1] + 26), "decode",
            ),
            "operand": (
                (rects["regs"][2], (rects["regs"][1] + rects["regs"][3]) / 2),
                (rects["alu"][0], (rects["alu"][1] + rects["alu"][3]) / 2), "operands",
            ),
            "alu_result": (
                (rects["alu"][0], rects["alu"][1] + 8),
                (rects["regs"][2], rects["regs"][3] - 8), "write back",
            ),
            "load": (
                (rects["dmem"][0], rects["dmem"][1] + 18),
                (rects["regs"][2], rects["regs"][3] - 24), "LOAD data",
            ),
            "store": (
                (rects["regs"][2], rects["regs"][3] - 8),
                (rects["dmem"][0], rects["dmem"][1] + 38), "STORE data",
            ),
            "branch": (
                (rects["control"][0] + 18, rects["control"][3]),
                (rects["pc"][0] + 12, rects["pc"][3]), "branch target",
            ),
        }
        for key, (start, end, label) in paths.items():
            active = key in active_paths
            color = COLORS["active"] if active else "#536477"
            canvas.create_line(
                *start, *end, fill=color, width=3 if active else 1.5,
                arrow=tk.LAST, arrowshape=(8, 10, 4),
            )
            midpoint = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
            canvas.create_text(
                midpoint[0], midpoint[1] - 8, text=label,
                fill=COLORS["active"] if active else COLORS["muted"],
                font=("Segoe UI", 7, "bold"),
            )
        for key, (x1f, y1f, x2f, y2f, label, kind) in boxes.items():
            x1, y1, x2, y2 = rects[key]
            fill_color = COLORS["panel_alt"]
            if key in active_components:
                fill_color = "#493d24"
            elif kind == "memory":
                fill_color = "#27253b"
            elif kind == "register":
                fill_color = "#1e2d40"
            outline = COLORS["active"] if key in active_components else COLORS["border"]
            canvas.create_rectangle(
                x1, y1, x2, y2, fill=fill_color, outline=outline,
                width=2 if key in active_components else 1.2,
            )
            canvas.create_text(
                (x1 + x2) / 2, (y1 + y2) / 2, text=label,
                fill=COLORS["text"], font=("Segoe UI", 9, "bold"),
                width=max(60, x2 - x1 - 8), justify="center",
            )
        canvas.create_text(
            8, height - 8, anchor="sw",
            text="Instruction fetch and data-memory paths are separate.",
            fill=COLORS["muted"], font=("Segoe UI", 8),
        )

    def _active_diagram_parts(self) -> tuple[set[str], set[str]]:
        components: set[str] = set()
        paths: set[str] = set()
        if self.cpu is None or self.cpu.last_stage is None:
            return components, paths
        stage = self.cpu.last_stage
        instruction = self.cpu.current_instruction
        opcode = instruction.opcode if instruction else ""
        if stage == "FETCH":
            components.update({"pc", "imem", "ir"})
            paths.update({"fetch_pc", "fetch_ir"})
        elif stage == "DECODE":
            components.update({"ir", "control"})
            paths.add("decode")
        elif stage == "EXECUTE":
            if opcode in {"ADD", "SUB", "MUL", "CMP"}:
                components.update({"regs", "alu", "flags"})
                paths.update({"operand", "alu_result"})
            elif opcode in {"JMP", "JZ", "JNZ"}:
                components.update({"control", "pc"})
                paths.add("branch")
            elif opcode in {"LOAD", "STORE"}:
                components.update({"control", "dmem"})
            elif opcode == "MOV":
                components.update({"control", "regs"})
        elif stage == "MEMORY ACCESS" and opcode in {"LOAD", "STORE"}:
            components.update({"dmem", "regs"})
            paths.add("load" if opcode == "LOAD" else "store")
        elif stage == "WRITE BACK":
            if opcode in {"MOV", "ADD", "SUB", "MUL", "LOAD"}:
                components.add("regs")
                paths.add("load" if opcode == "LOAD" else "alu_result")
            if opcode in {"ADD", "SUB", "MUL", "CMP"}:
                components.add("flags")
            if opcode in {"JMP", "JZ", "JNZ"}:
                components.update({"control", "pc"})
                paths.add("branch")
        return components, paths

    def _on_close(self) -> None:
        self._pause()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    CPUVisualizer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
