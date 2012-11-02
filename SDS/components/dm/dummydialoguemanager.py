#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import *

from SDS.components.dm.__init__ import *
from SDS.components.slu.da import *
from SDS.utils.exception import *


class DummyDialogueState(object):
    """This is a trivial implementation of a dialogue state and its update.

    It uses only the best dialogue act from the input and based on this it updates its state.

    """

    def __init__(self):
        self.slots = defaultdict(lambda: "None")
        self.turns = defaultdict(list)

    def restart(self):
        """Reinitialise the dialogue state so that the dialogue manager can start from scratch.

        Nevertheless, remember the turn history.
        """

        self.slots = defaultdict(lambda: "None")

    def update(self, user_da, last_system_da):
        """Interface for the dialogue act update.

        It can process dialogue act, dialogue act N best lists, or dialogue act confusion networks.
        """

        if isinstance(user_da, DialogueAct):
            # use da as it is
            pass
        elif isinstance(user_da, DialogueActNBList) or isinstance(user_da, DialogueActConfusionNetwork):
            # get only the best dialogue act
            da = da.get_best_da(user_da)
        else:
            raise DummyDialogueManagerException(
                "Unsupported input for the dialogue manager.")

        # store the input
        self.turns.append([user_da, last_system_da])

        # perform the update
        user_da = self.context_resolution(user_da, last_system_da)
        self.state_update(user_da, last_system_da)

    def context_resulution(self, user_da, last_system_da):
        """Resolves and converts meaning of some user dialogue acts given the context."""

        new_user_da = DialogueAct()

        for user_dai in user_da:
            if last_system_da == "confirm" and user_dai.dat == "affirm":
                user_dai = DialogueActItem(
                    "inform", last_system_da.name, last_system_da.value)

            elif last_system_da == "confirm" and user_dai.dat == "negate":
                user_dai = DialogueActItem(
                    "deny", last_system_da.name, last_system_da.value)

            elif last_system_da == "request" and user_dai.dat == "inform" and \
                    user_dai.name == "" and user_dai.value == "dontcare":
                user_dai = DialogueActItem(
                    "inform", last_system_da.name, last_system_da.value)

            elif last_system_da == "request" and user_dai.dat == "affirm" and user_dai.name.startswith("has_"):
                user_dai = DialogueActItem(
                    "inform", last_system_da.name, "true")

            elif last_system_da == "request" and user_dai.dat == "negate" and user_dai.name.startswith("has_"):
                user_dai = DialogueActItem(
                    "inform", last_system_da.name, "false")

            elif last_system_da == "request" and user_dai.dat == "affirm" and user_dai.name.endswith("_allowed"):
                user_dai = DialogueActItem(
                    "inform", last_system_da.name, "true")

            elif last_system_da == "request" and user_dai.dat == "negate" and user_dai.name.endswith("_allowed"):
                user_dai = DialogueActItem(
                    "inform", last_system_da.name, "false")

        return user_da

    def state_update(self, user_da):
        """Records the information provided by the system and/or by the user."""

        # first process the system dialogue act since it was produce "earlier"
        for dai in last_system_da:
            if dai.dat == "inform":
                # set that the system already informed about the slot
                self.slots["rh_" + dai.name] = "system-informed"
                self.slots["ch_" + dai.name] = "system-informed"
                self.slots["sh_" + dai.name] = "system-informed"

        # now process the user dialogue act
        for dai in user_da:
            if dai.dat == "inform":
                if dai.name:
                    self.slots[dai.name] = dai.value
            elif dai.dat == "deny":
                if self.slots[dai.name] == dai.value:
                    # it must be changed since user does not want this but we do not know for what to change it
                    # therefore it will be changed to None
                    self.slots[dai.name] = "None"
                else:
                    # the value of the slot is different. therefore it does not conflict with the provided information
                    pass
            elif dai.dat == "request":
                self.slots["rh_" + dai.name] = dai.value
            elif dai.dat == "confirm":
                self.slots["ch_" + dai.name] = dai.value
            elif dai.dat == "select":
                self.slots["sh_" + dai.name] = dai.value
            elif dai.dat in ["ack", "apology", "bye", "hangup", "hello", "help", "null",
                             "repeat", "reqalts", "reqmore", "restart", "thankyou"]:
                self.slots["lda"] = dai.dat

    def get_requested_slots(self):
        """Return all slots which are currently being requested by the user."""
        requested_slots = []

        for slot in self.slots:
            if slot.startswith("rh_") and self.slots[slot] == "user-requested":
                requested_slots.append(slot[3:])

        return requested_slots

    def get_confirmed_slots(self):
        """Return all slots which are currently being confirmed by the user."""
        confirmed_slots = {}

        for slot in self.slots:
            if slot.startswith("ch_") and self.slots[slot] != "None" and self.slots[slot] != "system-informed":
                confimed_slots[slot[3:]] = self.slots[slot]

        return confimed_slots_slots


