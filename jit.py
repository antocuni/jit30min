import mmap
from cffi import FFI
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


class FunctionAssembler:

    def __init__(self):
        self.nargs = None
        self.instructions = []
        self.locals = {} # varname -> offset
        self._cur_offset = -0x08 # we start with the return address on the stack

    def var_offset(self, varname):
        try:
            return self.locals[varname]
        except KeyError:
            pass
        res = self.locals[varname] = self._cur_offset
        self._cur_offset -= 8
        return res

    def load_var(self, dst, varname):
        ofs = self.var_offset(varname)
        instr = asm.MOVSD(dst, asm.qword[asm.rbp + ofs])
        self.add(instr)

    def store_var(self, varname, src):
        ofs = self.var_offset(varname)
        instr = asm.MOVSD(asm.qword[asm.rbp + ofs], src)
        self.add(instr)

    def add(self, instr):
        self.instructions.append(instr)
