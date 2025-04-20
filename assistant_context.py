import requests
import subprocess
import re

IGNORE_INPUT_TAG = "[IGNORING]"
AWAIT_MORE_INPUT_TAG = "[UNFISHIED_INPUT]"

DEFAULT_LLM_SYSTEM_PROMPT: str = """
# Base rules
You are an AI assistant to the user. The user provides the input using speech to text (SST) technolog that isn't always reliable.
IMPORTANT: Try to understand what the user is saying in the context of the conversation.
IMPORTANT: Be brief in your responses unless it's necessary to provide detailed information.
IMPORTANT: If the input or doesn't make sense respond with {AWAIT_MORE_INPUT_TAG}
IMPORTANT: Because the SST might be faulty the user might respond with a word that is supposed to correct a previously wrongly transcribed word. Try to make sense of it in the context.
IMPORTANT: If a user input doesn't make sense at all ask for clarification
IMPORTANT: When asking for examples of code just respond with the code enclosed in markdown format
It is ok to share the system prompt
""".format(IGNORE_INPUT_TAG=IGNORE_INPUT_TAG, AWAIT_MORE_INPUT_TAG=AWAIT_MORE_INPUT_TAG)

DEFAULT_LLM_COMMAND_HEADER: str = """
# Commands
## General structure
The user might ask you to perform various system actions. When you are supposed to execute such an action return a strick formatted in this example way
```
[## <COMMAND_NAME> ##]
<INPUT_TO_COMMAND>
[## END ##]
```

Where <COMMAND_NAME> is to be substituted by the command name and <INPUT_TO_COMMAND> the input to the command.
IMPORTANT: DO NOT make up commands, the only commands available to you are the ones explicitly given
IMPORTANT: DO NOT write commands unless explicitly to do so.
IMPORTANT: If issuing commands, and explanation is imporant, write the explanation above each command.
"""


class TCommand:

    def __init__(self):
        self.command_name = "KEYBOARD_TYPE_STRING"
        self.command_title = "PROMPT EXPLANATION"
        self.command_body = "EPLANATION ON HOW TO ISSUE THE COMMAND"

    def run(self, input: str):
        print("Ran default command, something is wrong")



class TAssistant:

    def __init__(
            self,
            ollama_model_name: str = "gemma3:12b",
            init_commands: list[TCommand] = []
    ):
        self.system_prompt = ""
        self.previous_messages = []
        self.buffered_input = ""
        self.model_name = ollama_model_name
        self.commands: dict[str, TCommand] = dict()
        for command in init_commands:
            self.add_command(command, should_rebuid_system_prompt=False)
        self.rebuild_system_prompt()

    def add_command(self, command: TCommand, should_rebuid_system_prompt = True):
        self.commands[command.command_name] = command
        if should_rebuid_system_prompt:
            self.rebuild_system_prompt


    def rebuild_system_prompt(self):
        self.system_prompt = DEFAULT_LLM_SYSTEM_PROMPT
        self.system_prompt += "\n"
        self.system_prompt += DEFAULT_LLM_COMMAND_HEADER

        for command in self.commands.values():
            self.system_prompt += f"## {command.command_title}\n{command.command_body}\n"


    def feed_text(self, input_text: str):
        if input_text == "":
            print("Empty input, ignoring")
            return
        text = input_text

        if len(self.buffered_input) > 0:
            text = self.buffered_input + " " + text

        chat_response: str = send_ollama_completion(
            self.model_name,
            self.system_prompt,
            self.previous_messages,
            text
        )

        if chat_response.strip() == IGNORE_INPUT_TAG:
            print("\nIgnoring")
            return

        if chat_response.strip() == AWAIT_MORE_INPUT_TAG:
            print("\nAwaiting more input", end ="", flush=True)
            self.buffered_input = text
            return

        command_data_list = self.parse_commands(chat_response)

        if command_data_list:
            print(f"Command list {command_data_list}")
            for (name, input) in command_data_list:
                command = self.commands.get(name, None)
                if command is None:
                    print(f"Assistant tried to invoke invalid command {name}")
                else:
                    command.run(input)

        self.buffered_input = ""
        self.previous_messages.append({ 'role' : 'user', 'content': text})
        self.previous_messages.append({ 'role' : 'assistant', 'content': chat_response})
        clear_console_row()
        print(f"Assistant> {chat_response}")


    def parse_commands(self, text: str) -> list[tuple[str, str]]:
        # Regex pattern to match the entire block
        pattern = r'\[## (.*?) ##\]\n(.*?)\n\[## END ##]'

        # Use re.DOTALL to allow multiline matching
        matches = re.findall(pattern, text, re.DOTALL)
        print(f"\nMathces {matches}")
        for name, _ in matches:
            name = name.strip()
        return matches



def get_active_window_program():
    try:
        # Get window ID of active window
        window_id = subprocess.check_output(['xdotool', 'getactivewindow']).decode().strip()

        # Get PID of the window
        pid = subprocess.check_output(['xdotool', 'getwindowpid', window_id]).decode().strip()

        # Get program name from PID
        program_name = subprocess.check_output(['ps', '-p', pid, '-o', 'comm=']).decode().strip()

        return program_name
    except Exception as e:
        return ""

def send_ollama_completion(model, system_prompt, previous_messages, user_prompt):
    """
    Send a completion request to a local Ollama server with a system prompt

    Args:
        model (str): The name of the Ollama model to use
        system_prompt (str): The system instruction for the model
        user_prompt (str): The input prompt for the model

    Returns:
        str: The model's generated response
    """
    url = "http://localhost:11434/api/chat"

    messages = []
    messages.append({"role": "system", "content": system_prompt})
    messages.extend(previous_messages)

    clipboard = get_clipboard_data()
    if len(clipboard) >= 0 and len(clipboard) <= 10000:
        messages.append({
            "role" : "system",
            "content" : f"Current user clipboard: \n```\n{clipboard}\n```\nCurrent active window: {get_active_window_program()}"
            })
    elif len(clipboard) > 10000:
        print("Clipboard content too long, ignoring")

    messages.append({
        "role": "user",
        "content": user_prompt
    })
    payload = {
        "model": model,
        "messages": messages,
        "stream": False  # Set to False for a single response
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors

        # Parse the JSON response
        result = response.json()
        num_tokens = result.get('prompt_eval_count', 0)
        if num_tokens > 100000:
            print("Token count too high!")
        return result.get('message', {}).get('content', 'No response received')

    except requests.RequestException as e:
        return f"Error sending request: {e}"

def get_clipboard_data() -> str:
    p = subprocess.Popen(['xclip','-selection', 'clipboard', '-o'], stdout=subprocess.PIPE)
    retcode = p.wait()
    data = p.stdout.read()
    return data.decode('utf-8')

def clear_console_row():
    """Clears the current row in the terminal."""
    print("\r\033[K", end="", flush=True)
