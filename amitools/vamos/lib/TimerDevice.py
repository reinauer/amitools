import time
from amitools.vamos.libcore import LibImpl
from amitools.vamos.machine.regs import REG_A0, REG_A1
from amitools.vamos.astructs import AccessStruct
from amitools.vamos.libstructs import DateStampStruct
from amitools.vamos.libstructs.exec_ import IORequestStruct

from datetime import datetime

# Timer commands
TR_ADDREQUEST = 9
TR_GETSYSTIME = 11


class TimerDevice(LibImpl):
    def BeginIO(self, ctx):
        """Handle timer IO requests."""
        io_addr = ctx.cpu.r_reg(REG_A1)
        io = AccessStruct(ctx.mem, IORequestStruct, io_addr)
        cmd = io.r_s("io_Command")

        # Clear error
        io.w_s("io_Error", 0)

        if cmd == TR_ADDREQUEST:
            # Timer request - read timeval from io_Data area
            # The timeval is at offset 32 in the timerequest structure
            # tv_secs at +32, tv_micro at +36
            tv_secs = ctx.mem.r32(io_addr + 32)
            tv_micro = ctx.mem.r32(io_addr + 36)
            delay_secs = tv_secs + tv_micro / 1000000.0
            # Cap at 1 second max to avoid long hangs, but still provide real delay
            if delay_secs > 0:
                time.sleep(min(delay_secs, 1.0))
        elif cmd == TR_GETSYSTIME:
            # Return current time
            now = time.time()
            ctx.mem.w32(io_addr + 32, int(now))
            ctx.mem.w32(io_addr + 36, int((now % 1) * 1000000))
        # Other commands just succeed
        return 0

    def ReadEClock(self, ctx):
        eclockval = ctx.cpu.r_reg(REG_A0)

        dt = datetime.now()

        # abuse DateStampStruct
        tv = AccessStruct(ctx.mem, DateStampStruct, struct_addr=eclockval)
        tv.ds_Days = dt.microsecond / 1000000
        tv.ds_Minute = dt.microsecond % 1000000

        return 50
