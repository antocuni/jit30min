import mmap
import ast
import textwrap
import inspect
from collections import defaultdict
from cffi import FFI
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
        self.buf = mmap.mmap(-1, len(code), mmap.MAP_PRIVATE,
                             mmap.PROT_READ | mmap.PROT_WRITE |
                             mmap.PROT_EXEC)
        self.buf[:len(code)] = code
        fntype = 'fn%d' % nargs
        self.fptr = ffi.cast(fntype, ffi.from_buffer(self.buf))

    def __call__(self, *args):
        return self.fptr(*args)


class RegAllocator:

    REGISTERS = (FA.xmm0, FA.xmm1, FA.xmm2, FA.xmm3, FA.xmm4,
                 FA.xmm5, FA.xmm6, FA.xmm7, FA.xmm8, FA.xmm9,
                 FA.xmm10, FA.xmm11, FA.xmm12, FA.xmm13,
                 FA.xmm14, FA.xmm15)

    def __init__(self):
        self._registers = list(reversed(self.REGISTERS))
        self.vars = defaultdict(self._allocate) # name -> reg

    def _allocate(self):
        try:
            return self._registers.pop()
        except IndexError:
            raise NotImplementedError("Too many variables: register spilling not implemented")

    def get(self, varname):
        return self.vars[varname]

class AstCompiler:

    def __init__(self, src):
        self.tree = ast.parse(textwrap.dedent(src))
        self.asm = None

    def show(self, node):
        import astpretty
        from ast2png import ast2png
        astpretty.pprint(node)
        ast2png(self.tree, highlight_node=node, filename='ast.png')

    def _newfunc(self, name, argnames):
        self.asm = FA(name, argnames)
        self.regs = RegAllocator()
        for argname in argnames:
            self.regs.get(argname)
        self.tmp0 = self.regs.get('__scratch_register_0__')
        self.tmp1 = self.regs.get('__scratch_register_1__')

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
        return meth(node)

    def Module(self, node):
        for child in node.body:
            self.visit(child)

    def FunctionDef(self, node):
        assert not self.asm, 'cannot compile more than one function'
        argnames = [arg.arg for arg in node.args.args]
        self._newfunc(node.name, argnames)
        for child in node.body:
            self.visit(child)
        # return 0 by default
        self.asm.PXOR(self.asm.xmm0, self.asm.xmm0)
        self.asm.RET()

    def Pass(self, node):
        pass

    def Return(self, node):
        self.visit(node.value)
        self.asm.popsd(self.asm.xmm0)
        self.asm.RET()

    def Num(self, node):
        self.asm.MOVSD(self.tmp0, self.asm.const(node.n))
        self.asm.pushsd(self.tmp0)

    def BinOp(self, node):
        OPS = {
            'ADD': self.asm.ADDSD,
            'SUB': self.asm.SUBSD,
            'MULT': self.asm.MULSD,
            'DIV': self.asm.DIVSD,
            }
        opname = node.op.__class__.__name__.upper()
        self.visit(node.left)
        self.visit(node.right)
        self.asm.popsd(self.tmp1)
        self.asm.popsd(self.tmp0)
        OPS[opname](self.tmp0, self.tmp1)
        self.asm.pushsd(self.tmp0)

    def Name(self, node):
        reg = self.regs.get(node.id)
        self.asm.pushsd(reg)

    def Assign(self, node):
        assert len(node.targets) == 1
        varname = node.targets[0].id
        reg = self.regs.get(varname)
        self.visit(node.value)
        self.asm.popsd(self.tmp0)
        self.asm.MOVSD(reg, self.tmp0)

    def If(self, node):
        """
            IF <test> GOTO then_label
            GOTO end_label
        then_label:
            <BODY>
        end_label:
            ...
        """
        CMP = {
            'LT': self.asm.JB
            }
        assert not node.orelse
        then_label = self.asm.Label()
        end_label = self.asm.Label()
        op = self.visit(node.test)
        CMP[op](then_label)
        self.asm.JMP(end_label)
        self.asm.LABEL(then_label)
        for child in node.body:
            self.visit(child)
        self.asm.LABEL(end_label)

    def Compare(self, node):
        assert len(node.ops) == 1
        cmp_op = node.ops[0].__class__.__name__.upper()
        self.visit(node.left)
        self.visit(node.comparators[0])
        self.asm.popsd(self.tmp1)
        self.asm.popsd(self.tmp0)
        self.asm.UCOMISD(self.tmp0, self.tmp1)
        return cmp_op

    def While(self, node):
        """
        begin_label:
            IF <test> GOTO body_label
            GOTO end_label
        body_label:
            <BODY>
            GOTO begin_label
        end_label:
            ...
        """
        CMP = {
            'LT': self.asm.JB
            }
        begin_label = self.asm.Label()
        body_label = self.asm.Label()
        end_label = self.asm.Label()
        #
        self.asm.LABEL(begin_label)
        op = self.visit(node.test)
        CMP[op](body_label)
        self.asm.JMP(end_label)
        self.asm.LABEL(body_label)
        for child in node.body:
            self.visit(child)
        self.asm.JMP(begin_label)
        self.asm.LABEL(end_label)


def jit(fn):
    src = inspect.getsource(fn)
    comp = AstCompiler(src)
    return comp.compile()
