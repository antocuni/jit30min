import pytest
import jit
from jit import asm

def test_CompliedFunction():
    code = b'\xf2\x0f\x58\xc1\xc3' # addsd  xmm0,xmm1 ; ret
    p = jit.CompiledFunction(2, code)
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

    def test_arguments(self):
        assembler = jit.FunctionAssembler('foo', ['a', 'b'])
        assert assembler.var('a') == asm.xmm0
        assert assembler.var('b') == asm.xmm1
        assert assembler.var('c') == asm.xmm2

    def test_compile(self):
        assembler = jit.FunctionAssembler('foo', ['a', 'b'])
        assembler.emit(asm.ADDSD(asm.xmm0, asm.xmm1))
        assembler.emit(asm.RET())
        fn = assembler.compile()
        assert fn(3, 4) == 7

    def test_nargs(self):
        assembler = jit.FunctionAssembler('foo', ['a', 'b', 'c'])
        assembler.emit(asm.ADDSD(asm.xmm0, asm.xmm1))
        assembler.emit(asm.ADDSD(asm.xmm0, asm.xmm2))
        assembler.emit(asm.RET())
        fn = assembler.compile()
        assert fn(3, 4, 5) == 12


class TestAstCompiler:

    def test_simple(self):
        comp = jit.AstCompiler("""
        def foo(a, b):
            return a+b
        """)
        fn = comp.compile()
        assert fn(3, 4) == 7
