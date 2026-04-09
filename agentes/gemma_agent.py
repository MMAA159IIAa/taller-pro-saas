import os
import sys

# Foundation for Gemma 3 Integration
# He downloaded: google/gemma-3n-e4b

class GemmaAgent:
    def __init__(self, model_path=None):
        self.model_path = model_path or "google/gemma-3n-e4b"
        self.tokenizer = None
        self.model = None
        self.is_ready = False
        
    def cargar_modelo(self):
        """
        Carga el modelo Gemma para inferencia local.
        Requiere torch y transformers.
        """
        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForCausalLM
            
            print(f"Cargando modelo Gemma desde: {self.model_path}")
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                torch_dtype=torch.bfloat16,
                device_map="auto"
            )
            self.is_ready = True
            return True, "Modelo cargado exitosamente."
        except Exception as e:
            return False, f"Error cargando Gemma: {e}"

    def chat(self, prompt, max_tokens=200):
        if not self.is_ready:
            return "El modelo no esta listo."
            
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            outputs = self.model.generate(**inputs, max_new_tokens=max_tokens)
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return response
        except Exception as e:
            return f"Error en chat: {e}"

# Singleton para acceso global
_instance = None
def get_gemma_agent():
    global _instance
    if _instance is None:
        _instance = GemmaAgent()
    return _instance
