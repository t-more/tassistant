import requests
import re

from typing import Self, TypeVar

IGNORE_INPUT_TAG = "[IGNORING]"
AWAIT_MORE_INPUT_TAG = "[UNFISHIED_INPUT]"

DEFAULT_LLM_SYSTEM_PROMPT: str = """
# Base rules
You are an AI assistant to the user. The user provides the input using speech to text (SST) technolog that isn't always reliable.
IMPORTANT: Try to understand what the user is saying in the context of the conversation.
IMPORTANT: Be brief in your responses unless it's necessary to provide detailed information.
IMPORTANT: When asked to write code. Just do what you think is the best thing given the criteria. The user will provide more information if neccessary.
IMPORTANT: If the input or doesn't make sense respond with {AWAIT_MORE_INPUT_TAG}
IMPORTANT: Because the SST might be faulty the user might respond with a word that is supposed to correct a previously wrongly transcribed word. Try to make sense of it in the context.
IMPORTANT: If a user input doesn't make sense at all ask for clarification
IMPORTANT: When asking for examples of code just respond with the code enclosed in markdown format
It is ok to share the system prompt
IMPORTANT: When the user speaks about doing actions. If it makes sense assume the actions should be performed in the current window.

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
IMPORTANT: Only use commands that have been specified to you in a system prompt.
IMPORTANT: Do not write commands unless explicitly to do so.
"""

SomeFeature = TypeVar('SomeFeature', bound="TAssistantFeature")

class AssistantFeatureContext:

    def __init__(self):
        self.features: list["TAssistantFeature"] = []
        self.feature_class_dict: dict[type["TAssistantFeature"], "TAssistantFeature"] = {}

    def init_feature(self, feature_class: type["TAssistantFeature"]) -> "TAssistantFeature":
        if feature_class in self.feature_class_dict:
            return self.feature_class_dict[feature_class]

        for depdendency in feature_class._dependencies:
            self.init_feature(depdendency)

        feature_instance = feature_class(self)
        self.feature_class_dict[feature_class] = feature_instance
        self.features.append(feature_instance)
        return feature_instance

    def get_feature(self, feature_class: type[SomeFeature]) -> SomeFeature:
        if feature_class in self.feature_class_dict:
            return self.feature_class_dict[feature_class]
        else:
            raise Exception(f"Cannot find feature {feature_class} in dict {self.feature_class_dict}")

    def update_features(self):
        for feature in self.features:
            feature.update()

    def build_context_system_prompt(self) -> str:
        results = []
        for feature in self.features:
            row = feature.make_current_context_system_prompt().strip()
            if row:
                results.append(row)

        return '\n'.join(results)

class TAssistantFeature:

    _dependencies: list[type[Self]] = []

    def __init__(self, feature_context: AssistantFeatureContext):
        self._feature_context = feature_context
        pass

    def get_feature(self, feature_class: type[SomeFeature]) -> SomeFeature:
        res = self._feature_context.get_feature(feature_class)
        return res

    def update(self):
        pass

    def make_current_context_system_prompt(self) -> str:
        return ""

class TCommand:
    command_body_file: None | str = None

    def __init__(self):
        self.command_name: str = "KEYBOARD_TYPE_STRING"
        self.command_title: str = "PROMPT EXPLANATION"
        self.command_body: str = "EXPLANATION ON HOW TO ISSUE THE COMMAND"
        self.command_body_file: None | str = None

    def run(self, input: str):
        print("Ran default command, something is wrong")



class TAssistant:

    def __init__(
            self,
            ollama_model_name: str = "gemma3:12b",
            init_commands: list[TCommand] = [],
            init_system_prompt_features: list[type[TAssistantFeature]] = []
    ):
        self.system_prompt = ""
        self.previous_messages = []
        self.buffered_input = ""
        self.model_name = ollama_model_name

        self.commands: dict[str, TCommand] = dict()
        for command in init_commands:
            self.add_command(command, should_rebuid_system_prompt=False)
        self.rebuild_system_prompt()

        self.feature_context = AssistantFeatureContext()

        for feature_cls in init_system_prompt_features:
            self.feature_context.init_feature(feature_cls)

    def add_command(self, command: TCommand, should_rebuid_system_prompt = True):
        self.commands[command.command_name] = command
        if should_rebuid_system_prompt:
            self.rebuild_system_prompt()

    def rebuild_system_prompt(self):
        self.system_prompt = DEFAULT_LLM_SYSTEM_PROMPT
        self.system_prompt += "\n"
        self.system_prompt += DEFAULT_LLM_COMMAND_HEADER

        for command in self.commands.values():
            command_body = ""
            if command.command_body_file is not None:
                with open("prompts/" + command.command_body_file, "r") as file:
                    command_body = file.read()
            else:
                command_body = command.command_body
            self.system_prompt += f"## {command.command_title}\n{command_body}\n"


    def feed_text(self, input_text: str):
        if input_text == "":
            print("Empty input, ignoring")
            return

        self.feature_context.update_features()

        text = input_text

        if len(self.buffered_input) > 0:
            text = self.buffered_input + " " + text

        context_system_prompts: list[str] = []
        current_feature_system_prompt = self.feature_context.build_context_system_prompt()
        if current_feature_system_prompt:
            context_system_prompts.append(current_feature_system_prompt)

        chat_response: str = send_ollama_completion(
            self.model_name,
            self.system_prompt,
            self.previous_messages,
            context_system_prompts,
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
        for name, _ in matches:
            name = name.strip()
        return matches



def send_ollama_completion(model, system_prompt, previous_messages, context_system_prompts, user_prompt):
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

    for context_system_promp in context_system_prompts:
        if context_system_promp:
             messages.append({
                 "role" : "system",
                 "content" : context_system_promp
                 })

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



def clear_console_row():
    """Clears the current row in the terminal."""
    print("\r\033[K", end="", flush=True)
