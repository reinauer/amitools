"""
Minimal input.device stub for filesystem handlers.
FFS opens input.device during Init but only uses it for propagating disk events.
We provide a no-op implementation that just succeeds.
"""

from amitools.vamos.libcore import LibImpl
from amitools.vamos.machine.regs import REG_A1
from amitools.vamos.astructs import AccessStruct
from amitools.vamos.libstructs.exec_ import IORequestStruct


class InputDevice(LibImpl):
    def BeginIO(self, ctx):
        """Handle input IO requests - all succeed with no-op."""
        io_addr = ctx.cpu.r_reg(REG_A1)
        io = AccessStruct(ctx.mem, IORequestStruct, io_addr)
        # Clear error and mark complete
        io.w_s("io_Error", 0)
        return 0

    def AbortIO(self, ctx):
        """Abort an IO request - no-op."""
        return 0
