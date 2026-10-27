import unittest

from assembler import Assembler, AssemblyError
from cpu import CPU, ExecutionError
from samples import SAMPLES


def assemble(source):
    return Assembler().assemble(source)


def run_to_stop(cpu, limit=1000):
    for _ in range(limit):
        if cpu.stopped:
            return
        cpu.advance_stage()
    raise AssertionError("CPU did not stop within the stage limit.")


class AssemblerTests(unittest.TestCase):
    def test_parses_mov_immediate_and_register_operands(self):
        program = assemble("MOV R1, 10\nMOV R2, R1\nMOV R3, 0X2A")
        self.assertEqual([item.opcode for item in program.instructions], ["MOV"] * 3)
        self.assertEqual(program.instructions[0].operands, ("R1", ("immediate", 10)))
        self.assertEqual(program.instructions[1].operands, ("R2", ("register", "R1")))
        self.assertEqual(program.instructions[2].operands[1], ("immediate", 42))

    def test_register_names_are_case_insensitive(self):
        program = assemble("mov r1, 4\nadd R2, r1, R1")
        self.assertEqual(program.instructions[0].operands[0], "R1")
        self.assertEqual(program.instructions[1].operands, ("R2", "R1", "R1"))

    def test_comments_blank_lines_and_source_information(self):
        program = assemble("\n; comment\n MOV r1, 7 ; trailing\n\nHALT\n")
        self.assertEqual(len(program.instructions), 2)
        self.assertEqual(program.instructions[0].source_line, 3)
        self.assertEqual(program.instructions[0].text, "MOV r1, 7")

    def test_labels_resolve_case_insensitively_to_instruction_indexes(self):
        program = assemble("JMP loop\nMOV R0, 9\nLOOP:\nHALT\n")
        self.assertEqual(program.labels["LOOP"], 2)
        self.assertEqual(program.instructions[0].operands[0], 2)

    def test_duplicate_and_undefined_labels_have_line_numbers(self):
        with self.assertRaisesRegex(AssemblyError, "Line 3: Duplicate label"):
            assemble("loop:\nHALT\nLOOP:\n")
        with self.assertRaisesRegex(AssemblyError, "Line 1: Undefined label"):
            assemble("JMP nowhere\n")

    def test_invalid_opcode_and_operand_counts_are_rejected(self):
        with self.assertRaisesRegex(AssemblyError, "Line 1: Unknown opcode"):
            assemble("NOPE R1\n")
        with self.assertRaisesRegex(AssemblyError, "expects 3 operand"):
            assemble("ADD R1, R2\n")
        with self.assertRaisesRegex(AssemblyError, "expects 0 operand"):
            assemble("HALT R0\n")

    def test_invalid_register_is_rejected(self):
        with self.assertRaisesRegex(AssemblyError, "Invalid register"):
            assemble("MOV R8, 1\n")
        with self.assertRaisesRegex(AssemblyError, "Invalid register"):
            assemble("ADD R1, R2, R9\n")

    def test_immediate_and_memory_address_ranges_are_validated(self):
        for source in ("MOV R1, 65536", "MOV R1, -1", "MOV R1, 0x10000"):
            with self.subTest(source=source), self.assertRaises(AssemblyError):
                assemble(source)
        for source in ("LOAD R1, [256]", "STORE R1, [-1]"):
            with self.subTest(source=source), self.assertRaises(AssemblyError):
                assemble(source)

    def test_memory_operand_and_label_syntax_are_strict(self):
        for source in ("LOAD R1, 10", "STORE R1, [1, 2]", "JMP bad-label", "LOOP: HALT"):
            with self.subTest(source=source), self.assertRaises(AssemblyError):
                assemble(source)

    def test_empty_program_is_rejected(self):
        with self.assertRaisesRegex(AssemblyError, "Program is empty"):
            assemble(" ; only a comment\n\n")


