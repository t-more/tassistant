from RealtimeSTT import AudioToTextRecorder

from assistant_context import TAssistant
import base_commands
import base_features

import multiprocessing

def assistant_process(conn):
    try:
        run_assistant(conn)
    finally:
        pass



def run_assistant(conn):
    assistant = TAssistant(
        ollama_model_name = "cogito:14b", # "gemma3:12b",
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

    while True:
        message = conn.get()
        clear_console_row()
        print(f"User> {message}")
        assistant.feed_text(message)

def clear_console_row():
    """Clears the current row in the terminal."""
    print("\r\033[K", end="", flush=True)



if __name__ == '__main__':

    print("Wait until it says 'speak now'")
    recorder = AudioToTextRecorder(
        model = "large-v2",
        language="en",
    )

    #parent_conn, child_conn = multiprocessing.Pipe()
    message_queue = multiprocessing.Queue()
    process = multiprocessing.Process(target=assistant_process, args=(message_queue,))
    process.start()



    def feed_text_to_assistant(text: str):
        message_queue.put(text)

    try:
        while True:
            recorder.text(feed_text_to_assistant)
    finally:
        recorder.abort()
        print("Abording recording")
