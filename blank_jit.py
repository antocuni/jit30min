import mmap
import ast
import textwrap
import inspect
from collections import defaultdict
from cffi import FFI
from assembler import FunctionAssembler as FA

## code = b'\xf2\x0f\x58\xc1\xc3' # addsd  xmm0,xmm1 ; ret
## buf = mmap.mmap(-1, len(code), mmap.MAP_PRIVATE,
##                 mmap.PROT_READ | mmap.PROT_WRITE |
##                 mmap.PROT_EXEC)
## buf[:] = code

## ffi = FFI()
## ffi.cdef("""
##     typedef double (*fn0)(void);
##     typedef double (*fn1)(double);
##     typedef double (*fn2)(double, double);
##     typedef double (*fn3)(double, double, double);
## """)

## fptr = ffi.cast("fn2", ffi.from_buffer(buf))
## print(fptr(5, 2))


## class CompiledFunction:

##     def __init__(self, nargs, code):
##         ...
##         fntype = 'fn%d' % nargs
##         self.fptr = ffi.cast(fntype, ffi.from_buffer(self.buf))

##     def __call__(self, *args):
##         return self.fptr(*args)








## class RegAllocator:

##     REGISTERS = (FA.xmm0, FA.xmm1, FA.xmm2, FA.xmm3, FA.xmm4,
##                  FA.xmm5, FA.xmm6, FA.xmm7, FA.xmm8, FA.xmm9,
##                  FA.xmm10, FA.xmm11, FA.xmm12, FA.xmm13,
##                  FA.xmm14, FA.xmm15)





## class AstCompiler:

##     def __init__(self, src):
##         self.tree = ast.parse(textwrap.dedent(src))
##         self.asm = None

##     def show(self, node):
##         import astpretty
##         from ast2png import ast2png
##         astpretty.pprint(node)
##         ast2png(self.tree, highlight_node=node, filename='ast.png')
## 
##     def compile(self):
##         self.visit(self.tree)
##         assert self.asm is not None, 'No function found?'
##         code = self.asm.assemble_and_relocate()
##         return CompiledFunction(self.asm.nargs, code)
##
##     def visit(self, node):
##         methname = node.__class__.__name__
##         meth = getattr(self, methname, None)
##         if meth is None:
##             raise NotImplementedError(methname)
##         return meth(node)
