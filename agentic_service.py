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

class CrewAIService:
    """
    CrewAI-based service implementation (hello-world demonstration)
    
    Note: This is a minimal implementation showing CrewAI integration patterns.
    For full CrewAI functionality, uncomment the imports and implement 
    actual Agent, Task, and Crew objects.
    """
    
    def __init__(self, logger=None):
        self.logger = logger
        # for demo purposes, we'll simulate CrewAI without full dependencies
        # uncomment below when you have openai api key configured:
        # from crewai import Agent, Task, Crew
        # self.crew = self._create_crew()
    
    def _create_crew(self):
        """
        Create a simple CrewAI crew for text processing
        
        Uncomment this method when you have CrewAI properly configured:
        """
        # from crewai import Agent, Task, Crew
        # 
        # text_processor = Agent(
        #     role='Text Processor',
        #     goal='Process and analyze text input from users',
        #     backstory='''You are a helpful text processing assistant. 
        #     Your job is to take text input and provide useful analysis.''',
        #     verbose=True,
        #     allow_delegation=False
        # )
        # 
        # return Crew(
        #     agents=[text_processor],
        #     tasks=[],  # tasks will be created dynamically
        #     verbose=True
        # )
        pass
    
    async def execute_task(self, input_data: dict) -> ServiceResult:
        """
        Execute CrewAI task (demo implementation)
        
        Args:
            input_data: Dictionary containing 'input_string' key
            
        Returns:
            ServiceResult with CrewAI-style processing result
        """
        text = input_data.get("input_string", "")
        
        if self.logger:
            self.logger.info(f"Processing with CrewAI-style analysis for text: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        
        # demo implementation: simulate CrewAI analysis
        # in real implementation, this would use actual CrewAI agents
        word_themes = ', '.join(text.split()[:3]) if text.split() else 'none'
        analyzed_text = f"CrewAI Analysis: Text contains {len(text)} characters and {len(text.split())} words. Key themes: {word_themes}..."
        
        if self.logger:
            self.logger.info(f"CrewAI analysis completed: '{analyzed_text[:50]}{'...' if len(analyzed_text) > 50 else ''}'")
        
        # create result with CrewAI-specific metadata
        result = ServiceResult(text, analyzed_text)
        result.json_dict = {
            "original_text": text,
            "analyzed_text": analyzed_text,
            "task": "crewai_analysis",
            "word_count": len(text.split()),
            "char_count": len(text)
        }
        return result 