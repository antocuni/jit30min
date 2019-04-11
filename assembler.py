import peachpy
from peachpy import Argument, double_, Constant
from peachpy import x86_64
# workaround because peachpy forget to expose rsp
x86_64.rsp = peachpy.x86_64.registers.rsp


class FunctionAssembler:

    from peachpy.x86_64 import (xmm0, xmm1, xmm2, xmm3, xmm4,
                                xmm5, xmm6, xmm7, xmm8, xmm9,
                                xmm10, xmm11, xmm12, xmm13,
                                xmm14, xmm15)

    def __init__(self, name, argnames):
        self.name = name
        self.nargs = len(argnames)
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

    def assemble_and_relocate(self):
        # this code has been copied and adapted from PeachPy: the goal is to
        # put the data section immediately contiguous to the code section:
        # this is suboptimal and dangerous because it mixes code and data and
        # puts the data inside an mmap-ed region with the executable flag, but
        # I don't want/don't have time to talk and explain this stuff during
        # the talk. Please forgive me :)

        encoded_func = self._encode()
        #print(); print(encoded_func.format())
        code_segment = bytearray(encoded_func.code_section.content)
        const_segment = bytearray(encoded_func.const_section.content)
        const_offset = len(code_segment)

        # Apply relocations
        from peachpy.x86_64.meta import RelocationType
        from peachpy.util import is_sint32
        for relocation in encoded_func.code_section.relocations:
            assert relocation.type == RelocationType.rip_disp32
            assert relocation.symbol in encoded_func.const_section.symbols
            old_value = code_segment[relocation.offset] | \
                (code_segment[relocation.offset + 1] << 8) | \
                (code_segment[relocation.offset + 2] << 16) | \
                (code_segment[relocation.offset + 3] << 24)

            # this is the biggest difference wrt peachpy
            new_value = (old_value + const_offset + relocation.symbol.offset +
                         -relocation.program_counter)
            #
            assert is_sint32(new_value)
            code_segment[relocation.offset] = new_value & 0xFF
            code_segment[relocation.offset + 1] = (new_value >> 8) & 0xFF
            code_segment[relocation.offset + 2] = (new_value >> 16) & 0xFF
            code_segment[relocation.offset + 3] = (new_value >> 24) & 0xFF
        assert not encoded_func.const_section.relocations

        return code_segment + const_segment
