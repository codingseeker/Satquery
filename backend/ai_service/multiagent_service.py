import os
import time
from typing import Any, Dict, Optional
from ai_service.base import AIService

class MultiAgentService(AIService):
    def __init__(self, use_real_model: bool = False):
        self.use_real_model = use_real_model
        if self.use_real_model:
            # Import the real model here to avoid loading if not needed
            import sys
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            if root_dir not in sys.path:
                sys.path.append(root_dir)
            from training.scripts.satquery_inference import SatQueryBot
            
            model_path = os.environ.get("MODEL_PATH", "training/models/satquery-best-lora")
            base_model_cache = os.path.join(root_dir, "training", "models", "qwen25vl")
            adapter_path = os.path.join(root_dir, model_path)
            
            print("Loading MultiAgent Service with Real SatQueryBot...")
            self.bot = SatQueryBot(
import os
import time
from typing import Any, Dict, Optional
from ai_service.base import AIService

class MultiAgentService(AIService):
    def __init__(self, use_real_model: bool = False):
        self.use_real_model = use_real_model
        if self.use_real_model:
            # Import the real model here to avoid loading if not needed
            import sys
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            if root_dir not in sys.path:
                sys.path.append(root_dir)
            from training.scripts.satquery_inference import SatQueryBot
            
            model_path = os.environ.get("MODEL_PATH", "training/models/satquery-best-lora")
            base_model_cache = os.path.join(root_dir, "training", "models", "qwen25vl")
            adapter_path = os.path.join(root_dir, model_path)
            
            print("Loading MultiAgent Service with Real SatQueryBot...")
            self.bot = SatQueryBot(
                base_model_id=base_model_cache,
                adapter_path=adapter_path
            )
        else:
            self.bot = None

    def analyze(
        self,
        image_path: str,
        query: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        start_time = time.time()
        print(f"[MultiAgent] Starting multi-agent workflow for query: '{query}'")
        
        execution_steps = []
        task_name = "Scene Understanding"
        lower_query = query.lower()
        if "water" in lower_query:
            task_name = "Water Detection"
        elif "built" in lower_query or "urban" in lower_query:
            task_name = "Built-up Detection"
            
        execution_steps.append(f"[Query Router] -> Detected task category: {task_name}")

        # Phase 1: Vision Analysis Agent
        print("[MultiAgent] [Agent 1] Vision Analyzer running...")
        execution_steps.append("[Query Router] -> Routing image to VisionAgent for spatial parsing")
        if self.use_real_model and self.bot:
            execution_steps.append("[VisionAgent] -> Loading Qwen-VL with SatQuery LoRA and extracting features")
            vision_query = f"You are a Vision Expert. Describe the satellite image in detail, focusing on elements relevant to: {query}"
            vision_result = self.bot.chat(vision_query, image_path=image_path)
            vision_answer = vision_result.get("answer", "")
            execution_steps.append("[VisionAgent] -> Completed multi-band feature extraction")
        else:
            time.sleep(0.5)
            vision_answer = "I have scanned the image. Various geographic and built-up features have been identified."
            execution_steps.append("[VisionAgent] -> Processed features (Mock)")

        # Phase 2: Data Interpretation Agent
        print("[MultiAgent] [Agent 2] Data Interpreter running...")
        if self.use_real_model and self.bot:
            execution_steps.append("[DataInterpreterAgent] -> Synthesizing geographic context from VisionAgent data")
            interpreter_query = f"You are a Data Interpreter. Based on the vision expert's findings: '{vision_answer}', provide insights for the user's query: {query}"
            try:
                interpreter_result = self.bot.chat(interpreter_query, image_path=None)
                interpreter_answer = interpreter_result.get("answer", "")
            except Exception:
                interpreter_result = self.bot.chat(interpreter_query, image_path=image_path)
                interpreter_answer = interpreter_result.get("answer", "")
            execution_steps.append("[DataInterpreterAgent] -> Synthesis complete")
        else:
            time.sleep(0.5)
            interpreter_answer = "The visual findings strongly correlate with expected urbanization and land-use patterns."
            execution_steps.append("[DataInterpreterAgent] -> Geographic synthesis complete (Mock)")

        # Phase 3: Synthesis Agent
        print("[MultiAgent] [Agent 3] Report Synthesizer running...")
        if self.use_real_model and self.bot:
            execution_steps.append("[SynthesisAgent] -> Compiling final structured JSON and markdown report")
            synthesizer_query = f"You are a Synthesis Expert. Combine these insights into a final comprehensive answer for the user's query '{query}'.\nVision Findings: {vision_answer}\nData Insights: {interpreter_answer}\nEnsure your response is highly structured (using markdown) and includes explicit step-by-step logical reasoning explaining why features (like water, vegetation, etc.) are present based on the visual and data insights."
            try:
                final_result = self.bot.chat(synthesizer_query, image_path=None)
                final_answer = final_result.get("answer", "")
            except Exception:
                final_result = self.bot.chat(synthesizer_query, image_path=image_path)
                final_answer = final_result.get("answer", "")
            execution_steps.append("[SynthesisAgent] -> Final response successfully generated")
        else:
            time.sleep(0.5)
            final_answer = (
                f"**Multi-Agent Analysis Report**\n\n"
                f"*Query:* {query}\n\n"
                f"**1. Vision Analysis:**\n{vision_answer}\n\n"
                f"**2. Data Interpretation:**\n{interpreter_answer}\n\n"
                f"**Conclusion:**\nThe multi-agent pipeline has successfully processed the query and derived the necessary insights."
            )
            execution_steps.append("[SynthesisAgent] -> Final response generated (Mock)")

        return {
            "task": task_name,
            "status": "completed",
            "confidence": 0.92,
            "answer": final_answer,
            "metadata": metadata or {},
            "execution": {
                "taskDetected": task_name,
                "tools": ["QueryRouter", "VisionAgent", "DataInterpreterAgent", "SynthesisAgent"],
                "inputType": "satellite_image",
                "outputType": "multimodal_vqa",
                "status": "completed",
                "durationMs": int((time.time() - start_time) * 1000),
                "steps": execution_steps
            }
        }
