import mmap
import ast
import textwrap
from collections import defaultdict
from cffi import FFI
from peachpy import Argument, double_
from peachpy import x86_64 as asm
import astpretty

# workaround because peachpy forget to expose rsp
import peachpy
asm.rsp = peachpy.x86_64.registers.rsp


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
        self.nargs = len(args)
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

    def pushsd(self, reg):
        self.emit(asm.SUB(asm.rsp, 16))
        self.emit(asm.MOVSD(asm.qword[asm.rsp], reg))

    def popsd(self, reg):
        self.emit(asm.MOVSD(reg, asm.qword[asm.rsp]))
        self.emit(asm.ADD(asm.rsp, 16))

    def compile(self):
        abi_func = self._peachpy_fn.finalize(asm.abi.detect())
        enc_func = abi_func.encode()
        print(enc_func.format())
        code = enc_func.code_section.content
        return CompiledFunction(self.nargs, code)


class AstCompiler:

    def __init__(self, src):
        self.tree = ast.parse(textwrap.dedent(src))
        #astpretty.pprint(self.tree)
        self.assembler = None

    def compile(self):
        self.visit(self.tree)
        assert self.assembler is not None, 'No function found?'
        return self.assembler.compile()

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
        assert not self.assembler, 'cannot compile more than one function'
        argnames = [arg.arg for arg in node.args.args]
        self.assembler = FunctionAssembler(node.name, argnames)
        for child in node.body:
            self.visit(child)
        # XXX: emit a default return?

    def Return(self, node):
        self.visit(node.value)
        self.assembler.popsd(asm.xmm0)
        self.assembler.emit(asm.RET())

    def BinOp(self, node):
        OPS = {
            'ADD': asm.ADDSD,
            }
        opname = node.op.__class__.__name__.upper()
        self.visit(node.left)
        self.assembler.popsd(asm.xmm14)
        self.visit(node.right)
        self.assembler.popsd(asm.xmm15)
        self.assembler.emit(OPS[opname](asm.xmm14, asm.xmm15))
        self.assembler.pushsd(asm.xmm14)

    def Name(self, node):
        reg = self.assembler.var(node.id)
        self.assembler.pushsd(reg)
