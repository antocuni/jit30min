import pytest
import jit
from assembler import FunctionAssembler as FA
from test_assembler import TestFunctionAssembler as AssemblerTest

class TestCompiledFuntion(AssemblerTest):

    def test_basic(self):
        code = b'\xf2\x0f\x58\xc1\xc3' # addsd  xmm0,xmm1 ; ret
        p = jit.CompiledFunction(2, code)
        assert p.fptr(12.34, 56.78) == 12.34 + 56.78
        assert p(12.34, 56.78) == 12.34 + 56.78

    def load(self, asm):
        code = asm.assemble_and_relocate()
        return jit.CompiledFunction(asm.nargs, code)

class TestRegAllocator:

    def test_allocate(self):
        regs = jit.RegAllocator()
        assert regs.get('a') == FA.xmm0
        assert regs.get('b') == FA.xmm1
        assert regs.get('a') == FA.xmm0
        assert regs.get('c') == FA.xmm2

    def test_too_many_vars(self):
        regs = jit.RegAllocator()
        # force allocation of xmm0..xmm14
        for i in range(15):
            regs.get('var%d' % i)
        assert regs.get('var15') == FA.xmm15
        pytest.raises(NotImplementedError, "regs.get('var16')")


class TestAstCompiler:

    def test_empty(self):
        comp = jit.AstCompiler("""
        def foo():
            pass
        """)
        fn = comp.compile()
        assert fn() == 0

    def test_simple(self):
        comp = jit.AstCompiler("""
        def foo():
            return 100
        """)
        fn = comp.compile()
        assert fn() == 100

    def test_arguments(self):
        comp = jit.AstCompiler("""
        def foo(a, b):
            return b
        """)
        fn = comp.compile()
        assert fn(3, 4) == 4

    def test_add(self):
        comp = jit.AstCompiler("""
        def foo(a, b):
            return a+b
        """)
        fn = comp.compile()
        assert fn(3, 4) == 7

    def test_binops(self):
        comp = jit.AstCompiler("""
        def foo(a, b):
            return (a-b) + (a*b) - (a/b)
        """)
        fn = comp.compile()
        res = (3-4) + (3*4) - (3.0/4)
        assert fn(3, 4) == res

    def test_assign(self):
        comp = jit.AstCompiler("""
        def foo(a):
            b = a + 1
            return b
        """)
        fn = comp.compile()
        assert fn(41) == 42

    def test_if(self):
        comp = jit.AstCompiler("""
        def foo(a):
            if a < 0:
                return 0-a
            return a
        """)
        fn = comp.compile()
        assert fn(-42) == 42
        assert fn(42) == 42

    def test_while(self):
        comp = jit.AstCompiler("""
        def foo(a):
            tot = 0
            i = 0
            while i < a:
                tot = tot + i
                i = i + 1
            return tot
        """)
        fn = comp.compile()
        assert fn(5) == 1+2+3+4
