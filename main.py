from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.uix.modalview import ModalView
from kivy.uix.dropdown import DropDown
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.core.window import Window
from kivy.properties import StringProperty, BooleanProperty, NumericProperty, ListProperty
from kivy.animation import Animation
from kivy.effects.dampedscroll import DampedScrollEffect
from kivy.utils import get_color_from_hex
import threading
import os
from datetime import datetime
import uuid

from utils.openai_handler import OpenAIClient
from utils.supabase_client import SupabaseClient

class NeuButton(Button):
    """Bouton avec effet néomorphique"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.color = (0.2, 0.8, 1, 1)
        self.font_size = '16sp'
        self.bold = True
        self.always_release = True
        
    def on_press(self):
        anim = Animation(scale=0.95, duration=0.1) + Animation(scale=1.0, duration=0.1)
        anim.start(self)

class GlowingLabel(Label):
    """Label avec effet de glow animé"""
    glow_intensity = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(lambda dt: self.animate_glow(), 0.5)
    
    def animate_glow(self):
        anim = Animation(glow_intensity=1, duration=2) + Animation(glow_intensity=0, duration=2)
        anim.repeat = True
        anim.start(self)

class ChatBubble(BoxLayout):
    """Bulles de chat avec style futuriste"""
    message = StringProperty("")
    is_user = BooleanProperty(False)
    timestamp = StringProperty("")

class AILoadingSpinner(ModalView):
    """Spinner de chargement personnalisé"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (140, 140)
        self.background_color = (0, 0, 0, 0.85)
        self.auto_dismiss = False
        
        content = BoxLayout(orientation='vertical', padding=25, spacing=15)
        
        # Animation de loading
        self.loading_icon = Image(
            source='assets/loading.gif' if os.path.exists('assets/loading.gif') else '',
            size_hint=(None, None), 
            size=(60, 60)
        )
        
        # Texte animé
        thinking_text = GlowingLabel(
            text='Online X réfléchit...',
            color=(0.2, 0.8, 1, 1),
            font_size='16sp',
            bold=True
        )
        
        # Points animés
        dots_label = Label(
            text='. . .',
            color=(0.5, 0.8, 1, 1),
            font_size='20sp'
        )
        
        def animate_dots():
            anim = Animation(opacity=0.3, duration=0.5) + Animation(opacity=1, duration=0.5)
            anim.repeat = True
            anim.start(dots_label)
        
        Clock.schedule_once(lambda dt: animate_dots(), 0.1)
        
        content.add_widget(self.loading_icon)
        content.add_widget(thinking_text)
        content.add_widget(dots_label)
        self.add_widget(content)

