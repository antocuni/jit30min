import mmap
from cffi import FFI
ffi = FFI()
ffi.cdef("typedef double (*d2_d_t)(double, double);")

class CompiledFunction(object):

    def __init__(self, code):
        self.map = mmap.mmap(-1, len(code), mmap.MAP_PRIVATE,
                             mmap.PROT_READ | mmap.PROT_WRITE | mmap.PROT_EXEC)
        self.map[:len(code)] = code
        self.fptr = ffi.cast('d2_d_t', ffi.from_buffer(self.map))

    def __call__(self, *args):
        return self.fptr(*args)
