from assistant_context import TCommand, TAssistant

from pynput.keyboard import Key, Controller

import emacs

import subprocess

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
For example if the user asks you to write "Potato" on the keyboard you respond with
```
[## KEYBOARD_TYPE_STRING ##]
Potato
[## END ##]
```
        """

        self.keyboard_controller = Controller()

    def run(self, input: str):
        print(f"Typing '{input}'")
        self.keyboard_controller.type(input)



class EmacsTCommand(TCommand):

    def __init__(self):
        self.command_name = "EMACS"
        self.command_title = "Interacting with emacs"
        self.command_body = """
The user may ask you to check certain things in emacs when asked to do so respond with the EMACS command together with the emacs elisp you want to evaluate.
Emacs is the users default editor.
Never use yes-or-no-p for simple actions
```
[## EMACS ##]
<EMACS COMMAND(s)>
[## END ##]
```
IMPORANT: Before invoking commands that may change the data in the buffer, ask for permision
```
[## EMACS ##]
(buffer-name (current-buffer))
[## END ##]
```

Here is some useful emacs commands:

###
To get the contents of the current buffer: do this
```
(substring-no-properties (buffer-string))
```

        """

        self.emacs = emacs.EmacsClient()

    def run(self, input: str):
        print(f"Evaluating emacs command '{input}'")
        p = subprocess.Popen(['emacsclient','--eval', f'(with-current-buffer (window-buffer (frame-selected-window (selected-frame))) {input})'], stdout=subprocess.PIPE)
        retcode = p.wait()
        data:bytes = p.stdout.read()
        res = data.decode("utf-8").strip()
        print(f"Result '{res}'")