class SessionManager(ModalView):
    """Gestionnaire de sessions"""
    def __init__(self, supabase_client, callback, **kwargs):
        super().__init__(**kwargs)
        self.supabase_client = supabase_client
        self.callback = callback
        self.size_hint = (0.85, 0.7)
        self.setup_ui()
    
    def setup_ui(self):
        content = BoxLayout(orientation='vertical', spacing=15, padding=20)
        
        # Header
        header = BoxLayout(size_hint_y=None, height=50)
        title = Label(
            text='📁 Gestion des Sessions',
            color=(0.2, 0.8, 1, 1),
            font_size='20sp',
            bold=True
        )
        header.add_widget(title)
        header.add_widget(Label())  # Spacer
        
        close_btn = NeuButton(text='✕', size_hint_x=None, width=50)
        close_btn.bind(on_press=lambda x: self.dismiss())
        header.add_widget(close_btn)
        
        # Liste des sessions
        sessions_label = Label(
            text='Sessions disponibles:',
            color=(0.7, 0.9, 1, 1),
            font_size='16sp',
            size_hint_y=None,
            height=30
        )
        
        self.sessions_scroll = ScrollView()
        self.sessions_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=5)
        self.sessions_layout.bind(minimum_height=self.sessions_layout.setter('height'))
        self.sessions_scroll.add_widget(self.sessions_layout)
        
        # Boutons d'action
        actions_layout = BoxLayout(size_hint_y=None, height=60, spacing=10)
        
        new_session_btn = NeuButton(text='🆕 Nouvelle Session')
        new_session_btn.bind(on_press=self.create_new_session)
        
        refresh_btn = NeuButton(text='🔄 Actualiser')
        refresh_btn.bind(on_press=self.load_sessions)
        
        actions_layout.add_widget(new_session_btn)
        actions_layout.add_widget(refresh_btn)
        
        content.add_widget(header)
        content.add_widget(sessions_label)
        content.add_widget(self.sessions_scroll)
        content.add_widget(actions_layout)
        
        self.add_widget(content)
        self.load_sessions()
    
    def load_sessions(self, instance=None):
        """Charge la liste des sessions"""
        self.sessions_layout.clear_widgets()
        
        sessions = self.supabase_client.get_all_sessions()
        
        if not sessions:
            empty_label = Label(
                text='Aucune session trouvée',
                color=(0.5, 0.5, 0.7, 1),
                italic=True
            )
            self.sessions_layout.add_widget(empty_label)
            return
        
        for session in sessions:
            session_btn = Button(
                text=f"💬 {session['session_id']}",
                size_hint_y=None,
                height=60,
                background_color=(0.15, 0.15, 0.25, 1),
                color=(0.8, 0.9, 1, 1)
            )
            session_btn.bind(
                on_press=lambda x, s=session: self.select_session(s['session_id'])
            )
            self.sessions_layout.add_widget(session_btn)
    
    def select_session(self, session_id):
        """Sélectionne une session"""
        self.callback(session_id)
        self.dismiss()
    
    def create_new_session(self, instance):
        """Crée une nouvelle session"""
        new_session_id = f"onlinex_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.callback(new_session_id)
        self.dismiss()

