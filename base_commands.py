from assistant_context import TCommand, TAssistant

from pynput.keyboard import Key, Controller

import emacs

import subprocess

import emacs_ext

class KeyboardInputTCommand(TCommand):


    def __init__(self):
        self.command_name = "KEYBOARD_TYPE_STRING"
        self.command_title = "Typing character strings to the keyboard"
        self.command_body = """
If the use asks you to type something on the keyboard you run the KEYBOARD_TYPE_STRING command together with the
```
[## KEYBOARD_TYPE_STRING ##]
<KEYBOARD_INPUT_STRING>
[## END ##]
```
IMPORANT: DO NOT invoke this command unless the last user prompt asks you to
For example if the user asks you to write "Potato" on the keyboard you respond with (do not respond with the markdown region)
```
[## KEYBOARD_TYPE_STRING ##]
Potato
[## END ##]
```

IMPORANT: If you want to show the user what command you will do before doing it do not include the [## and ##] part. Only use those when you want to execute the command.
        """

        self.keyboard_controller = Controller()

    def run(self, input: str):
        print(f"Typing '{input}'")
        self.keyboard_controller.type(input)



class EmacsTCommand(TCommand):

    def __init__(self):
        self.command_name = "EMACS"
        self.command_title = "Interacting with emacs"
        self.command_body = ""
        self.command_body_file = "emacs_body.txt"

        self.emacs = emacs.EmacsClient()

    def run(self, input: str):
        print(f"Evaluating emacs command '{input}'")
        res = emacs_ext.run_in_current_buffer(f"\n{input}")
        print(f"Result '{res}'")
