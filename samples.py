"""Assembly source examples shared by the GUI and non-GUI tests."""

SAMPLES = {
    "Arithmetic and memory": (
        "; Calculate 10 + 20 and store the answer at memory address 100\n"
        "MOV R1, 10\nMOV R2, 20\nADD R3, R1, R2\nSTORE R3, [100]\nHALT"
    ),
    "Loop and conditional branch": (
        "; Calculate 5 + 4 + 3 + 2 + 1\n"
        "MOV R1, 5\nMOV R2, 0\nMOV R3, 1\nLOOP:\n"
        "ADD R2, R2, R1\nSUB R1, R1, R3\nCMP R1, R0\n"
        "JNZ LOOP\nSTORE R2, [100]\nHALT"
    ),
    "Load and reuse memory": (
        "; Store 42, load it back, then add 8\n"
        "MOV R1, 42\nSTORE R1, [10]\nLOAD R2, [10]\n"
        "MOV R3, 8\nADD R4, R2, R3\nHALT"
    ),
}
