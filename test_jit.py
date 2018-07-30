import jit

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
