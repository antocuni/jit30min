from assembler import FunctionAssembler
from peachpy import x86_64

class TestFunctionAssembler:

    def test_getattr(self):
        asm = FunctionAssembler('foo', [])
        assert asm.xmm0 is x86_64.xmm0
        assert asm.rsp is x86_64.rsp
        assert asm.qword is x86_64.qword

    def test_opcode(self):
        asm = FunctionAssembler('foo', [])
        asm.ADDSD(asm.xmm0, asm.xmm1)
        assert len(asm._peachpy_fn._instructions) == 1
        assert asm._peachpy_fn._instructions[0].__class__.__name__ == 'ADDSD'

    def test_encode(self):
        asm = FunctionAssembler('foo', ['a', 'b'])
        asm.ADDSD(asm.xmm0, asm.xmm1)
        asm.RET()
        pyfn = asm._as_pyfunc()
        assert pyfn(3, 4) == 7

    def test_const(self):
        asm = FunctionAssembler('foo', ['a', 'b'])
        asm.ADDSD(asm.xmm0, asm.xmm1)
        asm.ADDSD(asm.xmm0, asm.const(100))
        asm.RET()
        pyfn = asm._as_pyfunc()
        assert pyfn(3, 4) == 107

