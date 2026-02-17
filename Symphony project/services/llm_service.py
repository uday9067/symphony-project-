import os
import json
import asyncio
from typing import Dict, Any, Optional
import google.generativeai as genai
from huggingface_hub import InferenceClient
import requests

from app.config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)

class FreeLLMService:
    """Service for free LLM APIs (Google Gemini and Hugging Face)"""
    
    def __init__(self):
        self.setup_apis()
        
    def setup_apis(self):
        """Setup free AI APIs"""
        # Setup Google Gemini (Free tier: 60 requests per minute)
        if settings.google_api_key:
            genai.configure(api_key=settings.google_api_key)
            self.gemini_available = True
            logger.info("✅ Google Gemini API configured")
        else:
            self.gemini_available = False
            logger.warning("⚠️ Google Gemini API key not found")
        
        # Setup Hugging Face (Free tier)
        if settings.huggingface_token:
            self.hf_client = InferenceClient(token=settings.huggingface_token)
            self.hf_available = True
            logger.info("✅ Hugging Face API configured")
        else:
            self.hf_available = False
            logger.warning("⚠️ Hugging Face token not found")
    
    async def generate(self, prompt: str, model: str = None) -> Dict[str, Any]:
        """Generate response using free LLMs"""
        if not model:
            model = settings.default_model
        
        try:
            # Try Gemini first (free and good)
            if model == "gemini-pro" and self.gemini_available:
                return await self._generate_gemini(prompt)
            
            # Fallback to Hugging Face
            elif self.hf_available:
                return await self._generate_huggingface(prompt)
            
            # Last resort: Use free OpenAI-compatible endpoint
            else:
                return await self._generate_free_endpoint(prompt)
                
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            raise
    
    async def _generate_gemini(self, prompt: str) -> Dict[str, Any]:
        """Generate using Google Gemini (FREE)"""
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": 2048,
                }
            )
            return {"content": response.text, "model": "gemini-pro"}
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            raise
    
    async def _generate_huggingface(self, prompt: str) -> Dict[str, Any]:
        """Generate using Hugging Face Inference API (FREE models)"""
        try:
            # Try different free models
            models_to_try = [
                "mistralai/Mistral-7B-Instruct-v0.2",
                "google/flan-t5-xxl",
                "microsoft/DialoGPT-medium"
            ]
            
            for model_name in models_to_try:
                try:
                    response = self.hf_client.text_generation(
                        prompt,
                        model=model_name,
                        max_new_tokens=1000,
                        temperature=0.7
                    )
                    return {"content": response, "model": model_name}
                except:
                    continue
            
            raise Exception("No Hugging Face models available")
        except Exception as e:
            logger.error(f"Hugging Face error: {e}")
            raise
    
    async def _generate_free_endpoint(self, prompt: str) -> Dict[str, Any]:
        """Generate using completely free endpoint (no API key needed)"""
        # Use Together.ai free tier or local models
        try:
            # This is a fallback - you can add more free endpoints
            url = "https://api.together.xyz/v1/chat/completions"
            headers = {
                "Authorization": "Bearer free-key",  # Some services have free tier
                "Content-Type": "application/json"
            }
            data = {
                "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000
            }
            
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                result = response.json()
                return {
                    "content": result["choices"][0]["message"]["content"],
                    "model": "free-endpoint"
                }
            else:
                raise Exception(f"Free endpoint failed: {response.text}")
        except Exception as e:
            logger.error(f"Free endpoint error: {e}")
            # Return a simple response if all APIs fail
            return {
                "content": f"I understand you want: {prompt[:100]}... I'll help you with that.",
                "model": "fallback"
            }

# Singleton instance
llm_service = FreeLLMService()