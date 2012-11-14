#!/usr/bin/env python
# -*- coding: utf-8 -*-

import multiprocessing
import time

from SDS.components.dm.common import dm_factory, get_dm_type


from SDS.components.hub.messages import Command, SLUHyp, DMDA
from SDS.utils.exception import DMException


class DM(multiprocessing.Process):
    """DM accepts N-best list hypothesis or a confusion network generated by an SLU component.
    The result of this component is an output dialogue act.

    When the component receives an SLU hypothesis then it immediately responds with an dialogue act.

    This component is a wrapper around multiple dialogue managers which handles multiprocessing
    communication.
    """

    def __init__(self, cfg, commands, slu_hypotheses_in, dialogue_act_out):
        multiprocessing.Process.__init__(self)

        self.cfg = cfg
        self.commands = commands
        self.slu_hypotheses_in = slu_hypotheses_in
        self.dialogue_act_out = dialogue_act_out

        dm_type = get_dm_type(cfg)
        self.dm = dm_factory(dm_type, cfg)

    def process_pending_commands(self):
        """Process all pending commands.

        Available comamnds:
          stop() - stop processing and exit the process
          flush() - flush input buffers.
            Now it only flushes the input connection.

        Return True if the process should terminate.
        """

        if self.commands.poll():
            command = self.commands.recv()
            if self.cfg['DM']['debug']:
                self.cfg['Logging']['system_logger'].debug(command)

            if isinstance(command, Command):
                if command.parsed['__name__'] == 'stop':
                    return True

                if command.parsed['__name__'] == 'flush':
                    # discard all data in in input buffers
                    while self.slu_hypotheses_in.poll():
                        data_in = self.slu_hypotheses_in.recv()

                    self.dm.new_dialogue()

                    return False

                if command.parsed['__name__'] == 'new_dialogue':
                    self.dm.new_dialogue()

                    # I should generate the first DM output
                    da = self.dm.da_out()

                    if self.cfg['DM']['debug']:
                        s = []
                        s.append("DM Output")
                        s.append("-"*60)
                        s.append(str(da))
                        s.append("")
                        s = '\n'.join(s)
                        self.cfg['Logging']['system_logger'].debug(s)

                    self.dialogue_act_out.send(DMDA(da))
                    self.commands.send(Command('dm_da_generated()', 'DM', 'HUB'))

                    return False

                if command.parsed['__name__'] == 'end_dialogue':
                    self.dm.end_dialogue()
                    return False

        return False

    def read_slu_hypotheses_write_dialogue_act(self):
        # read SLU hypothesis
        while self.slu_hypotheses_in.poll():
            # read SLU hypothesis
            data_slu = self.slu_hypotheses_in.recv()

            if isinstance(data_slu, SLUHyp):
                self.dm.da_in(data_slu.hyp)
                da = self.dm.da_out()

                if self.cfg['DM']['debug']:
                    s = []
                    s.append("DM Output")
                    s.append("-"*60)
                    s.append(str(da))
                    s.append("")
                    s = '\n'.join(s)
                    self.cfg['Logging']['system_logger'].debug(s)

                self.dialogue_act_out.send(DMDA(da))
                self.commands.send(Command('dm_da_generated()', 'DM', 'HUB'))

                if da == "bye()":
                    self.commands.send(Command('hangup()', 'DM', 'HUB'))

            elif isinstance(data_slu, Command):
                cfg['Logging']['system_logger'].info(data_slu)
            else:
                raise DMException('Unsupported input.')

    def run(self):
        self.recognition_on = False

        while 1:
            time.sleep(self.cfg['Hub']['main_loop_sleep_time'])

            # process all pending commands
            if self.process_pending_commands():
                return

            # process the incoming SLU hypothesis
            self.read_slu_hypotheses_write_dialogue_act()
