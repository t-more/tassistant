from assistant_context import TAssistantFeature
import subprocess


class ActiveWindowFeature(TAssistantFeature):

    def __init__(self):
        self.window_id = ""
        self.pid = ""
        self.program_name = ""

    def make_current_context_system_prompt(self) -> str:
        active_window = self.get_active_window_program()
        return f"Current active window: {active_window}"


    def update(self):
        self.window_id = ""
        self.pid = ""
        self.program_name = ""

        try:
            # Get window ID of active window
            self.window_id = subprocess.check_output(['xdotool', 'getactivewindow']).decode().strip()

            # Get PID of the window
            self.pid = subprocess.check_output(['xdotool', 'getwindowpid', self.window_id]).decode().strip()

            # Get program name from PID
            self.program_name = subprocess.check_output(['ps', '-p', self.pid, '-o', 'comm=']).decode().strip()
        except Exception as e:
            print(f"Error in ActiveWindowSystemPromptFeature")
            return

    def get_active_window_program(self):
        if self.program_name:
            return f"Current active window: {self.program_name}"
        else:
            return ""



class ClipboardFeature(TAssistantFeature):

    def __init__(self):
        self.clipboard = ""
        self.cliboard_size_limit = 10000

    def update(self):
        self.clipboard = self.get_clipboard_data()

    def make_current_context_system_prompt(self) -> str:
        if len(self.clipboard) <= self.cliboard_size_limit:
            return self.clipboard
        else:
            return ""


    def get_clipboard_data(self) -> str:
        p = subprocess.Popen(['xclip','-selection', 'clipboard', '-o'], stdout=subprocess.PIPE)
        retcode = p.wait()
        data = p.stdout.read()
        return data.decode('utf-8')
