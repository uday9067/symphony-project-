import json
from typing import Dict, List, Any

from services.llm_service import llm_service
from utils.prompts import PHASE1_PROMPT
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ProjectManager:
    """Phase 1: Analyzes project and breaks into tasks"""
    
    def __init__(self):
        self.agent_type = "project_manager"
    
    async def analyze_project(self, user_prompt: str) -> Dict[str, Any]:
        """Analyze project and create task breakdown"""
        logger.info(f"📋 Phase 1: Analyzing project: {user_prompt[:100]}...")
        
        try:
            # Generate project analysis
            response = await llm_service.generate(
                PHASE1_PROMPT.format(user_prompt=user_prompt)
            )
            
            # Parse JSON response
            result = json.loads(response["content"])
            
            # Validate structure
            if "tasks" not in result:
                raise ValueError("Invalid response from project manager")
            
            logger.info(f"✓ Project analyzed: {len(result['tasks'])} tasks created")
            return {
                "phase": 1,
                "status": "completed",
                "result": result,
                "model_used": response["model"]
            }
            
        except json.JSONDecodeError as e:
            # Try to fix JSON if malformed
            logger.warning(f"JSON decode error, trying to fix: {e}")
            return await self._fix_json_response(response["content"], user_prompt)
        except Exception as e:
            logger.error(f"Project analysis error: {e}")
            raise
    
    async def _fix_json_response(self, raw_response: str, user_prompt: str) -> Dict[str, Any]:
        """Fix malformed JSON responses"""
        try:
            # Try to extract JSON from response
            start_idx = raw_response.find('{')
            end_idx = raw_response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = raw_response[start_idx:end_idx]
                result = json.loads(json_str)
                return {
                    "phase": 1,
                    "status": "completed",
                    "result": result,
                    "model_used": "gemini-pro",
                    "note": "JSON was fixed"
                }
            else:
                # Create a simple task structure as fallback
                return await self._create_fallback_tasks(user_prompt)
        except:
            return await self._create_fallback_tasks(user_prompt)
    
    async def _create_fallback_tasks(self, user_prompt: str) -> Dict[str, Any]:
        """Create fallback task structure"""
        return {
            "phase": 1,
            "status": "completed",
            "result": {
                "project_name": f"Project from: {user_prompt[:50]}",
                "description": user_prompt,
                "tasks": [
                    {
                        "id": 1,
                        "title": "Create main implementation",
                        "description": user_prompt,
                        "agent_type": "coder",
                        "priority": "high",
                        "dependencies": [],
                        "expected_output": "Main code implementation",
                        "estimated_time": "1 hour"
                    },
                    {
                        "id": 2,
                        "title": "Create documentation",
                        "description": "Document the project",
                        "agent_type": "writer",
                        "priority": "medium",
                        "dependencies": [1],
                        "expected_output": "Project documentation",
                        "estimated_time": "30 minutes"
                    }
                ],
                "tech_stack": ["Python"],
                "success_criteria": ["Working implementation"],
                "constraints": []
            },
            "model_used": "fallback",
            "note": "Used fallback task structure"
        }