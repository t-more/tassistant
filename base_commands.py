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
        self.command_body = """
The user may ask you to check certain things in emacs when asked to do so respond with the EMACS command together with the emacs elisp you want to evaluate.
Emacs is the users default editor.
Never use yes-or-no-p for simple actions
```
[## EMACS ##]
<EMACS COMMAND(s)>
[## END ##]
```
Example:
[## EMACS ##]
(replace-first-in-buffer "def old_function_name(" "def new_function_name(")
[## END ##]

Here is some useful emacs commands:

###
####
To get the contents of the current buffer: do this
```
(substring-no-properties (buffer-string))
```
####
To go to a certain line (in this example, line 1 (the first line))
```
(goto-line 1)
```
####
To split a string (or buffer) at the lines type
```
(split-string (buffer-string) "\n")
```
####
To insert data into emacs prefer the use of insert command. It inserts data at the current position
```
(insert "example\ntext")
```
####
To replace part of the using a regex pattern, the first argument is a regex and the second is the text to replace it with
```
(replace-regexp "5" "fizz")
(replace-regexp "\\(2\\|8\\|9\\)" "buzz")
```
IMPORTANT: When asking you to replace occursence remember to go to the first line before running the command.
####
When you should replace an exact region in a buffer use the following command. First argument should be the exact text to replace.
```
(replace-first-in-buffer "def old_function_name(" "def new_function_name(")
```
IMPORTANT: When asked to delete something use replace-first-in-buffer and provide an empty string as the argument.
####
When asked to go to a specific word or phrase in code you can use `search-and-goto-start` to go to the start of the match.
```
(search-and-goto-start "<STRING_TO_GO_TO>")
```
IMPORTANT: When asked to go to a certain function use this command with a unique part of the string that identifies that area.

        """

        self.emacs = emacs.EmacsClient()

    def run(self, input: str):
        print(f"Evaluating emacs command '{input}'")
        res = emacs_ext.run_in_current_buffer(f"\n{input}")
        print(f"Result '{res}'")
