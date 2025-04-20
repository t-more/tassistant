from RealtimeSTT import AudioToTextRecorder

from assistant_context import TAssistant
from base_commands import EmacsTCommand, KeyboardInputTCommand
from base_features import ClipboardFeature, ActiveWindowFeature

assistant = TAssistant(
    ollama_model_name = "gemma3:12b",
    init_commands=[
        KeyboardInputTCommand(),
        EmacsTCommand()
    ],
    init_system_prompt_features=[
        ClipboardFeature(),
        ActiveWindowFeature()
    ]
)

def clear_console_row():
    """Clears the current row in the terminal."""
    print("\r\033[K", end="", flush=True)


def process_text(text:str):
    global assistant
    clear_console_row()
    print(f"User> {text}")
    assistant.feed_text(text)


if __name__ == '__main__':
    print("Wait until it says 'speak now'")
    recorder = AudioToTextRecorder(
        model = "large-v2",
        language="en",
    )

    while True:
        recorder.text(process_text)
