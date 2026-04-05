"""
Step 7 — LLM Inference Module (Ollama)
Connects to Ollama and generates responses using llama3.2.
"""

import ollama
from src.config import CONFIG

# Default model
DEFAULT_MODEL = CONFIG.ollama_model

# System prompt for the bank assistant
SYSTEM_PROMPT = """You are a helpful and polite customer support assistant for NUST Bank.

Your responsibilities:
- Respond naturally to greetings (hi, hello, thank you, etc.) in a friendly, conversational manner
- When greeted, introduce yourself simply as "NUST Bank Assistant" and offer to help
- Do NOT make up a personal name for yourself
- Answer banking questions using ONLY the provided context
- If asked about personal matters or topics completely unrelated to banking, politely redirect: "I specialize in helping with NUST Bank products and services. How can I assist you with your banking needs today?"
- If banking information is not in the context, say: "I don't have that specific information. Please contact NUST Bank at +92 (51) 111 000 494 or email support@NUSTbank.com.pk"
- Be professional, clear, conversational, and helpful
- Remember the customer's name if they introduce themselves, but don't make up your own name

Keep answers concise and natural. Don't make up information."""


def build_prompt(context: str, question: str) -> str:
    """Build the user prompt with context and question.
    
    Args:
        context:  Retrieved context chunks as a formatted string
        question: The user's question
    
    Returns:
        Formatted prompt string
    """
    # Check if it's a simple greeting/small talk
    question_lower = question.lower().strip()
    greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 
                 'thanks', 'thank you', 'bye', 'goodbye']
    
    is_greeting = any(greeting in question_lower for greeting in greetings) and len(question.split()) < 10
    
    if is_greeting:
        # For greetings, provide minimal context to keep response natural
        prompt = f"""User message: {question}

Respond naturally to this greeting and offer to help with NUST Bank services."""
    else:
        # For banking queries, provide full context
        prompt = f"""Context from NUST Bank Knowledge Base:
{context}

Customer Question: {question}

Provide a helpful answer based on the context above."""
    
    return prompt


def generate_response(question: str, context: str, model: str = DEFAULT_MODEL) -> str:
    """Generate an answer using the LLM via Ollama.
    
    Args:
        question: User's question
        context:  Retrieved context string
        model:    Ollama model name
    
    Returns:
        Generated answer string
    """
    user_prompt = build_prompt(context, question)

    try:
        response = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response["message"]["content"]

    except Exception as e:
        return f"Error generating response: {str(e)}\nPlease ensure Ollama is running and the model '{model}' is available."


if __name__ == "__main__":
    # Quick test
    test_context = "NUST Bank offers a Little Champs Account for minors below 18 years."
    test_question = "Do you have accounts for children?"
    answer = generate_response(test_question, test_context)
    print(f"Q: {test_question}")
    print(f"A: {answer}")