class DummyPolicy(object):
    """This is a trivial policy just to demonstrate basic functionality DM."""

    def __init__(self):
        self.das = []
        self.last_dialogue_act = None

    def get_da(self, dialogue_state):

        requested_slots == dialogue_state.get_requested_slots()
        confimed_slots == dialogue_state.get_confirmed_slots()

        if len(self.das) == 0:
            # NLG("Thank you for calling. How may I help you?")
            self.last_dialogue_act = DialogueAct("thankyou()&hello()")
            self.slots["lda"] = "None"

        elif dialogue_state.slots["lda"] == "bye":
            # NLG("Goodbye.")
            self.last_dialogue_act = DialogueAct("bye()")
            self.slots["lda"] = "None"

        elif dialogue_state.slots["lda"] == "restart":
            # NLG("Let's start again from scratch. How may I help you?")
            dialogue_state.restart()
            self.last_dialogue_act = DialogueAct("restart()&hello()")
            self.slots["lda"] = "None"

        elif dialogue_state.slots["lda"] == "repeat":
            # NLG - use the last dialogue act
            self.slots["lda"] = "None"

        elif dialogue_state.slots["lda"] == "reqalts":
            # NLG("There is nothing else in the database.")
            self.last_dialogue_act = DialogueAct("deny(alternatives=true")
            self.slots["lda"] = "None"

        elif requested_slots:
            # inform about all requested slots
            self.last_dialogue_act = DialogueAct()
            for slot in requested_slots:
                dai = DiaqlogueActItem(
                    "inform", slot, dialogue_state.slots[slot])
                self.last_dialogue_act.append(dai)

        elif confirmed_slots:
            # inform about all slots being confirmed by the user
            self.last_dialogue_act = DialogueAct()
            for slot in confirmed_slots:
                if confirmed_slots[slot] == dialogue_state[slot]:
                    # it is as user expected
                    dai = DialogueActItem(
                        "inform", slot, dialogue_state.slots[slot])
                    self.last_dialogue_act.append(DialogueActItem("affirm"))
                    self.last_dialogue_act.append(dai)
                else:
                    # it is something else to what user expected
                    self.last_dialogue_act.append(DialogueActItem("negate"))
                    dai = DiaqlogueActItem(
                        "deny", slot, dialogue_state.slots[slot])
                    self.last_dialogue_act.append(dai)
        else:
            # NLG("Can I help you with anything else?")
            self.last_dialogue_act = DialogueAct("reqmore()")
            self.slots["lda"] = "None"

        # record the system dialogue acts
        self.das.append(self.last_dialogue_act)
        return self.last_dialogue_act


class DummyDM(DialogueManager):
    """This is an example of an dialogue manager. It is fully handcrafted and it has a limited functionality.

    The dialogue state and the dialogue policy are implemented in a very simplistic way.

    The purpose of this class is to serve for debugging and testing of other components when building the
    full dialogue system.

    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.last_dialogue_act = None

    def new_dialogue(self):
        """Initialise the dialogue manager and makes it ready for a new dialogue conversation."""

        self.dialogue_state = DummyDialogueState()
        self.policy = DummyPolicy()

    def da_in(self, da):
        """Receives an input dialogue act or dialogue act list with probabilities or dialogue act confusion network.

        When the dialogue act is received, an update of the state is performed.
        """

        self.dialogue_state.update(da, self.last_dialogue_act)

    def da_out(self):
        """Produces output dialogue act."""

        self.last_dialogue_act = self.policy.get_da(self.dialogue_state)

        return self.last_dialogue_act

    def end_dialogue(self):
        """Ends the dialogue and post-process the data."""
        pass