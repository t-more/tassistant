from RealtimeSTT import AudioToTextRecorder

from assistant_context import TAssistant
import base_commands
import base_features

assistant = TAssistant(
    ollama_model_name = "gemma3:12b",
    init_commands=[
        base_commands.KeyboardInputTCommand(),
        base_commands.EmacsTCommand()
    ],
    init_system_prompt_features=[
        base_features.ClipboardFeature,
        base_features.ActiveWindowFeature,
        base_features.EmacsDetailsFeature
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
