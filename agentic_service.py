class ServiceResult:
    """Simple result object to mimic CrewAI result structure"""
    def __init__(self, original_text: str, reversed_text: str):
        self.original_text = original_text
        self.reversed_text = reversed_text
        self.raw = reversed_text
        self.json_dict = {
            "original_text": original_text,
            "reversed_text": reversed_text,
            "task": "reverse_echo"
        }

class AgenticService:
    """Simple service that reverses input text"""
    
    def __init__(self, logger=None):
        self.logger = logger
    
    async def execute_task(self, input_data: dict) -> ServiceResult:
        """
        Execute reverse echo task
        
        Args:
            input_data: Dictionary containing 'input_string' key
            
        Returns:
            ServiceResult with reversed text
        """
        text = input_data.get("input_string", "")
        
        if self.logger:
            self.logger.info(f"Processing reverse echo for text: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        
        # simple reverse operation
        reversed_text = text[::-1]
        
        if self.logger:
            self.logger.info(f"Reverse echo completed: '{reversed_text[:50]}{'...' if len(reversed_text) > 50 else ''}'")
        
        return ServiceResult(text, reversed_text)

def get_agentic_service(logger=None):
    """
    Factory function to get the appropriate service for this branch.
    This enables easy switching between different implementations across branches.
    
    CrewAI branch: CrewAI-based agent implementation
    """
    return CrewAIService(logger)


# ─────────────────────────────────────────────────────────────────────────────
# CrewAI Integration Implementation 
# ─────────────────────────────────────────────────────────────────────────────

import os
from crew import MyCrew  # Crew definition in crew.py - customize there!

class CrewAIService:
    """
    CrewAI service using simple direct instantiation
    Requires OPENAI_API_KEY environment variable
    """
    
    def __init__(self, logger=None):
        self.logger = logger
        
        # check for OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            error_msg = "OPENAI_API_KEY environment variable is required for CrewAI functionality"
            if self.logger:
                self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        if self.logger:
            self.logger.info("CrewAI service initialized")
    
    async def execute_task(self, input_data: dict) -> ServiceResult:
        """
        Execute CrewAI summarization using stock pattern
        
        Args:
            input_data: Dictionary containing 'input_string' key
            
        Returns:
            ServiceResult with CrewAI summarization
        """
        text = input_data.get("input_string", "")
        
        if self.logger:
            self.logger.info(f"Processing CrewAI summarization for: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        
        if not text.strip():
            summary = "No text provided for summarization."
        else:
            try:
                # create crew instance from crew.py (simple pattern)
                crew_instance = MyCrew(logger=self.logger)
                
                if self.logger:
                    self.logger.info("Executing CrewAI crew...")
                
                # execute the crew with inputs (no manual configuration)
                result = crew_instance.crew.kickoff(inputs={'text': text})
                summary = str(result).strip()
                
                if self.logger:
                    self.logger.info("CrewAI summarization completed successfully")
                    
            except Exception as e:
                error_msg = f"CrewAI execution failed: {str(e)}"
                if self.logger:
                    self.logger.error(error_msg)
                summary = f"Error during summarization: {str(e)}"
        
        # create result object
        result_obj = ServiceResult(text, summary)
        result_obj.json_dict = {
            "original_text": text,
            "summary": summary,
            "task": "crewai_summarization", 
            "word_count": len(text.split()) if text else 0,
            "char_count": len(text),
            "agent_type": "CrewAI"
        }
        
        return result_obj


# ─────────────────────────────────────────────────────────────────────────────
# Command Line Interface for Testing
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import asyncio
    import json
    
    parser = argparse.ArgumentParser(description="Test CrewAI service directly")
    parser.add_argument("--input", required=True, help="Text to process")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show verbose output")
    
    args = parser.parse_args()
    
    async def main():
        if args.verbose:
            import logging
            logging.basicConfig(level=logging.INFO)
            logger = logging.getLogger("crewai_test")
        else:
            logger = None
        
        service = get_agentic_service(logger=logger)
        result = await service.execute_task({"input_string": args.input})
        
        if args.verbose:
            print("=== CrewAI Service Test Results ===")
            print(f"Service Type: {service.__class__.__name__}")
            print(f"Original Text: {result.original_text}")
            print(f"Processed Result: {result.raw}")
            print(f"Full JSON: {json.dumps(result.json_dict, indent=2)}")
        else:
            print(result.raw)
    
    asyncio.run(main()) 