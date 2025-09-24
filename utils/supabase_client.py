import os
from supabase import create_client, Client
from datetime import datetime
import uuid
import json
from typing import List, Dict, Optional

class SupabaseClient:
    def __init__(self):
        # Récupère les variables d'environnement
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_KEY')
        
        if not self.url or not self.key:
            raise ValueError("❌ Variables Supabase manquantes. Vérifie ton .env")
        
        try:
            self.client: Client = create_client(self.url, self.key)
            self.table_name = "chat_history"
            self.session_id = self.get_or_create_session_id()
            print("✅ Client Supabase initialisé avec succès")
        except Exception as e:
            raise ConnectionError(f"❌ Erreur connexion Supabase: {e}")
    
    def get_or_create_session_id(self) -> str:
        """Génère ou récupère un ID de session unique"""
        try:
            # Essaye de récupérer depuis le stockage local
            session_id = "onlinex_session_" + str(uuid.uuid4())[:8]
            return session_id
        except:
            return "default_session"
    
    def save_message(self, content: str, role: str, metadata: Optional[Dict] = None) -> bool:
        """
        Sauvegarde un message dans la base de données
        """
        try:
            data = {
                "session_id": self.session_id,
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            response = self.client.table(self.table_name).insert(data).execute()
            
            if hasattr(response, 'error') and response.error:
                print(f"❌ Erreur sauvegarde: {response.error}")
                return False
            
            print(f"✅ Message sauvegardé ({role}): {content[:50]}...")
            return True
            
        except Exception as e:
            print(f"❌ Erreur critique sauvegarde: {e}")
            return False
    
    def get_chat_history(self, limit: int = 20, session_id: str = None) -> List[Dict]:
        """
        Récupère l'historique des conversations
        """
        try:
            target_session = session_id or self.session_id
            
            response = self.client.table(self.table_name)\
                .select("*")\
                .eq("session_id", target_session)\
                .order("timestamp", desc=False)\
                .limit(limit)\
                .execute()
            
            if hasattr(response, 'error') and response.error:
                print(f"❌ Erreur récupération historique: {response.error}")
                return []
            
            # Formatte les données
            history = []
            for item in response.data:
                history.append({
                    'role': item['role'],
                    'content': item['content'],
                    'timestamp': item['timestamp'],
                    'metadata': item.get('metadata', {})
                })
            
            print(f"✅ Historique chargé: {len(history)} messages")
            return history
            
        except Exception as e:
            print(f"❌ Erreur récupération historique: {e}")
            return []
    
    def clear_session_history(self, session_id: str = None) -> bool:
        """
        Supprime l'historique d'une session
        """
        try:
            target_session = session_id or self.session_id
            
            response = self.client.table(self.table_name)\
                .delete()\
                .eq("session_id", target_session)\
                .execute()
            
            if hasattr(response, 'error') and response.error:
                print(f"❌ Erreur suppression historique: {response.error}")
                return False
            
            print(f"✅ Historique de la session {target_session} supprimé")
            return True
            
        except Exception as e:
            print(f"❌ Erreur suppression historique: {e}")
            return False
    
    def get_all_sessions(self) -> List[Dict]:
        """
        Récupère toutes les sessions disponibles
        """
        try:
            response = self.client.table(self.table_name)\
                .select("session_id")\
                .order("timestamp", desc=True)\
                .execute()
            
            if hasattr(response, 'error') and response.error:
                return []
            
            # Élimine les doublons
            sessions = []
            seen = set()
            for item in response.data:
                if item['session_id'] not in seen:
                    sessions.append({'session_id': item['session_id']})
                    seen.add(item['session_id'])
            
            return sessions
            
        except Exception as e:
            print(f"❌ Erreur récupération sessions: {e}")
            return []
    
    def test_connection(self) -> bool:
        """
        Teste la connexion à Supabase
        """
        try:
            response = self.client.table(self.table_name)\
                .select("count", count="exact")\
                .limit(1)\
                .execute()
            
            print("✅ Connexion Supabase fonctionnelle")
            return True
            
        except Exception as e:
            print(f"❌ Test connexion échoué: {e}")
            return False

# Fonction utilitaire pour initialiser le client
def create_supabase_client():
    """Factory function pour créer le client Supabase"""
    return SupabaseClient()