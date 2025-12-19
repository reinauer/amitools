from amitools.vamos.libcore import LibImpl
from amitools.vamos.machine.regs import REG_A0
from amitools.vamos.astructs import AccessStruct
from amitools.vamos.libstructs import DateStampStruct

from datetime import datetime


class TimerDevice(LibImpl):
    def ReadEClock(self, ctx):
        eclockval = ctx.cpu.r_reg(REG_A0)

        dt = datetime.now()

        # abuse DateStampStruct (ds_Days -> ev_hi, ds_Minute -> ev_lo)
        tv = AccessStruct(ctx.mem, DateStampStruct, struct_addr=eclockval)
        tv.w_s("ds_Days", dt.microsecond // 1000000)
        tv.w_s("ds_Minute", dt.microsecond % 1000000)

        return 50
