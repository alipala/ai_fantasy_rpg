# agents/safety_checker.py
from crewai import Agent
from together import Together

class SafetyCheckerAgent:
    def __init__(self, api_key):
        self.client = Together(api_key=api_key)
        self.agent = Agent(
            role='Safety Checker',
            goal='Ensure game content remains appropriate and safe',
            backstory='Expert at content moderation and safety guidelines',
            allow_delegation=False
        )
    
    def check_content(self, content: str) -> bool:
        """Check if content meets safety guidelines."""
        system_prompt = """You are a content safety checker. Evaluate the following content
        for appropriateness in a family-friendly fantasy game. Check for:
        - Excessive violence
        - Inappropriate language
        - Adult content
        - Harmful themes
        
        Respond with either 'SAFE' or 'UNSAFE' followed by a reason if unsafe."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]
        
        response = self.client.chat.completions.create(
            model="meta-llama/Llama-3-70b-chat-hf",
            messages=messages,
            temperature=0
        )
        
        result = response.choices[0].message.content.strip().upper()
        return result.startswith('SAFE')

    def sanitize_content(self, content: str) -> str:
        """Attempt to sanitize unsafe content while preserving game context."""
        if self.check_content(content):
            return content
            
        system_prompt = """Rewrite the following game content to be family-friendly
        while maintaining the fantasy game context and core meaning."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content}
        ]
        
        response = self.client.chat.completions.create(
            model="meta-llama/Llama-3-70b-chat-hf",
            messages=messages
        )
        
        return response.choices[0].message.content