class OnlineXChatAI(BoxLayout):
    """Interface principale de l'application"""
    
    current_session = StringProperty("Session Principale")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = [15, 10, 15, 10]
        self.spacing = 15
        
        self.setup_ui()
        self.setup_clients()
        
        # Charger l'historique après initialisation
        Clock.schedule_once(self.load_history, 0.5)
    
    def setup_ui(self):
        """Configure l'interface utilisateur"""
        self.setup_header()
        self.setup_chat_area()
        self.setup_input_area()
    
    def setup_header(self):
        """Configure l'en-tête de l'application"""
        header = BoxLayout(size_hint_y=None, height=110, spacing=20, padding=[20, 10])
        
        with header.canvas.before:
            # Fond avec effet de profondeur
            Color(0.08, 0.08, 0.18, 1)
            RoundedRectangle(pos=header.pos, size=header.size, radius=[25,])
            
            # Bordure lumineuse
            Color(0.2, 0.8, 1, 0.4)
            Line(rounded_rectangle=[header.x, header.y, header.width, header.height, 25], width=1.5)
        
        # Logo
        logo_container = BoxLayout(size_hint_x=None, width=80)
        logo = Image(
            source='assets/logo.png' if os.path.exists('assets/logo.png') else '',
            size_hint=(None, None), 
            size=(70, 70)
        )
        logo_container.add_widget(logo)
        
        # Titre et informations
        title_container = BoxLayout(orientation='vertical', spacing=2)
        
        main_title = GlowingLabel(
            text='ONLINE X CHAT AI',
            font_size='22sp',
            bold=True,
            color=(0.2, 0.8, 1, 1)
        )
        
        subtitle = Label(
            text='Assistant IA Multimodal Avancé',
            font_size='12sp',
            color=(0.7, 0.7, 1, 0.8)
        )
        
        session_info = Label(
            text=f'Session: {self.current_session}',
            font_size='10sp',
            color=(0.5, 0.8, 1, 0.7)
        )
        
        title_container.add_widget(main_title)
        title_container.add_widget(subtitle)
        title_container.add_widget(session_info)
        
        # Boutons header
        header_buttons = BoxLayout(size_hint_x=None, width=120, spacing=10)
        
        session_btn = NeuButton(text='📁', size_hint_x=None, width=50)
        session_btn.bind(on_press=self.show_session_manager)
        
        clear_btn = NeuButton(text='🗑️', size_hint_x=None, width=50)
        clear_btn.bind(on_press=self.clear_chat)
        
        header_buttons.add_widget(session_btn)
        header_buttons.add_widget(clear_btn)
        
        header.add_widget(logo_container)
        header.add_widget(title_container)
        header.add_widget(header_buttons)
        
        self.add_widget(header)
    
    def setup_chat_area(self):
        """Configure la zone de chat"""
        chat_container = BoxLayout(orientation='vertical', spacing=5)
        
        # Zone de défilement du chat
        self.chat_scroll = ScrollView(
            effect_cls=DampedScrollEffect,
            bar_width=8,
            bar_color=(0.2, 0.6, 1, 0.5)
        )
        
        self.chat_layout = BoxLayout(
            orientation='vertical', 
            size_hint_y=None, 
            spacing=12,
            padding=[10, 20]
        )
        self.chat_layout.bind(minimum_height=self.chat_layout.setter('height'))
        self.chat_scroll.add_widget(self.chat_layout)
        
        chat_container.add_widget(self.chat_scroll)
        self.add_widget(chat_container)
    
    def setup_input_area(self):
        """Configure la zone de saisie"""
        input_container = BoxLayout(size_hint_y=None, height=90, spacing=15)
        
        with input_container.canvas.before:
            # Fond avec effet de profondeur
            Color(0.1, 0.1, 0.2, 0.9)
            RoundedRectangle(
                pos=[input_container.x + 5, input_container.y + 5], 
                size=[input_container.width - 10, input_container.height - 10], 
                radius=[20,]
            )
        
        # Bouton sessions
        session_btn = NeuButton(
            text='📁',
            size_hint_x=None,
            width=60,
            background_color=(0.3, 0.5, 0.8, 0.3)
        )
        session_btn.bind(on_press=self.show_session_manager)
        
        # Champ de saisie principal
        self.message_input = TextInput(
            hint_text='💬 Posez votre question à Online X AI...',
            multiline=False,
            background_color=(0.15, 0.15, 0.25, 1),
            foreground_color=(1, 1, 1, 1),
            padding=[20, 15],
            font_size='16sp',
            hint_text_color=(0.5, 0.7, 1, 0.6)
        )
        self.message_input.bind(on_text_validate=self.send_message)
        
        # Bouton envoi
        send_btn = NeuButton(
            text='🚀',
            size_hint_x=None,
            width=70,
            background_color=(0.2, 0.8, 0.6, 0.4)
        )
        send_btn.bind(on_press=self.send_message)
        
        # Bouton image
        image_btn = NeuButton(
            text='🖼️',
            size_hint_x=None,
            width=60,
            background_color=(0.8, 0.4, 0.8, 0.3)
        )
        image_btn.bind(on_press=self.show_image_modal)
        
        input_container.add_widget(session_btn)
        input_container.add_widget(self.message_input)
        input_container.add_widget(image_btn)
        input_container.add_widget(send_btn)
        
        self.add_widget(input_container)
    
    def setup_clients(self):
        """Initialise les clients Supabase et OpenAI"""
        try:
            self.supabase_client = SupabaseClient()
            if self.supabase_client.test_connection():
                print("✅ Supabase connecté avec succès")
            else:
                self.show_error("❌ Erreur de connexion à la base de données")
                return
            
            self.openai_client = OpenAIClient()
            print("✅ OpenAI configuré avec succès")
            
        except Exception as e:
            self.show_error(f"❌ Erreur d'initialisation: {str(e)}")
    
    def load_history(self, dt):
        """Charge l'historique de la session actuelle"""
        try:
            history = self.supabase_client.get_chat_history(limit=15)
            if history:
                for msg in history:
                    timestamp = msg.get('timestamp', '')
                    if timestamp:
                        try:
                            dt_obj = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            formatted_time = dt_obj.strftime('%H:%M')
                        except:
                            formatted_time = "maintenant"
                    else:
                        formatted_time = "maintenant"
                    
                    self.add_message(msg['content'], msg['role'] == 'user', formatted_time)
            else:
                welcome_msg = "👋 Bienvenue sur Online X Chat AI ! Je suis ton assistant IA multimodal. Posez-moi n'importe quelle question !"
                self.add_message(welcome_msg, False, "maintenant")
                
        except Exception as e:
            print(f"⚠️ Historique non chargé: {e}")
            welcome_msg = "👋 Bienvenue ! Commencez une nouvelle conversation avec votre IA."
            self.add_message(welcome_msg, False, "maintenant")
    
    def add_message(self, message, is_user, timestamp=""):
        """Ajoute un message à la conversation"""
        bubble = ChatBubble(message=message, is_user=is_user, timestamp=timestamp)
        self.chat_layout.add_widget(bubble)
        
        # Animation d'apparition
        bubble.opacity = 0
        anim = Animation(opacity=1, duration=0.5)
        anim.start(bubble)
        
        Clock.schedule_once(lambda dt: self.scroll_to_bottom(), 0.1)
    
    def scroll_to_bottom(self):
        """Fait défiler vers le bas de la conversation"""
        self.chat_scroll.scroll_y = 0
    
    def send_message(self, instance):
        """Envoie un message à l'IA"""
        message = self.message_input.text.strip()
        if not message:
            return
        
        self.message_input.text = ''
        current_time = datetime.now().strftime('%H:%M')
        self.add_message(message, True, current_time)
        
        # Afficher le spinner de chargement
        self.spinner = AILoadingSpinner()
        self.spinner.open()
        
        # Traitement dans un thread séparé
        thread = threading.Thread(target=self.process_ai_response, args=(message, False))
        thread.daemon = True
        thread.start()
    
    def show_image_modal(self, instance):
        """Affiche la modale de génération d'image"""
        modal = ModalView(size_hint=(0.8, 0.5))
        content = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        title = Label(
            text='🎨 Générateur d\'Image Online X',
            color=(0.2, 0.8, 1, 1),
            font_size='18sp',
            bold=True
        )
        
        prompt_input = TextInput(
            hint_text='Décrivez l\'image que vous voulez générer...',
            multiline=True,
            size_hint_y=None,
            height=100
        )
        
        buttons_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        
        generate_btn = NeuButton(text='Générer 🖼️')
        cancel_btn = NeuButton(text='Annuler')
        
        def generate_image():
            prompt = prompt_input.text.strip()
            if prompt:
                modal.dismiss()
                self.process_ai_response(f"Génère une image: {prompt}", True)
        
        generate_btn.bind(on_press=lambda x: generate_image())
        cancel_btn.bind(on_press=lambda x: modal.dismiss())
        
        buttons_layout.add_widget(generate_btn)
        buttons_layout.add_widget(cancel_btn)
        
        content.add_widget(title)
        content.add_widget(prompt_input)
        content.add_widget(buttons_layout)
        
        modal.add_widget(content)
        modal.open()
    
    def process_ai_response(self, user_message, is_image=False):
        """Traite la réponse de l'IA"""
        try:
            # Sauvegarder le message utilisateur
            self.supabase_client.save_message(user_message, 'user')
            
            if is_image:
                # Génération d'image
                image_url = self.openai_client.generate_image(user_message)
                if image_url:
                    ai_response = f"🎨 Image générée avec succès!\n📎 Lien: {image_url}"
                else:
                    ai_response = "❌ Désolé, je n'ai pas pu générer l'image. Réessayez avec une autre description."
            else:
                # Chat normal
                response = self.openai_client.chat_completion(user_message)
                ai_response = response
            
            # Sauvegarder la réponse de l'IA
            self.supabase_client.save_message(ai_response, 'assistant')
            
            # Mettre à jour l'interface
            current_time = datetime.now().strftime('%H:%M')
            Clock.schedule_once(lambda dt: self.show_ai_response(ai_response, current_time), 0)
            
        except Exception as e:
            error_msg = f"⚠️ Erreur: {str(e)}"
            current_time = datetime.now().strftime('%H:%M')
            Clock.schedule_once(lambda dt: self.show_ai_response(error_msg, current_time), 0)
        
        finally:
            Clock.schedule_once(lambda dt: self.spinner.dismiss(), 0)
    
    def show_ai_response(self, response, timestamp):
        """Affiche la réponse de l'IA"""
        self.add_message(response, False, timestamp)
    
    def show_session_manager(self, instance):
        """Affiche le gestionnaire de sessions"""
        modal = SessionManager(self.supabase_client, self.change_session)
        modal.open()
    
    def change_session(self, session_id):
        """Change la session active"""
        self.supabase_client.session_id = session_id
        self.current_session = session_id
        self.chat_layout.clear_widgets()
        self.load_history(0)
        
        # Animation de transition
        self.opacity = 0
        Animation(opacity=1, duration=0.5).start(self)
    
    def clear_chat(self, instance):
        """Efface la conversation actuelle"""
        confirm_modal = ModalView(size_hint=(0.7, 0.3))
        content = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        question = Label(
            text='Effacer toute la conversation?',
            color=(1, 1, 1, 1),
            font_size='16sp'
        )
        
        buttons_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        
        confirm_btn = NeuButton(text='Oui', background_color=(1, 0.3, 0.3, 0.8))
        cancel_btn = NeuButton(text='Non')
        
        def confirm_clear():
            self.supabase_client.clear_session_history()
            self.chat_layout.clear_widgets()
            self.add_message("💬 Conversation effacée. Commencez une nouvelle discussion!", False, "maintenant")
            confirm_modal.dismiss()
        
        confirm_btn.bind(on_press=lambda x: confirm_clear())
        cancel_btn.bind(on_press=lambda x: confirm_modal.dismiss())
        
        buttons_layout.add_widget(confirm_btn)
        buttons_layout.add_widget(cancel_btn)
        
        content.add_widget(question)
        content.add_widget(buttons_layout)
        
        confirm_modal.add_widget(content)
        confirm_modal.open()
    
    def show_error(self, message):
        """Affiche une erreur"""
        error_modal = ModalView(size_hint=(0.7, 0.3))
        content = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        error_label = Label(
            text=message,
            color=(1, 0.3, 0.3, 1),
            font_size='14sp'
        )
        
        close_btn = NeuButton(text='Fermer')
        close_btn.bind(on_press=lambda x: error_modal.dismiss())
        
        content.add_widget(error_label)
        content.add_widget(close_btn)
        
        error_modal.add_widget(content)
        error_modal.open()

class OnlineXApp(App):
    """Application principale"""
    def build(self):
        Window.clearcolor = (0.05, 0.05, 0.12, 1)
        self.title = 'Online X Chat AI'
        self.icon = 'assets/logo.png' if os.path.exists('assets/logo.png') else ''
        return OnlineXChatAI()
    
    def on_start(self):
        """Callback au démarrage de l'app"""
        print("🚀 Online X Chat AI démarré!")
    
    def on_stop(self):
        """Callback à l'arrêt de l'app"""
        print("🛑 Online X Chat AI arrêté")

if __name__ == '__main__':
    OnlineXApp().run()