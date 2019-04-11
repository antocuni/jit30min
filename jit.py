import mmap
import ast
import textwrap
from collections import defaultdict
from cffi import FFI
import astpretty
from assembler import FunctionAssembler as FA

ffi = FFI()
ffi.cdef("""
    typedef double (*fn0)(void);
    typedef double (*fn1)(double);
    typedef double (*fn2)(double, double);
    typedef double (*fn3)(double, double, double);
""")

class CompiledFunction:

    def __init__(self, nargs, code):
        self.map = mmap.mmap(-1, len(code), mmap.MAP_PRIVATE,
                             mmap.PROT_READ | mmap.PROT_WRITE | mmap.PROT_EXEC)
        self.map[:len(code)] = code
        fntype = 'fn%d' % nargs
        self.fptr = ffi.cast(fntype, ffi.from_buffer(self.map))

    def __call__(self, *args):
        return self.fptr(*args)


class RegAllocator:

    REGISTERS = (FA.xmm0, FA.xmm1, FA.xmm2, FA.xmm3, FA.xmm4, FA.xmm5,
                 FA.xmm6, FA.xmm7, FA.xmm8, FA.xmm9, FA.xmm10, FA.xmm11,
                 FA.xmm12, FA.xmm13)
    SCRATCH = (FA.xmm14, FA.xmm15)

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


class AstCompiler:

    def __init__(self, src):
        self.tree = ast.parse(textwrap.dedent(src))
        #astpretty.pprint(self.tree)
        self.asm = None
        self.regs = None

    def compile(self):
        self.visit(self.tree)
        assert self.asm is not None, 'No function found?'
        code = self.asm.assemble_and_relocate()
        return CompiledFunction(self.asm.nargs, code)

    def visit(self, node):
        methname = node.__class__.__name__
        meth = getattr(self, methname, None)
        if meth is None:
            raise NotImplementedError(methname)
        meth(node)

    def Module(self, node):
        for child in node.body:
            self.visit(child)

    def FunctionDef(self, node):
        assert not self.asm, 'cannot compile more than one function'
        argnames = [arg.arg for arg in node.args.args]
        self.asm = FA(node.name, argnames)
        self.regs = RegAllocator()
        for argname in argnames:
            self.regs.get(argname)
        for child in node.body:
            self.visit(child)
        #
        # by default, a function returns 0 if not explict return has been
        # executed
        self.asm.PXOR(self.asm.xmm0, self.asm.xmm0)
        self.asm.RET()

    def Pass(self, node):
        pass

    def Return(self, node):
        self.visit(node.value)
        self.asm.popsd(self.asm.xmm0)
        self.asm.RET()

    def BinOp(self, node):
        OPS = {
            'ADD': self.asm.ADDSD,
            'SUB': self.asm.SUBSD,
            }
        opname = node.op.__class__.__name__.upper()
        self.visit(node.left)
        self.asm.popsd(self.asm.xmm14)
        self.visit(node.right)
        self.asm.popsd(self.asm.xmm15)
        OPS[opname](self.asm.xmm14, self.asm.xmm15)
        self.asm.pushsd(self.asm.xmm14)

    def Name(self, node):
        reg = self.regs.get(node.id)
        self.asm.pushsd(reg)
