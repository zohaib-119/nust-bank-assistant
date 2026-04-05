import ollama

print("Bank Assistant Chatbot (type 'exit' to quit)")

while True:
    user = input("You: ")

    if user.lower() == "exit":
        break

    response = ollama.chat(
        model='llama3.2',
        messages=[{"role": "user", "content": user}]
    )

    print("Bot:", response['message']['content'])