import json
import re
import random
import os
from difflib import SequenceMatcher

# NLTK bootstrapping with fallback to pure Python if imports or downloads fail
NLTK_AVAILABLE = False
try:
    import nltk
    # Bootstrap required packages
    for resource in ['punkt', 'stopwords', 'wordnet']:
        try:
            nltk.data.find(f'tokenizers/{resource}' if resource == 'punkt' else f'corpora/{resource}')
        except LookupError:
            nltk.download(resource, quiet=True)
            
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))
    NLTK_AVAILABLE = True
except Exception:
    # If NLTK fails or has download issues, we use pure python fallback
    NLTK_AVAILABLE = False


class ChatbotEngine:
    def __init__(self, intents_filepath, config_filepath):
        self.intents_filepath = intents_filepath
        self.config_filepath = config_filepath
        self.intents = []
        self.config = {}
        
        # Conversation state
        self.user_name = None
        self.current_context = None
        
        # Load data
        self.load_intents()
        self.load_config()
        
        # Standard synonym dictionary to expand keyword recognition
        self.synonyms = {
            "buy": ["purchase", "order", "get", "acquire", "shop"],
            "return": ["refund", "exchange", "send back", "returns", "returning"],
            "refund": ["reimburse", "money back", "repayment", "refunds"],
            "shipping": ["delivery", "postage", "carrier", "shipment", "transport"],
            "hours": ["timing", "timings", "schedule", "open", "close", "operating"],
            "hello": ["hi", "hey", "hola", "greetings", "howdy"],
            "login": ["signin", "log in", "log-in", "enter", "portal"],
            "password": ["pass", "code", "credentials", "passcode"],
            "contact": ["call", "email", "phone", "support", "speak", "talk", "representative"],
            "delivery": ["arrival", "shipment", "courier", "receive"]
        }

    def load_intents(self):
        """Loads intents from JSON file."""
        if os.path.exists(self.intents_filepath):
            try:
                with open(self.intents_filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.intents = data.get("intents", [])
            except Exception as e:
                print(f"Error loading intents.json: {e}")
                self.intents = []
        else:
            print("intents.json not found, initializing empty list.")
            self.intents = []

    def load_config(self):
        """Loads bot responses configuration."""
        if os.path.exists(self.config_filepath):
            try:
                with open(self.config_filepath, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception as e:
                print(f"Error loading responses.json: {e}")
                self.config = {}
        else:
            self.config = {}

    def save_intents(self):
        """Saves current intents list to JSON file."""
        try:
            with open(self.intents_filepath, 'w', encoding='utf-8') as f:
                json.dump({"intents": self.intents}, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving intents: {e}")
            return False

    def clean_text_pure_python(self, text):
        """Pure Python fallback for tokenization, stopword removal, and basic stemming."""
        # Convert to lowercase and strip non-alphanumeric chars
        text = text.lower()
        words = re.findall(r'\b[a-z0-9]+\b', text)
        
        # Simple stop words set
        fallback_stops = {'is', 'an', 'the', 'a', 'to', 'for', 'of', 'in', 'on', 'at', 'by', 'this', 'that', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your'}
        cleaned_words = [w for w in words if w not in fallback_stops]
        
        # Very basic lemmatizer fallback (strips plural 's' or 'es', 'ing', 'ed')
        stemmed_words = []
        for w in cleaned_words:
            if len(w) > 4:
                if w.endswith('ing'):
                    w = w[:-3]
                elif w.endswith('ed'):
                    w = w[:-2]
                elif w.endswith('ies'):
                    w = w[:-3] + 'y'
                elif w.endswith('s') and not w.endswith('ss'):
                    w = w[:-1]
            stemmed_words.append(w)
        return stemmed_words

    def preprocess(self, text):
        """Preprocesses text using NLTK if available, otherwise pure Python fallback."""
        if not NLTK_AVAILABLE:
            return self.clean_text_pure_python(text)
        
        try:
            text = text.lower()
            tokens = word_tokenize(text)
            # Remove stopwords and punctuation
            cleaned = [word for word in tokens if word.isalnum() and word not in stop_words]
            # Lemmatize
            lemmatized = [lemmatizer.lemmatize(word) for word in cleaned]
            return lemmatized
        except Exception:
            return self.clean_text_pure_python(text)

    def expand_synonyms(self, tokens):
        """Expands the query tokens list to include predefined synonyms."""
        expanded = list(tokens)
        for token in tokens:
            for key, val in self.synonyms.items():
                if token == key or token in val:
                    expanded.append(key)
                    expanded.extend(val)
        return list(set(expanded))

    def extract_name(self, text):
        """Uses Regex to search for patterns indicating the user's name."""
        name_patterns = [
            r"\bmy name is ([a-zA-Z]+)\b",
            r"\bi am ([a-zA-Z]+)\b",
            r"\bi'm ([a-zA-Z]+)\b",
            r"\bcall me ([a-zA-Z]+)\b",
            r"\bthis is ([a-zA-Z]+)\b"
        ]
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                self.user_name = match.group(1).capitalize()
                return self.user_name
        return None

    def calculate_fuzzy_match(self, text, patterns):
        """Uses difflib to compare string similarity for fallback intents."""
        max_ratio = 0.0
        cleaned_text = text.lower().strip()
        for pattern in patterns:
            cleaned_pat = pattern.lower().strip()
            ratio = SequenceMatcher(None, cleaned_text, cleaned_pat).ratio()
            if ratio > max_ratio:
                max_ratio = ratio
        return max_ratio

    def match_intent(self, text):
        """
        Determines the intent of a user's text.
        Matches using:
        1. Exact/keyword overlap
        2. Context filtering
        3. Synonym expansion
        4. Fuzzy matching
        """
        tokens = self.preprocess(text)
        expanded_tokens = self.expand_synonyms(tokens)
        
        best_intent = None
        highest_score = 0
        
        # Check all loaded intents
        for intent in self.intents:
            if intent["tag"] == "unknown":
                continue
                
            score = 0
            
            # 1. Match patterns keywords
            for pattern in intent["patterns"]:
                pattern_tokens = self.preprocess(pattern)
                # Count matching tokens
                overlap = set(expanded_tokens).intersection(set(pattern_tokens))
                score += len(overlap)
                
                # Check for direct phrase match
                if pattern.lower() in text.lower():
                    score += 3
            
            # 2. Check context-awareness boost
            if "context_filter" in intent and intent["context_filter"] == self.current_context:
                score += 2 # Boost matches matching active context
                
            if score > highest_score:
                highest_score = score
                best_intent = intent
        
        # If score is too low, attempt fuzzy matching
        if highest_score <= 1:
            fuzzy_best_intent = None
            highest_fuzzy = 0.0
            
            for intent in self.intents:
                if intent["tag"] == "unknown" or not intent["patterns"]:
                    continue
                ratio = self.calculate_fuzzy_match(text, intent["patterns"])
                if ratio > highest_fuzzy:
                    highest_fuzzy = ratio
                    fuzzy_best_intent = intent
            
            # If fuzzy match is above 60% similarity, select it
            if highest_fuzzy >= 0.60:
                best_intent = fuzzy_best_intent
                
        # If we still don't have a good match, fall back to "unknown"
        if not best_intent or (highest_score == 0 and highest_fuzzy < 0.60):
            for intent in self.intents:
                if intent["tag"] == "unknown":
                    return intent
                    
        return best_intent

    def get_response(self, user_message):
        """
        Generates the chatbot response.
        Updates internal context, resolves placeholders like name, and returns text.
        """
        user_message_clean = user_message.strip()
        if not user_message_clean:
            return "Please type a message so I can help you!"
            
        # 1. Look for user name in text
        new_name = self.extract_name(user_message_clean)
        
        # 2. Find intent
        intent = self.match_intent(user_message_clean)
        
        # 3. Handle Context Setting
        if "context_set" in intent:
            self.current_context = intent["context_set"]
        else:
            self.current_context = None # Clear context if no follow-up context set
            
        # 4. Generate reply text
        responses_list = intent.get("responses", [])
        if not responses_list:
            # Fall back to responses.json templates
            fallbacks = self.config.get("bot_config", {}).get("fallback_responses", [
                "I'm sorry, I'm not sure how to answer that."
            ])
            response_text = random.choice(fallbacks)
        else:
            response_text = random.choice(responses_list)
            
        # 5. Context-aware modifications
        # If user name is known, greet them personalized
        if self.user_name and intent["tag"] == "greetings":
            personal_greetings = [
                f"Hello {self.user_name}! How can I help you today?",
                f"Hi {self.user_name}! Welcome back. How can I assist you?",
                f"Hey {self.user_name}, great to see you! What can I do for you today?"
            ]
            response_text = random.choice(personal_greetings)
            
        # If user introduced themselves, respond directly
        if new_name and intent["tag"] == "greetings":
            response_text = f"Nice to meet you, {new_name}! How can I assist you with your customer service needs today?"
            
        return response_text
