import os
import openai
import requests
import json
import base64
from typing import Dict, List, Optional, Union
from datetime import datetime
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OnlineX_AI")

class OpenAIClient:
    """
    Client OpenAI avancé pour Online X Chat AI
    Supporte le chat, les images, et bientôt l'audio/vidéo
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise le client OpenAI avec gestion d'erreur robuste
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        
        if not self.api_key:
            raise ValueError("❌ OPENAI_API_KEY non trouvée. Vérifie ton .env")
        
        # Configuration OpenAI
        openai.api_key = self.api_key
        
        # Modèles par défaut
        self.chat_model = "gpt-4-1106-preview"  # GPT-4 Turbo
        self.image_model = "dall-e-3"
        self.vision_model = "gpt-4-vision-preview"
        
        # Configuration des paramètres
        self.default_max_tokens = 2000
        self.default_temperature = 0.7
        
        # Historique des conversations pour le contexte
        self.conversation_history: List[Dict] = []
        self.max_history_length = 10
        
        # Statistiques d'usage
        self.usage_stats = {
            "total_requests": 0,
            "chat_requests": 0,
            "image_requests": 0,
            "last_request": None
        }
        
        logger.info("✅ Client OpenAI initialisé avec succès")
    
    def _make_request(self, func, *args, **kwargs):
        """
        Wrapper pour toutes les requêtes OpenAI avec gestion d'erreur
        """
        try:
            self.usage_stats["total_requests"] += 1
            self.usage_stats["last_request"] = datetime.now().isoformat()
            
            response = func(*args, **kwargs)
            logger.info(f"✅ Requête OpenAI réussie")
            return response
            
        except openai.error.AuthenticationError:
            error_msg = "❌ Erreur d'authentification OpenAI. Vérifie ta clé API."
            logger.error(error_msg)
            return {"error": error_msg}
            
        except openai.error.RateLimitError:
            error_msg = "⚠️ Limite de taux dépassée. Réessaye dans quelques instants."
            logger.warning(error_msg)
            return {"error": error_msg}
            
        except openai.error.APIConnectionError:
            error_msg = "🔌 Erreur de connexion à l'API OpenAI. Vérifie ta connexion internet."
            logger.error(error_msg)
            return {"error": error_msg}
            
        except openai.error.Timeout:
            error_msg = "⏰ Timeout de l'API OpenAI. Réessaye."
            logger.error(error_msg)
            return {"error": error_msg}
            
        except openai.error.ServiceUnavailableError:
            error_msg = "🔧 Service OpenAI temporairement indisponible."
            logger.error(error_msg)
            return {"error": error_msg}
            
        except openai.error.InvalidRequestError as e:
            error_msg = f"📝 Requête invalide: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
            
        except Exception as e:
            error_msg = f"❌ Erreur inattendue: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}
    
    def _update_conversation_history(self, role: str, content: str):
        """
        Met à jour l'historique de conversation pour le contexte
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        self.conversation_history.append(message)
        
        # Garde seulement les N derniers messages
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]
    
    def _get_system_prompt(self) -> Dict:
        """
        Retourne le prompt système pour Online X Chat AI
        """
        return {
            "role": "system",
            "content": """Tu es Online X Chat AI, un assistant IA multimodal avancé, élégant et futuriste.

🎯 **TON IDENTITÉ** :
- Nom : Online X Chat AI
- Style : Professionnel, chaleureux et innovant
- Ton : Équilibré entre technique et accessible
- Objectif : Aider l'utilisateur de manière exhaustive

🌟 **TES SPÉCIALITÉS** :
- Réponses détaillées et structurées
- Création de contenu (texte, idées, stratégies)
- Analyse et résolution de problèmes
- Génération d'images créatives
- Support technique et éducatif

📝 **FORMAT DE RÉPONSE** :
- Utilise des emojis pertinents pour aérer le texte
- Structure avec des titres clairs si nécessaire
- Sois concis mais complet
- Propose des étapes ou des alternatives quand c'est utile

🚀 **ÉLÉMENTS FUTURISTES** :
- Terminologie moderne mais accessible
- Vision orientée solutions
- Approche innovante des problèmes

N'oublie pas : tu es l'assistant IA le plus avancé et utile possible !"""
        }
    
    def chat_completion(self, 
                       user_message: str, 
                       use_history: bool = True,
                       max_tokens: Optional[int] = None,
                       temperature: Optional[float] = None) -> str:
        """
        Génère une réponse de chat avancée avec gestion du contexte
        """
        try:
            self.usage_stats["chat_requests"] += 1
            
            # Construction des messages
            messages = [self._get_system_prompt()]
            
            # Ajout de l'historique si demandé
            if use_history and self.conversation_history:
                for msg in self.conversation_history[-6:]:  # Derniers 6 messages
                    messages.append({"role": msg["role"], "content": msg["content"]})
            
            # Ajout du nouveau message
            messages.append({"role": "user", "content": user_message})
            
            # Appel à l'API OpenAI
            response = self._make_request(
                openai.ChatCompletion.create,
                model=self.chat_model,
                messages=messages,
                max_tokens=max_tokens or self.default_max_tokens,
                temperature=temperature or self.default_temperature,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            if isinstance(response, dict) and "error" in response:
                return response["error"]
            
            # Extraction de la réponse
            ai_response = response.choices[0].message.content
            
            # Mise à jour de l'historique
            self._update_conversation_history("user", user_message)
            self._update_conversation_history("assistant", ai_response)
            
            logger.info(f"💬 Chat completion réussi - Tokens: {response.usage.total_tokens}")
            return ai_response
            
        except Exception as e:
            error_msg = f"❌ Erreur lors de la génération de réponse: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def generate_image(self, 
                      prompt: str, 
                      size: str = "1024x1024",
                      quality: str = "standard",
                      style: str = "vivid") -> Optional[str]:
        """
        Génère une image avec DALL-E 3 avec des paramètres avancés
        """
        try:
            self.usage_stats["image_requests"] += 1
            
            # Amélioration du prompt pour DALL-E 3
            enhanced_prompt = self._enhance_image_prompt(prompt)
            
            response = self._make_request(
                openai.Image.create,
                model=self.image_model,
                prompt=enhanced_prompt,
                size=size,
                quality=quality,
                style=style,
                n=1
            )
            
            if isinstance(response, dict) and "error" in response:
                return response["error"]
            
            image_url = response.data[0].url
            
            # Mise à jour de l'historique
            self._update_conversation_history("user", f"[Génération d'image] {prompt}")
            self._update_conversation_history("assistant", f"🖼️ Image générée: {image_url}")
            
            logger.info(f"🎨 Image générée avec succès: {prompt[:50]}...")
            return image_url
            
        except Exception as e:
            error_msg = f"❌ Erreur lors de la génération d'image: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def _enhance_image_prompt(self, prompt: str) -> str:
        """
        Améliore les prompts d'image pour de meilleurs résultats
        """
        enhancements = [
            "Haute qualité, détaillé, professionnel",
            "Style futuriste et cyberpunk",
            "Éclairage dramatique, couleurs vibrantes",
            "8K, ultra HD, rendu réaliste"
        ]
        
        enhanced = f"{prompt}. {', '.join(enhancements)}"
        return enhanced
    
    def vision_analysis(self, image_url: str, question: str) -> str:
        """
        Analyse une image avec GPT-4 Vision
        """
        try:
            response = self._make_request(
                openai.ChatCompletion.create,
                model=self.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": question},
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url}
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            if isinstance(response, dict) and "error" in response:
                return response["error"]
            
            analysis = response.choices[0].message.content
            
            # Mise à jour de l'historique
            self._update_conversation_history("user", f"[Analyse d'image] {question}")
            self._update_conversation_history("assistant", f"🔍 Analyse: {analysis}")
            
            return analysis
            
        except Exception as e:
            error_msg = f"❌ Erreur lors de l'analyse d'image: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def multi_modal_chat(self, text: str, image_url: Optional[str] = None) -> str:
        """
        Chat multimodal supportant texte + image
        """
        try:
            messages = [self._get_system_prompt()]
            
            content = [{"type": "text", "text": text}]
            if image_url:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": image_url}
                })
            
            messages.append({"
                "role": "user",
                "content": content
            })
            
            response = self._make_request(
                openai.ChatCompletion.create,
                model=self.vision_model,
                messages=messages,
                max_tokens=1500
            )
            
            if isinstance(response, dict) and "error" in response:
                return response["error"]
            
            return response.choices[0].message.content
            
        except Exception as e:
            error_msg = f"❌ Erreur chat multimodal: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def get_models(self) -> List[str]:
        """
        Récupère la liste des modèles disponibles
        """
        try:
            models = openai.Model.list()
            return [model.id for model in models.data]
        except Exception as e:
            logger.error(f"❌ Erreur récupération modèles: {e}")
            return []
    
    def get_usage_statistics(self) -> Dict:
        """
        Retourne les statistiques d'usage
        """
        return {
            **self.usage_stats,
            "conversation_history_length": len(self.conversation_history),
            "active_models": {
                "chat": self.chat_model,
                "image": self.image_model,
                "vision": self.vision_model
            }
        }
    
    def clear_conversation_history(self):
        """
        Efface l'historique de conversation
        """
        self.conversation_history.clear()
        logger.info("🗑️ Historique de conversation effacé")
    
    def set_model(self, model_type: str, model_name: str):
        """
        Change le modèle utilisé
        """
        model_type = model_type.lower()
        
        if model_type == "chat" and model_name.startswith("gpt"):
            self.chat_model = model_name
            logger.info(f"🔧 Modèle chat changé vers: {model_name}")
        
        elif model_type == "image" and model_name.startswith("dall-e"):
            self.image_model = model_name
            logger.info(f"🎨 Modèle image changé vers: {model_name}")
        
        else:
            logger.warning(f"⚠️ Modèle non supporté: {model_name}")

# Singleton pour une utilisation globale
_onlinex_ai_instance = None

def get_ai_client() -> OpenAIClient:
    """
    Retourne l'instance singleton du client AI
    """
    global _onlinex_ai_instance
    if _onlinex_ai_instance is None:
        _onlinex_ai_instance = OpenAIClient()
    return _onlinex_ai_instance

# Exemple d'utilisation et tests
if __name__ == "__main__":
    def test_openai_client():
        """Teste le client OpenAI"""
        print("🧪 Test du client OpenAI...")
        
        try:
            client = OpenAIClient()
            
            # Test de connexion
            models = client.get_models()
            print(f"✅ Modèles disponibles: {len(models)}")
            
            # Test chat simple
            response = client.chat_completion("Bonjour ! Présente-toi en 2 phrases.")
            print(f"✅ Test chat: {response[:100]}...")
            
            # Test statistiques
            stats = client.get_usage_statistics()
            print(f"📊 Statistiques: {stats}")
            
            print("🎉 Tous les tests passent !")
            
        except Exception as e:
            print(f"❌ Erreur: {e}")

    test_openai_client()