class CPUExecutionTests(unittest.TestCase):
    def cpu_for(self, source):
        return CPU(assemble(source))

    def test_mov_copies_immediate_and_register_values(self):
        cpu = self.cpu_for("MOV R0, 19\nMOV R7, R0\nHALT")
        cpu.finish_instruction()
        self.assertEqual(cpu.registers["R0"], 19)
        cpu.finish_instruction()
        self.assertEqual(cpu.registers["R7"], 19)

    def test_add_result_and_overflow_flags(self):
        cpu = self.cpu_for("MOV R1, 12\nMOV R2, 30\nADD R3, R1, R2\nHALT")
        while cpu.current_instruction_index != 2 or cpu.current_stage != "FETCH":
            cpu.advance_stage()
        for _ in range(4):
            cpu.advance_stage()
        self.assertEqual(cpu.registers["R3"], 42)
        self.assertFalse(cpu.zf)
        self.assertFalse(cpu.cf)
        cpu = self.cpu_for("MOV R1, 65535\nMOV R2, 1\nADD R3, R1, R2\nHALT")
        while cpu.registers["R2"] != 1:
            cpu.finish_instruction()
        cpu.finish_instruction()
        self.assertEqual(cpu.registers["R3"], 0)
        self.assertTrue(cpu.zf)
        self.assertTrue(cpu.cf)

    def test_sub_result_borrow_and_zero_flags(self):
        cpu = self.cpu_for("MOV R1, 3\nMOV R2, 5\nSUB R3, R1, R2\nHALT")
        while cpu.registers["R2"] != 5:
            cpu.finish_instruction()
        cpu.finish_instruction()
        self.assertEqual(cpu.registers["R3"], 65534)
        self.assertFalse(cpu.zf)
        self.assertTrue(cpu.cf)
        cpu = self.cpu_for("MOV R1, 8\nSUB R2, R1, R1\nHALT")
        cpu.finish_instruction()
        cpu.finish_instruction()
        self.assertEqual(cpu.registers["R2"], 0)
        self.assertTrue(cpu.zf)
        self.assertFalse(cpu.cf)

    def test_mul_result_and_flags(self):
        cpu = self.cpu_for("MOV R1, 300\nMOV R2, 300\nMUL R3, R1, R2\nHALT")
        cpu.finish_instruction()
        cpu.finish_instruction()
        cpu.finish_instruction()
        self.assertEqual(cpu.registers["R3"], (300 * 300) & 0xFFFF)
        self.assertTrue(cpu.cf)
        self.assertFalse(cpu.zf)

    def test_cmp_sets_equal_and_unsigned_borrow_flags(self):
        cpu = self.cpu_for("MOV R1, 9\nMOV R2, 9\nCMP R1, R2\nHALT")
        cpu.finish_instruction()
        cpu.finish_instruction()
        cpu.finish_instruction()
        self.assertTrue(cpu.zf)
        self.assertFalse(cpu.cf)
        cpu = self.cpu_for("MOV R1, 4\nMOV R2, 7\nCMP R1, R2\nHALT")
        cpu.finish_instruction()
        cpu.finish_instruction()
        cpu.finish_instruction()
        self.assertFalse(cpu.zf)
        self.assertTrue(cpu.cf)

    def test_load_and_store_use_data_memory(self):
        cpu = self.cpu_for("MOV R1, 42\nSTORE R1, [10]\nLOAD R2, [10]\nHALT")
        cpu.finish_instruction()
        cpu.finish_instruction()
        cpu.finish_instruction()
        self.assertEqual(cpu.data_memory[10], 42)
        self.assertEqual(cpu.registers["R2"], 42)

    def test_jump_transfers_to_resolved_instruction(self):
        cpu = self.cpu_for("JMP TARGET\nMOV R0, 99\nTARGET:\nMOV R1, 7\nHALT")
        cpu.finish_instruction()
        self.assertEqual(cpu.pc, 2)
        cpu.finish_instruction()
        self.assertEqual(cpu.registers["R1"], 7)
        self.assertEqual(cpu.registers["R0"], 0)

    def test_jz_and_jnz_use_committed_zero_flag(self):
        cpu = self.cpu_for("MOV R1, 0\nCMP R1, R0\nJZ YES\nMOV R2, 8\nYES:\nMOV R3, 6\nHALT")
        cpu.finish_instruction()
        cpu.finish_instruction()
        cpu.finish_instruction()
        self.assertTrue(cpu.zf)
        self.assertEqual(cpu.pc, 4)
        self.assertEqual(cpu.registers["R2"], 0)
        cpu.finish_instruction()
        self.assertEqual(cpu.registers["R3"], 6)
        cpu = self.cpu_for("MOV R1, 1\nCMP R1, R0\nJNZ YES\nMOV R2, 8\nYES:\nHALT")
        cpu.finish_instruction()
        cpu.finish_instruction()
        cpu.finish_instruction()
        cpu.finish_instruction()
        self.assertEqual(cpu.pc, 5)
        self.assertEqual(cpu.registers["R2"], 0)

    def test_conditional_branch_not_taken_falls_through(self):
        cpu = self.cpu_for("MOV R1, 1\nCMP R1, R0\nJZ TARGET\nMOV R2, 8\nTARGET:\nHALT")
        cpu.finish_instruction()
        cpu.finish_instruction()
        cpu.finish_instruction()
        self.assertEqual(cpu.pc, 3)
        cpu.finish_instruction()
        self.assertEqual(cpu.pc, 4)
        cpu.finish_instruction()
        self.assertEqual(cpu.registers["R2"], 8)

    def test_halt_stops_after_write_back(self):
        cpu = self.cpu_for("HALT\nMOV R1, 2")
        for _ in range(4):
            cpu.advance_stage()
        self.assertFalse(cpu.halted)
        cpu.advance_stage()
        self.assertTrue(cpu.halted)
        with self.assertRaises(ExecutionError):
            cpu.advance_stage()

    def test_program_end_completes_normally(self):
        cpu = self.cpu_for("MOV R1, 3")
        cpu.finish_instruction()
        self.assertEqual(cpu.status, "Running")
        event = cpu.advance_stage()
        self.assertIn("completed normally", event)
        self.assertTrue(cpu.completed)

    def test_reset_restores_all_state_and_memory(self):
        cpu = self.cpu_for("MOV R1, 24\nSTORE R1, [200]\nHALT")
        cpu.finish_instruction()
        cpu.finish_instruction()
        cpu.reset()
        self.assertEqual(cpu.pc, 0)
        self.assertEqual(set(cpu.registers.values()), {0})
        self.assertFalse(cpu.zf)
        self.assertFalse(cpu.cf)
        self.assertEqual(len(cpu.data_memory), 256)
        self.assertEqual(set(cpu.data_memory), {0})
        self.assertEqual(cpu.status, "Ready")
        self.assertFalse(cpu.memory_touched)

    def test_step_stage_advances_exactly_one_stage(self):
        cpu = self.cpu_for("MOV R1, 5")
        self.assertEqual(cpu.current_stage, "FETCH")
        cpu.advance_stage()
        self.assertEqual(cpu.current_stage, "DECODE")
        self.assertEqual(cpu.pc, 1)
        self.assertEqual(cpu.registers["R1"], 0)

    def test_step_instruction_finishes_partial_instruction_once(self):
        cpu = self.cpu_for("STORE R1, [4]\nHALT")
        cpu.registers["R1"] = 31
        cpu.advance_stage()
        cpu.advance_stage()
        events = cpu.finish_instruction()
        self.assertEqual(len(events), 3)
        self.assertEqual(cpu.data_memory[4], 31)
        self.assertEqual(cpu.current_stage, "FETCH")

    def test_store_is_not_repeated_during_write_back(self):
        cpu = self.cpu_for("MOV R1, 10\nSTORE R1, [4]")
        cpu.finish_instruction()
        cpu.advance_stage()
        cpu.advance_stage()
        cpu.advance_stage()
        cpu.advance_stage()
        self.assertEqual(cpu.data_memory[4], 10)
        cpu.data_memory[4] = 77
        cpu.advance_stage()
        self.assertEqual(cpu.data_memory[4], 77)

    def test_load_reads_during_memory_stage_and_commits_during_write_back(self):
        cpu = self.cpu_for("LOAD R2, [12]")
        cpu.data_memory[12] = 55
        cpu.advance_stage()
        cpu.advance_stage()
        cpu.advance_stage()
        cpu.advance_stage()
        self.assertEqual(cpu.latches.memory_value, 55)
        self.assertEqual(cpu.registers["R2"], 0)
        cpu.data_memory[12] = 99
        cpu.advance_stage()
        self.assertEqual(cpu.registers["R2"], 55)

    def test_arithmetic_and_cmp_flags_commit_only_at_write_back(self):
        cpu = self.cpu_for("MOV R1, 0\nMOV R2, 0\nCMP R1, R2")
        cpu.finish_instruction()
        cpu.finish_instruction()
        cpu.advance_stage()
        cpu.advance_stage()
        cpu.advance_stage()
        self.assertFalse(cpu.zf)
        cpu.advance_stage()
        self.assertTrue(cpu.latches.pending_flags[0])
        self.assertFalse(cpu.zf)
        cpu.advance_stage()
        self.assertTrue(cpu.zf)

    def test_branch_decision_uses_previously_committed_flags(self):
        cpu = self.cpu_for("MOV R1, 0\nCMP R1, R0\nJZ TARGET\nMOV R2, 9\nTARGET:\nHALT")
        cpu.finish_instruction()
        cpu.advance_stage()
        cpu.advance_stage()
        cpu.advance_stage()
        self.assertFalse(cpu.zf)
        cpu.advance_stage()
        self.assertFalse(cpu.zf)
        cpu.advance_stage()
        self.assertTrue(cpu.zf)
        cpu.finish_instruction()
        self.assertEqual(cpu.pc, 4)

    def test_all_three_sample_programs_match_expected_results(self):
        expected = [
            ({"R1": 10, "R2": 20, "R3": 30}, 100, 30),
            ({"R1": 0, "R2": 15, "R3": 1}, 100, 15),
            ({"R1": 42, "R2": 42, "R3": 8, "R4": 50}, 10, 42),
        ]
        for source, (registers, address, value) in zip(SAMPLES.values(), expected):
            with self.subTest(example=source.splitlines()[0]):
                cpu = CPU(assemble(source))
                run_to_stop(cpu)
                self.assertTrue(cpu.halted)
                for register, expected_value in registers.items():
                    self.assertEqual(cpu.registers[register], expected_value)
                self.assertEqual(cpu.data_memory[address], value)
        loop_cpu = CPU(assemble(SAMPLES["Loop and conditional branch"]))
        run_to_stop(loop_cpu)
        self.assertTrue(loop_cpu.zf)


if __name__ == "__main__":
    unittest.main()
