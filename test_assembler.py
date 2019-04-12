from assembler import FunctionAssembler
from peachpy import x86_64

class TestFunctionAssembler:

    def load(self, asm):
        encoded_func = asm._encode()
        return encoded_func.load()

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
        pyfn = self.load(asm)
        assert pyfn(3, 4) == 7

    def test_const(self):
        asm = FunctionAssembler('foo', ['a', 'b'])
        asm.ADDSD(asm.xmm0, asm.xmm1)
        asm.ADDSD(asm.xmm0, asm.const(100))
        asm.RET()
        pyfn = self.load(asm)
        assert pyfn(3, 4) == 107

    def test_pushsd_popsd(self):
        asm = FunctionAssembler('foo', ['a', 'b', 'c'])
        asm.pushsd(asm.xmm0)
        asm.pushsd(asm.xmm1)
        asm.pushsd(asm.xmm2)
        asm.PXOR(asm.xmm0, asm.xmm0)        # xmm0 = 0
        asm.popsd(asm.xmm1)
        asm.MULSD(asm.xmm1, asm.const(100)) # xmm0 += (xmm1*100)
        asm.ADDSD(asm.xmm0, asm.xmm1)
        asm.popsd(asm.xmm1)
        asm.MULSD(asm.xmm1, asm.const(10)) # xmm0 += (xmm1*10)
        asm.ADDSD(asm.xmm0, asm.xmm1)
        asm.popsd(asm.xmm1)
        asm.ADDSD(asm.xmm0, asm.xmm1)
        asm.RET()
        pyfn = self.load(asm)
        assert pyfn(1, 2, 3) == 321

    def test_jump(self):
        asm = FunctionAssembler('foo', [])
        label = asm.Label()
        asm.MOVSD(asm.xmm0, asm.const(42))
        asm.JMP(label)
        asm.MOVSD(asm.xmm0, asm.const(123)) # this is not executed
        asm.LABEL(label)
        asm.RET()
        pyfn = self.load(asm)
        assert pyfn() == 42
