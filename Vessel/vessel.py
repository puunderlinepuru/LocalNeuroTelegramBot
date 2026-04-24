import time
import threading
import numpy as np
import argparse
import os
import socket
from queue import Queue
from rich.console import Console
# Updated imports for modern LangChain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_ollama import OllamaLLM

console = Console()

# Parse command line arguments
parser = argparse.ArgumentParser(description="Local Voice Assistant with ChatterBox TTS")
parser.add_argument("--voice", type=str, help="Path to voice sample for cloning")
parser.add_argument("--exaggeration", type=float, default=0.5, help="Emotion exaggeration (0.0-1.0)")
parser.add_argument("--cfg-weight", type=float, default=0.5, help="CFG weight for pacing (0.0-1.0)")
parser.add_argument("--model", type=str, default=None, help="LLM model name (default: gemma3 for ollama, MiniMax-M2.7 for minimax)")
parser.add_argument("--provider", type=str, default="ollama", choices=["ollama", "minimax"],
                    help="LLM provider: 'ollama' for local models, 'minimax' for MiniMax cloud API (default: ollama)")
parser.add_argument("--api-key", type=str, default=None, help="API key for cloud LLM providers (or set MINIMAX_API_KEY env var)")
parser.add_argument("--temperature", type=float, default=0.7, help="LLM temperature (default: 0.7)")
parser.add_argument("--save-voice", action="store_true", help="Save generated voice samples")
args = parser.parse_args()

# Server function to receive message
def server_receive(host='localhost', port=12345):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        while True:
            conn, addr = s.accept()
            with conn:
                print('Connected by', addr)
                data = b''
                while True:
                    chunk = conn.recv(1024)
                    if not chunk:
                        break
                    data += chunk
                    if b'\r\n\r\n' in data:
                        complete_msg, data = data.split(b'\r\n\r\n', 1)
                        received_text = complete_msg.decode().strip()
                        print("Received:", received_text)
                        if received_text == "exit":
                            response = "Goodbye!"
                            client_send(msg=response)
                            exit(0)
                        with console.status("Generating response...", spinner="dots"):
                            response = get_llm_response(received_text)
                            console.print(f"[cyan]Assistant: {response}")
                            client_send(msg=response)
                        break
    

# Client function to send message
def client_send(host='localhost', port=12346, msg="Hello World\r\n\r\n"):
    formatted_msg = msg + "\r\n\r\n"
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(formatted_msg.encode('utf-8'))
        console.print(f"[green]Sent response to client: {formatted_msg.encode('utf-8')}")
        s.close()

def create_llm(provider: str, model: str | None = None, api_key: str | None = None, temperature: float = 0.7):
    """
    Create an LLM instance based on the selected provider.

    Args:
        provider: LLM provider name ('ollama' or 'minimax').
        model: Model name. Defaults to 'gemma3' for ollama, 'MiniMax-M2.7' for minimax.
        api_key: API key for cloud providers (or set MINIMAX_API_KEY env var).
        temperature: LLM temperature (default: 0.7).

    Returns:
        A LangChain LLM or ChatModel instance.
    """
    if provider == "ollama":
        return OllamaLLM(model=model or "qwen3:8b", base_url="http://localhost:11434")
    else:
        raise ValueError(f"Unknown provider: {provider}. Supported: ollama, minimax")

prompt_template = ChatPromptTemplate.from_messages([
    # ("system", "You are a helpful and friendly AI assistant. You are polite, respectful, and aim to provide concise responses of less than 20 words."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

# Initialize LLM via provider factory
llm = create_llm(
    provider=args.provider,
    model=args.model,
    api_key=args.api_key,
    temperature=args.temperature,
)

# Create the chain with modern LCEL syntax
# StrOutputParser normalizes output across providers (string from Ollama, AIMessage from ChatOpenAI)
chain = prompt_template | llm | StrOutputParser()

# Chat history storage
chat_sessions = {}

def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    """Get or create chat history for a session."""
    if session_id not in chat_sessions:
        chat_sessions[session_id] = InMemoryChatMessageHistory()
    return chat_sessions[session_id]

# Create the runnable with message history
chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)


def get_llm_response(text: str) -> str:
    """
    Generates a response to the given text using the language model.

    Args:
        text (str): The input text to be processed.

    Returns:
        str: The generated response.
    """
    # Use a default session ID for this simple voice assistant
    session_id = "voice_assistant_session"

    # Invoke the chain with history
    response = chain_with_history.invoke(
        {"input": text},
        config={"session_id": session_id}
    )

    # The response is now a string from the LLM, no need to remove "Assistant:" prefix
    # since we're using a proper chat model setup
    return response.strip()


if __name__ == "__main__":
    console.print("[cyan]🤖 Local Assistant")
    console.print("[cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    console.print(f"[blue]CFG weight: {args.cfg_weight}")
    console.print(f"[blue]LLM model:'qwen3:8b'")
    console.print(f"[blue]LLM provider: {args.provider}")
    console.print("[cyan]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    console.print("[cyan]Press Ctrl+C to exit.\n")

    # Create voices directory if saving voices
    if args.save_voice:
        os.makedirs("voices", exist_ok=True)

    response_count = 0
    try:
        server_receive()
    except KeyboardInterrupt:
        console.print("\n[red]Exiting...")

    console.print("[blue]Session ended. Thank you for using ChatterBox Voice Assistant!")
