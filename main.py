"""
Step 9 — Terminal Interface (CLI)
Main entry point for the NUST Bank Customer Support Assistant.

Usage:
    python main.py
    python main.py --rebuild   (force rebuild the index)
"""

import sys
import os
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.rag_pipeline import RAGPipeline
from src.config import CONFIG


def print_banner():
    """Print the application banner."""
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " NUST Bank — AI Customer Support Assistant ".center(58) + "║")
    print("║" + " Powered by RAG + LLaMA 3.2 ".center(58) + "║")
    print("╚" + "═" * 58 + "╝")
    print()


def print_help():
    """Print help information."""
    print("\nCommands:")
    print("  Type your question and press Enter")
    print("  'exit' or 'quit'  — Exit the chatbot")
    print("  'help'            — Show this help message")
    print("  'sources'         — Toggle source display on/off")
    print()


def main():
    """Main function — CLI chat loop."""
    parser = argparse.ArgumentParser(description="NUST Bank RAG Assistant")
    parser.add_argument("--rebuild", action="store_true", help="Force rebuild the vector index")
    parser.add_argument("--ui", action="store_true", help="Launch Gradio web UI")
    args = parser.parse_args()

    if args.ui:
        # Launch UI
        from ui.app import demo  # type: ignore

        demo.launch(server_name=CONFIG.ui_host, server_port=CONFIG.ui_port)
        return

    print_banner()

    # Configuration — data_dir points to project root where .xlsx and .json files live
    project_root = os.path.dirname(os.path.abspath(__file__))
    data_dir = project_root
    index_dir = os.path.join(project_root, "index")

    # Check for --rebuild flag
    rebuild = args.rebuild

    # Initialize the RAG pipeline
    pipeline = RAGPipeline(data_dir=data_dir, index_dir=index_dir, top_k=CONFIG.top_k)

    if rebuild:
        # Remove existing index to force rebuild
        import shutil
        if os.path.exists(index_dir):
            shutil.rmtree(index_dir)
            print("Removed existing index. Rebuilding...\n")

    pipeline.initialize()

    # Chat loop
    show_sources = False
    print("\n\nBank Assistant Ready!")
    print("Ask a question (type 'exit' to quit, 'help' for commands):\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye! Thank you for using NUST Bank Assistant.")
            break

        # Handle empty input
        if not user_input:
            continue

        # Handle commands
        if user_input.lower() in ("exit", "quit"):
            print("\nGoodbye! Thank you for using NUST Bank Assistant.")
            break

        if user_input.lower() == "help":
            print_help()
            continue

        if user_input.lower() == "sources":
            show_sources = not show_sources
            status = "ON" if show_sources else "OFF"
            print(f"  Source display: {status}\n")
            continue

        # Process the query through the RAG pipeline
        print("\n  Thinking...\n")

        try:
            if show_sources:
                result = pipeline.query_with_sources(user_input)
                print(f"Bot: {result['answer']}")
                print(f"\nSources: {', '.join(result['sources'])}")
            else:
                answer = pipeline.query(user_input)
                print(f"Bot: {answer}")
        except Exception as e:
            print(f"  Error: {str(e)}")
            print("  Please make sure Ollama is running with the llama3.2 model.")

        print()


if __name__ == "__main__":
    main()
