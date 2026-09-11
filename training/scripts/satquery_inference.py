import torch
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration, BitsAndBytesConfig
from peft import PeftModel
from qwen_vl_utils import process_vision_info
import json

class SatQueryBot:
    def __init__(self, base_model_id="Qwen/Qwen2.5-VL-3B-Instruct", adapter_path="training/models/satquery-best-lora"):
        print("Loading Processor...")
        self.processor = AutoProcessor.from_pretrained(base_model_id)
        
        print("Loading Base Model...")
        try:
            # Attempt to load with 4-bit quantization (GPU preferred)
            quant_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.float16
            )
            base_model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                base_model_id,
                quantization_config=quant_config,
                device_map="auto"
            )
            print("Successfully loaded in 4-bit precision.")
        except Exception as e:
            print(f"4-bit quantization failed (e.g. no GPU). Falling back to CPU/standard precision: {e}")
            # Fallback to standard loading with CPU offloading or default device
            base_model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                base_model_id,
                torch_dtype=torch.float32 if not torch.cuda.is_available() else torch.float16,
                device_map="auto"
            )
            print("Successfully loaded with standard precision fallback.")
        
        print(f"Applying SatQuery LoRA from {adapter_path}...")
        self.model = PeftModel.from_pretrained(base_model, adapter_path)
        self.model.eval()
        
        # Keep track of conversation history for multi-turn
        self.history = []
        print("SatQuery Bot Ready!")

    def chat(self, user_text, image_path=None):
        """
        Handles both multimodal (image+text) and general (text-only) queries.
        Maintains conversation history for follow-ups.
        """
        # 1. Build the new message
        content = []
        if image_path:
            content.append({"type": "image", "image": image_path})
        content.append({"type": "text", "text": user_text})
        
        new_message = {"role": "user", "content": content}
        self.history.append(new_message)

        # 2. Add System Prompt for structure
        system_prompt = {
            "role": "system",
            "content": "You are SatQuery AI, an expert ISRO remote sensing assistant. Provide clear, highly structured answers using clean plain text. Do NOT use markdown symbols like asterisks (**), bolding, or hashes. Use standard line breaks and numbering to structure your response. If you identify specific spatial features or regions, you MUST output bounding boxes using the exact syntax: <box>(xmin, ymin), (xmax, ymax)</box>. Always include step-by-step logical reasoning for your conclusions."
        }
        
        messages = [system_prompt] + self.history

        # 3. Process inputs
        text = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        image_inputs, video_inputs, video_kwargs = process_vision_info(messages, return_video_kwargs=True)
        
        # Filter empty video kwargs to prevent crashes
        safe_video_kwargs = {k: v for k, v in (video_kwargs or {}).items() if v is not None and v != []}

        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
            **safe_video_kwargs
        ).to(self.model.device)

        # 4. Generate Answer
        with torch.no_grad():
            generated_ids = self.model.generate(**inputs, max_new_tokens=256)
            
        # Extract only the newly generated tokens
        generated_ids_trimmed = [
            out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        
        response_text = self.processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0]

        # 5. Add assistant response to history
        self.history.append({"role": "assistant", "content": [{"type": "text", "text": response_text}]})

        # 6. Return Structured Output (Enhancement 4)
        result = {
            "query": user_text,
            "has_image": bool(image_path),
            "answer": response_text.strip(),
            "status": "success"
        }
        return result

    def clear_history(self):
        self.history = []
        print("Conversation history cleared.")


if __name__ == "__main__":
    # WARNING: Do not run this while training is active on a 6GB GPU (will cause OutOfMemory error).
    # Run this only AFTER your training script completes.
    
    print("\n--- SatQuery ISRO Bot Interactive Mode ---")
    # bot = SatQueryBot()
    # 
    # Example 1: General ISRO Knowledge (Text only)
    # print(bot.chat("What does ISRO do?"))
    #
    # Example 2: Satellite Image Query
    # print(bot.chat("Is there a forest in this image?", image_path="path/to/image.png"))
    #
    # Example 3: Multi-turn Follow-up
    # print(bot.chat("How much area does it cover?"))
    print("Script created! Uncomment the lines above to run after training completes.")
