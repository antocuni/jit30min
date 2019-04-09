import pytest
import jit
from jit import asm

def test_CompliedFunction():
    code = b'\xf2\x0f\x58\xc1\xc3' # addsd  xmm0,xmm1 ; ret
    p = jit.CompiledFunction(code)
    assert p.fptr(12.34, 56.78) == 12.34 + 56.78
    assert p(12.34, 56.78) == 12.34 + 56.78

class TestRegAllocator:

    def test_allocate(self):
        regs = jit.RegAllocator()
        assert regs.get('a') == asm.xmm0
        assert regs.get('b') == asm.xmm1
        assert regs.get('a') == asm.xmm0
        assert regs.get('c') == asm.xmm2

    def test_too_many_vars(self):
        regs = jit.RegAllocator()
        # force allocation of xmm0..xmm14
        for i in range(13):
            regs.get('var%d' % i)
        assert regs.get('var13') == asm.xmm13
        pytest.raises(NotImplementedError, "regs.get('var14')")



class TestFunctionAssembler:

    def equals(self, l1, l2):
        enc1 = [instr.encode() for instr in l1]
        enc2 = [instr.encode() for instr in l2]
        return enc1 == enc2

    def test_arguments(self):
        fn = jit.FunctionAssembler(['a', 'b'])
        assert fn.registers.get('a') == asm.xmm0
        assert fn.registers.get('b') == asm.xmm1
        assert fn.registers.get('c') == asm.xmm2
