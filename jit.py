import mmap
from cffi import FFI
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
