from RealtimeSTT import AudioToTextRecorder

from assistant_context import TAssistant
from base_commands import EmacsTCommand, KeyboardInputTCommand

assistant = TAssistant(
    ollama_model_name = "gemma3:12b",
    init_commands=[
        KeyboardInputTCommand(),
        EmacsTCommand()
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
        language="en",
        enable_realtime_transcription=True,

    )

    while True:
        recorder.text(process_text)
