"""
LLM Orchestration Layer for Ossi Voice AI.
Direct httpx implementation for Python 3.14 compatibility.
"""

import time
import json
import httpx
import ssl
from pathlib import Path
from typing import Optional, List, Dict, Any

from src.utils.config import get_settings
from src.utils.logger import setup_logger
from src.core.models import (
    IntentClassification,
    ConversationContext,
    LLMResponse,
    IntentType
)

settings = get_settings()
logger = setup_logger(__name__)


class LLMOrchestrator:
    """
    Manages all Claude API interactions using httpx directly.
    Bypasses anthropic SDK for Python 3.14 compatibility.
    """
    
    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY
        self.model = settings.CLAUDE_MODEL
        self.max_tokens = settings.CLAUDE_MAX_TOKENS
        self.base_url = "https://api.anthropic.com/v1"
        self.total_tokens_used = 0
        self.total_api_calls = 0
        
        # Create httpx client with SSL verification disabled for Python 3.14
        # TODO: Fix SSL certificates properly before production!
        logger.warning("SSL verification disabled - TESTING ONLY!")
        self.client = httpx.Client(
            timeout=30.0,
            verify=False  # Temporary workaround for Python 3.14 SSL issue
        )
        
        # Load system prompts
        self.prompts = self._load_prompts()
        
        logger.info("LLM Orchestrator initialized (httpx mode, SSL disabled)", extra={
            "model": self.model,
            "max_tokens": self.max_tokens
        })
    
    def _load_prompts(self) -> Dict[str, str]:
        """Load system prompts from config files."""
        prompts = {}
        prompts_dir = Path("config/prompts")
        
        if not prompts_dir.exists():
            logger.warning("Prompts directory not found, using defaults")
            return self._get_default_prompts()
        
        for prompt_file in prompts_dir.glob("*.txt"):
            prompt_name = prompt_file.stem
            with open(prompt_file, 'r') as f:
                prompts[prompt_name] = f.read().strip()
            logger.debug(f"Loaded prompt: {prompt_name}")
        
        return prompts
    
    def _get_default_prompts(self) -> Dict[str, str]:
        """Fallback prompts if files don't exist."""
        return {
            "intent_classification": "You are an intent classifier. Classify the user's intent as receptionist, triage, or escalation.",
            "receptionist_system": "You are a helpful healthcare receptionist.",
            "triage_system": "You are a triage nurse assessing symptoms."
        }
    
    def classify_intent(
        self,
        user_message: str,
        context: Optional[ConversationContext] = None
    ) -> IntentClassification:
        """
        Classify user intent using Claude with structured output.
        """
        start_time = time.time()
        
        # Build the prompt
        system_prompt = self.prompts.get("intent_classification", "")
        
        # Add context if available
        context_str = ""
        if context and context.conversation_turns:
            recent_turns = context.get_recent_turns(3)
            context_str = "\n\nRecent conversation:\n"
            for turn in recent_turns:
                context_str += f"{turn.role}: {turn.content}\n"
        
        full_prompt = f"{system_prompt}\n{context_str}\nUser message: {user_message}"
        
        logger.info("Classifying intent", extra={
            "user_message": user_message[:100],
            "has_context": context is not None
        })
        
        try:
            # Call Claude with retry logic
            response = self._call_claude_with_retry(
                messages=[{"role": "user", "content": full_prompt}],
                max_retries=3
            )
            
            # Parse response as JSON
            response_text = response['content'][0]['text']
            
            # Try to extract JSON if it's wrapped in markdown
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            result_dict = json.loads(response_text)
            
            # Validate with Pydantic
            intent = IntentClassification(**result_dict)
            
            # Track metrics
            latency_ms = (time.time() - start_time) * 1000
            tokens_used = response['usage']['input_tokens'] + response['usage']['output_tokens']
            self.total_tokens_used += tokens_used
            self.total_api_calls += 1
            
            logger.info("Intent classified", extra={
                "intent": intent.intent,
                "confidence": intent.confidence,
                "latency_ms": round(latency_ms, 2),
                "tokens_used": tokens_used
            })
            
            return intent
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            return IntentClassification(
                intent=IntentType.ESCALATION,
                confidence=0.0,
                reasoning="Failed to parse AI response",
                next_action="Escalate to human",
                detected_keywords=[]
            )
        
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return IntentClassification(
                intent=IntentType.ESCALATION,
                confidence=0.0,
                reasoning=f"Error: {str(e)}",
                next_action="Escalate to human",
                detected_keywords=[]
            )
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        """General-purpose chat completion."""
        start_time = time.time()
        
        try:
            response = self._call_claude_with_retry(
                messages=messages,
                system=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens or self.max_tokens,
                max_retries=3
            )
            
            latency_ms = (time.time() - start_time) * 1000
            tokens_used = response['usage']['input_tokens'] + response['usage']['output_tokens']
            
            self.total_tokens_used += tokens_used
            self.total_api_calls += 1
            
            logger.info("Chat completion successful", extra={
                "latency_ms": round(latency_ms, 2),
                "tokens_used": tokens_used,
                "model": self.model
            })
            
            return LLMResponse(
                content=response['content'][0]['text'],
                tokens_used=tokens_used,
                model=self.model,
                latency_ms=latency_ms,
                metadata={
                    "input_tokens": response['usage']['input_tokens'],
                    "output_tokens": response['usage']['output_tokens']
                }
            )
            
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            raise
    
    def _call_claude_with_retry(
        self,
        messages: List[Dict[str, str]],
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Call Claude API directly using httpx with retry logic.
        """
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature
        }
        
        if system:
            payload["system"] = system
        
        for attempt in range(max_retries):
            try:
                response = self.client.post(
                    f"{self.base_url}/messages",
                    headers=headers,
                    json=payload
                )
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code in [400, 401, 403]:
                    # Don't retry client errors
                    logger.error(f"HTTP error (no retry): {e}")
                    raise
                
                if attempt == max_retries - 1:
                    logger.error(f"HTTP error after retries: {e}")
                    raise
                
                wait_time = 2 ** attempt
                logger.warning(f"HTTP error, retrying in {wait_time}s", extra={
                    "status_code": e.response.status_code,
                    "attempt": attempt + 1
                })
                time.sleep(wait_time)
                
            except httpx.RequestError as e:
                if attempt == max_retries - 1:
                    logger.error(f"Request error after {max_retries} retries: {e}")
                    raise
                
                wait_time = 2 ** attempt
                logger.warning(f"Request error, retrying in {wait_time}s", extra={
                    "error": str(e),
                    "attempt": attempt + 1
                })
                time.sleep(wait_time)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "total_tokens_used": self.total_tokens_used,
            "total_api_calls": self.total_api_calls,
            "model": self.model,
            "estimated_cost_usd": self._estimate_cost()
        }
    
    def _estimate_cost(self) -> float:
        """Estimate cost based on token usage."""
        return (self.total_tokens_used / 1_000_000) * 9.0


# Test function
if __name__ == "__main__":
    """Test the LLM Orchestrator."""
    import warnings
    warnings.filterwarnings('ignore', message='Unverified HTTPS request')
    
    print("\n" + "=" * 60)
    print("Testing Ossi LLM Orchestrator (httpx mode)")
    print("⚠️  SSL verification disabled - TESTING ONLY!")
    print("=" * 60 + "\n")
    
    orchestrator = LLMOrchestrator()
    
    # Test cases
    test_cases = [
        "I need to schedule an appointment with Dr. Smith",
        "I've had a headache for 3 days",
        "I'm having chest pain",
        "What are your clinic hours?",
        "I need to speak with someone right now"
    ]
    
    for i, message in enumerate(test_cases, 1):
        print(f"\nTest {i}: '{message}'")
        print("-" * 60)
        
        try:
            intent = orchestrator.classify_intent(message)
            print(f"Intent: {intent.intent}")
            print(f"Confidence: {intent.confidence:.2f}")
            print(f"Reasoning: {intent.reasoning}")
            print(f"Next Action: {intent.next_action}")
            if intent.detected_keywords:
                print(f"Keywords: {', '.join(intent.detected_keywords)}")
        
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Show usage stats
    print("\n" + "=" * 60)
    print("Usage Statistics")
    print("=" * 60)
    stats = orchestrator.get_usage_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print("\n✅ LLM Orchestrator test complete!")
    print("⚠️  Remember: SSL verification is disabled - fix before production!")
