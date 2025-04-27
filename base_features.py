from types import TracebackType
from assistant_context import TAssistantFeature, AssistantFeatureContext
import subprocess
import emacs_ext

import i3ipc

class ActiveWindowFeature(TAssistantFeature):

    def __init__(self, context: AssistantFeatureContext):
        super().__init__(context)

        self.window_id = ""
        self.pid = ""
        self.program_name = ""
        self.i3_connection = None
        try:
            self.i3_connection = i3ipc.Connection()
            print("\nGot i3 connection!")
        except Exception as _:
            print("Failed to get i3 connection!")
            pass

    def make_current_context_system_prompt(self) -> str:
        active_window = self.get_active_window_program()
        return f"Current active window: {active_window}"


    def update(self):
        self._window_id = ""
        self._pid = ""
        self.program_name = ""

        try:

            if self.i3_connection is not None:
                focused_window = self.i3_connection.get_tree().find_focused()
                if focused_window is None:
                    print("Failed to find focused i3 window")
                else:
                    self.program_name = focused_window.window_instance
                return
            # Get window ID of active window

            self._window_id = subprocess.check_output(['xdotool', 'getactivewindow']).decode().strip()

            # Get PID of the window
            self._pid = subprocess.check_output(['xdotool', 'getwindowpid', self.window_id]).decode().strip()

            # Get program name from PID
            self.program_name = subprocess.check_output(['ps', '-p', self.pid, '-o', 'comm=']).decode().strip()
        except Exception as e:
            print(f"Error in ActiveWindowSystemPromptFeature")
            print(e)
            return

    def get_active_window_program(self):
        if self.program_name:
            return self.program_name
        else:
            return ""



class ClipboardFeature(TAssistantFeature):

    def __init__(self, context: AssistantFeatureContext):
        super().__init__(context)
        self.clipboard = ""
        self.cliboard_size_limit = 10000

    def update(self):
        self.clipboard = self.get_clipboard_data()


    def make_current_context_system_prompt(self) -> str:
        if len(self.clipboard) <= self.cliboard_size_limit:
            return f"Current user clipboard: `{self.clipboard}`"
        else:
            return "The user does not have anything in their clipboard"


    def get_clipboard_data(self) -> str:
        p = subprocess.Popen(['xclip','-selection', 'clipboard', '-o'], stdout=subprocess.PIPE)
        retcode = p.wait()
        data = p.stdout.read()
        return data.decode('utf-8')


class EmacsDetailsFeature(TAssistantFeature):

    _depdendencies = [ActiveWindowFeature]

    def __init__(self, context: AssistantFeatureContext):
        super().__init__(context)
        self.active_window_feature = context.get_feature(ActiveWindowFeature)
        self.current_buffer_name = ""
        self.current_buffer_content = ""
        self.current_line = ""
        self.currently_marked_region = ""

    def is_focusing_emacs(self) -> bool:
        return self.active_window_feature.program_name == "emacs"

    def update(self):
        if self.is_focusing_emacs():
            self.current_buffer_name = emacs_ext.run_in_current_buffer(
                "(buffer-name (current-buffer))"
            )

            buffer_content = emacs_ext.get_buffer_content_pure()

            buffer_content_with_line_numbers = ""
            current_line = 1
            for line in buffer_content.splitlines():
                buffer_content_with_line_numbers += str(current_line)
                buffer_content_with_line_numbers += "> "
                buffer_content_with_line_numbers += line
                buffer_content_with_line_numbers += '\n'
                current_line += 1

            self.current_buffer_content = buffer_content_with_line_numbers

            self.current_line = emacs_ext.run_in_current_buffer(
                "(line-number-at-pos)"
            )
            self.current_column = emacs_ext.run_in_current_buffer(
                "(current-column)"
            )
            self.currently_marked_region = emacs_ext.run_in_current_buffer(
                "(buffer-substring-no-properties (region-beginning) (region-end))"
            )



    def make_current_context_system_prompt(self) -> str:
        if not self.is_focusing_emacs():
            return ""

        content = [
            "Information about the users current emacs buffer",
            f"Current emacs buffer name: {self.current_buffer_name}",
            f"Current emacs buffer content (with line numbers at the start of each line):\n```\n{self.current_buffer_content}\n```",
            f"Currently marked region: ```\n{self.currently_marked_region}\n```",
            f"Current curspor position in the buffer line: {self.current_line} column {self.current_column}",
            "IMPORTANT: If the user asks you to write or modify things do so using the EMACS command",
            "IMPORTANT: If the user asks about information from the editor / emacs / buffer use this data first and only issue commands if this is not enough",
            "IMPORTANT: If the user asks to modify add or rename parts of a code file the use might not give the request using programming notation and syntax. Try to match such occurences with the style of the current file",


        ]
        return '\n'.join(content)
