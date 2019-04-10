import mmap
from collections import defaultdict
from cffi import FFI
from peachpy import Argument, double_
from peachpy import x86_64 as asm

ffi = FFI()
ffi.cdef("typedef double (*d2_d_t)(double, double);")

class CompiledFunction:

    # XXX: for now we assume that the signature is (double, double) -> double
    def __init__(self, code):
        self.map = mmap.mmap(-1, len(code), mmap.MAP_PRIVATE,
                             mmap.PROT_READ | mmap.PROT_WRITE | mmap.PROT_EXEC)
        self.map[:len(code)] = code
        self.fptr = ffi.cast('d2_d_t', ffi.from_buffer(self.map))

    def __call__(self, *args):
        return self.fptr(*args)


class RegAllocator:

    REGISTERS = (asm.xmm0, asm.xmm1, asm.xmm2, asm.xmm3, asm.xmm4,
                 asm.xmm5, asm.xmm6, asm.xmm7, asm.xmm8, asm.xmm9,
                 asm.xmm10, asm.xmm11, asm.xmm12, asm.xmm13)

    SCRATCH = (asm.xmm14, asm.xmm15)

    def __init__(self):
        self.vars = defaultdict(self._allocate) # name -> reg

    def _allocate(self):
        n = len(self.vars)
        try:
            return self.REGISTERS[n]
        except IndexError:
            raise NotImplementedError("Register spilling not implemented")

    def get(self, varname):
        return self.vars[varname]


class FunctionAssembler:

    def __init__(self, name, args):
        self.name = name
        self._peachpy_fn = self._make_peachpy_fn(name, args)
        self._registers = RegAllocator()
        # force allocation of registers for arguments
        for arg in args:
            self._registers.get(arg)

    def _make_peachpy_fn(self, name, args):
        args = [Argument(double_, name=arg) for arg in args]
        return asm.Function(name, args)

    def var(self, name):
        return self._registers.get(name)

    def emit(self, instr):
        self._peachpy_fn.add_instruction(instr)

    def compile(self):
        abi_func = self._peachpy_fn.finalize(asm.abi.detect())
        enc_func = abi_func.encode()
        #print(enc_func.format())
        code = str(enc_func.code_section.content)
        return CompiledFunction(code)
