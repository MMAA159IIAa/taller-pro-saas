import os
import json
import urllib.request
from utils.database import get_config
from utils.logger import info, error

class BaseLLM:
    """
    Clase base para agentes que usan Inteligencia Artificial Generativa.
    Arquitectura Híbrida: Soporta LLMs Locales (LM Studio/Gemma), OpenAI y Claude.
    """

    def __init__(self, skill_folder_name, taller_context=None):
        """
        :param skill_folder_name: Nombre de la carpeta dentro de .taller_skills (Ej: '01-Recepcionista')
        :param taller_context: Diccionario opcional para reemplazar variables predefinidas en el prompt.
        """
        self.skill_folder_name = skill_folder_name
        self.system_prompt = self._cargar_skill()
        
        # Inyección de contexto de TallerPro (Precios, Horarios, etc.)
        if taller_context:
            self.system_prompt += f"\n\nContexto del Taller:\n{taller_context}"
            
        # Configuraciones de IA (se leen de la Base de Datos o default)
        self.provider = get_config("llm_provider", "local").lower() # local, openai, claude
        self.local_url = get_config("llm_local_url", "http://localhost:11434/v1/chat/completions") # Default para Ollama
        self.local_model = get_config("llm_local_model", "gemma:2b") # Opcional
        
        self.openai_api_key = get_config("openai_api_key", "")
        self.claude_api_key = get_config("claude_api_key", "")
        
        # Historial de conversación en memoria
        self.historial = []

    def _cargar_skill(self):
        """Lee el archivo SKILL.md correspondiente a este agente."""
        base_dir = os.path.dirname(os.path.dirname(__file__)) # Sube de /agentes a raíz
        skill_path = os.path.join(base_dir, ".taller_skills", self.skill_folder_name, "SKILL.md")
        try:
            with open(skill_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            error("BaseLLM", f"No se encontró el archivo SKILL.md para {self.skill_folder_name}")
            return "Eres un asistente de taller mecánico." # Fallback seguro

    def responder(self, mensaje_usuario):
        """
        Recibe el mensaje del usuario, lo añade al historial, procesa con el LLM,
        guarda la respuesta y la devuelve.
        """
        self.historial.append({"role": "user", "content": mensaje_usuario})
        
        try:
            if self.provider == "openai":
                respuesta = self._usar_openai()
            elif self.provider == "claude":
                respuesta = self._usar_claude()
            else:
                respuesta = self._usar_local()
                
            self.historial.append({"role": "assistant", "content": respuesta})
            return respuesta
            
        except Exception as e:
            error("BaseLLM", f"Error generando respuesta ({self.provider}): {e}")
            return "Disculpa, el sistema se encuentra temporalmente fuera de servicio. ¿Podrías intentar más tarde?"

    def _usar_local(self):
        """Llama a un LLM local corriendo en LM Studio u Ollama usando formato API de OpenAI."""
        info("BaseLLM", f"Enviando solicitud al motor local: {self.local_url}")
        mensajes = [{"role": "system", "content": self.system_prompt}] + self.historial[-10:] # Max 10 de contexto
        
        payload = json.dumps({
            "model": self.local_model,
            "messages": mensajes,
            "temperature": 0.5
        }).encode('utf-8')
        
        req = urllib.request.Request(self.local_url, data=payload, headers={"Content-Type": "application/json"})
        
        with urllib.request.urlopen(req, timeout=600) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['choices'][0]['message']['content']

    def _usar_openai(self):
        """Llama a la API oficial de OpenAI."""
        if not self.openai_api_key:
            raise ValueError("No hay API Key de OpenAI configurada.")
            
        mensajes = [{"role": "system", "content": self.system_prompt}] + self.historial[-10:]
        
        payload = json.dumps({
            "model": "gpt-3.5-turbo", # o gpt-4o-mini
            "messages": mensajes,
            "temperature": 0.5
        }).encode('utf-8')
        
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.openai_api_key}"}
        )
        
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['choices'][0]['message']['content']

    def _usar_claude(self):
        """Llama a la API oficial de Anthropic (Claude)."""
        if not self.claude_api_key:
            raise ValueError("No hay API Key de Claude configurada.")
            
        # Claude maneja el system prompt aparte del arreglo de messages
        payload = json.dumps({
            "model": "claude-3-haiku-20240307", # Modelo rápido y económico
            "max_tokens": 500,
            "temperature": 0.5,
            "system": self.system_prompt,
            "messages": self.historial[-10:]
        }).encode('utf-8')
        
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.claude_api_key,
                "anthropic-version": "2023-06-01"
            }
        )
        
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result['content'][0]['text']

    def borrar_memoria(self):
        """Limpia el contexto de la conversación actual."""
        self.historial = []
