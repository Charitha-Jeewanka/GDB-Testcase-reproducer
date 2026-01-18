import os
from groq import Groq
from utils.config_loader import get_groq_api_key

class BaseAgent:
    def __init__(self, model_name="llama-3.3-70b-versatile", temperature=0.1):
        self.client = Groq(api_key=get_groq_api_key())
        self.model_name = model_name
        self.temperature = temperature
        self.messages = []

    def set_system_prompt(self, prompt):
        self.messages = [{"role": "system", "content": prompt}]

    def chat(self, user_input):
        self.messages.append({"role": "user", "content": user_input})
        
        completion = self.client.chat.completions.create(
            messages=self.messages,
            model=self.model_name,
            temperature=self.temperature,
            stop=None # Can add stops if needed
        )
        
        response = completion.choices[0].message.content
        self.messages.append({"role": "assistant", "content": response})
        return response
