import logging
from .funcbase import FuncBase
from amitools.vamos.log import log_exec
from amitools.vamos.libtypes import MsgPort, Message
from amitools.vamos.libstructs import NodeType, MsgPortFlags


class MessageFunc(FuncBase):
    def __init__(self, ctx, exec_lib, signal_func, task_func, port_mgr):
        super().__init__(ctx, exec_lib)
        self.signal_func = signal_func
        self.task_func = task_func
        # legacy port mgr
        self.port_mgr = port_mgr

    def create_msg_port(self) -> MsgPort:
        # alloc signal first
        signal = self.signal_func.alloc_signal(-1)
        if signal == -1:
            log_exec.error("CreateMsgPort: no signal!")
            return None

        # get my task
        my_task = self.task_func.find_task(None)

        # alloc port
        msg_port = MsgPort.alloc(self.ctx.alloc, tag="exec_port")
        msg_port.new(sig_bit=signal, sig_task=my_task)
        log_exec.info(
            "CreateMsgPort: -> signal=%d my_task=%s port=%s", signal, my_task, msg_port
        )

        # dump msg port structure
        if log_exec.isEnabledFor(logging.DEBUG):
            msg_port.dump(log_exec.debug)

        return msg_port

    def delete_msg_port(self, msg_port: MsgPort):
        # get signal
        signal = msg_port.sig_bit.val
        log_exec.info("DeleteMsgPort(%s) (signal %d)", msg_port, signal)

        # free signal
        self.signal_func.free_signal(signal)

        # free port
        msg_port.free(self.ctx.alloc)

    def put_msg(self, port: MsgPort, msg: Message):
        # check legacy port manager first
        has_port = self.port_mgr.has_port(port.addr)
        if has_port:
            log_exec.info("PutMsg(%s, %s) -> PortMgr", port, msg)
            return self.port_mgr.put_msg(port.addr, msg.addr)

        # set type
        msg.node.type.val = NodeType.NT_MESSAGE

        # add to port list
        log_exec.info("PutMsg(%s, %s)", port, msg)
        port.msg_list.add_tail(msg.node)

        # signal?
        flags = port.flags.val
        if flags == MsgPortFlags.PA_SIGNAL:
            # post signal
            task = port.sig_task.aptr
            if task is None:
                log_exec.error("PutMsg: No task to signal?")
            else:
                sig_bit = port.sig_bit.val
                sig_mask = 1 << sig_bit
                log_exec.debug("PutMsg: set signal %s task %08x", sig_bit, task)
                self.signal_func.signal(task, sig_mask)
        elif flags == MsgPortFlags.PA_SOFTINT:
            log_exec.error("PutMsg: PA_SOFTINT is ignored!")
        elif flags == MsgPortFlags.PA_IGNORE:
            log_exec.debug("PutMsg: no notify")
        else:
            log_exec.error("PutMsg: unknown MsgPortFlags: %s", flags)

    def get_msg(self, port: MsgPort) -> Message:
        # check legacy port manager first
        has_port = self.port_mgr.has_port(port.addr)
        if has_port:
            msg = self.port_mgr.get_msg(port.addr)
            log_exec.info("GetMsg(%s) -> PortMgr -> %s", msg)
            return msg

        # get message list
        msg_list = port.msg_list

        # no messages
        if msg_list.is_empty():
            log_exec.info("GetMsg(%s) -> None", port)
            return None

        # get message
        msg = port.msg_list.rem_head().cast(Message)
        log_exec.info("GetMsg(%s) -> %s", port, msg)
        return msg

    def wait_port(self, port: MsgPort) -> Message:
        # check port mgr first
        has_port = self.port_mgr.has_port(port.addr)
        if has_port:
            has_msg = self.port_mgr.has_msg(port.addr)
            if not has_msg:
                log_exec.error(
                    "WaitPort: on empty message queue called: Port (%06x)", port.addr
                )
                return None
            msg_addr = self.port_mgr.peek_msg(port.addr)
            log_exec.info("WaitPort: peek message %06x", msg_addr)
            return Message(self.ctx.mem, msg_addr)

        # get sig mask
        sig_bit = port.sig_bit.val
        sig_mask = 1 << sig_bit
        msg_list = port.msg_list

        log_exec.info("WaitPort: port=%s", port)
        while msg_list.is_empty():
            log_exec.debug("WaitPort: waiting for signal %s", sig_bit)
            self.signal_func.wait(sig_mask)

        msg = msg_list.get_head().cast(Message)
        log_exec.info("WaitPort: return msg %s", msg)
        return msg
