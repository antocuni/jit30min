import peachpy
from peachpy import Argument, double_, Constant
from peachpy import x86_64
# workaround because peachpy forget to expose rsp
x86_64.rsp = peachpy.x86_64.registers.rsp


class FunctionAssembler:
    def __init__(self, name, argnames):
        self.name = name
        args = [Argument(double_, name=name) for name in argnames]
        self._peachpy_fn = x86_64.Function(name, args, double_)

    def __getattr__(self, name):
        obj = getattr(x86_64, name)
        if type(obj) is type and issubclass(obj, x86_64.instructions.Instruction):
            instr = obj
            def emit(*args):
                self._peachpy_fn.add_instruction(instr(*args))
            return emit
        else:
            return obj

    def const(self, val):
        return Constant.float64(float(val))

    def pushsd(self, reg):
        self.SUB(self.rsp, 16)
        self.MOVSD(self.qword[self.rsp], reg)

    def popsd(self, reg):
        self.MOVSD(reg, self.qword[self.rsp])
        self.ADD(self.rsp, 16)

    def _encode(self):
        abi_func = self._peachpy_fn.finalize(x86_64.abi.detect())
        return abi_func.encode()

    def compile(self):
        encoded_func = self._encode()
        #print(encoded_func.format())
        return encoded_func.code_section.content

    def _as_pyfunc(self):
        encoded_func = self._encode()
        return encoded_func.load()
