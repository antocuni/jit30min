import jit
from jit import asm

def test_CompliedFunction():
    code = b'\xf2\x0f\x58\xc1\xc3' # addsd  xmm0,xmm1 ; ret
    p = jit.CompiledFunction(code)
    assert p.fptr(12.34, 56.78) == 12.34 + 56.78
    assert p(12.34, 56.78) == 12.34 + 56.78

class TestFunctionAssembler:

    def test_var_offset(self):
        fasm = jit.FunctionAssembler()
        assert fasm.var_offset('a') == -0x08
        assert fasm.var_offset('b') == -0x10
        assert fasm.var_offset('c') == -0x18
        assert fasm.var_offset('a') == -0x08

    def equals(self, l1, l2):
        enc1 = [instr.encode() for instr in l1]
        enc2 = [instr.encode() for instr in l2]
        return enc1 == enc2

    def test_load_var(self):
        fasm = jit.FunctionAssembler()
        fasm.load_var(asm.xmm0, 'a')
        assert self.equals(fasm.instructions, [
            asm.MOVSD(asm.xmm0, asm.qword[asm.rbp - 0x08])
        ])

    def test_store_var(self):
        fasm = jit.FunctionAssembler()
        fasm.store_var('a', asm.xmm0,)
        assert self.equals(fasm.instructions, [
            asm.MOVSD(asm.qword[asm.rbp - 0x08], asm.xmm0)
        ])
