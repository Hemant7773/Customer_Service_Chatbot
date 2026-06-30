# AssistBot - Customer Service Chatbot in Python

AssistBot is a professional, rule-based Customer Service Chatbot developed in Python. It features basic Natural Language Processing (NLP), a responsive Tkinter graphical user interface (GUI) with Light/Dark mode toggles, and voice interaction support. The project includes an administrative portal to modify the JSON FAQ database dynamically.

---

## 🚀 Features

### 1. Modern GUI Interface
- **Chat Bubbles**: Structured dialog flow with message bubbles for user and bot.
- **Avatars**: Circular icons representing user and system (auto-generated if missing).
- **Themes**: Live toggle between professional light and dark modes.
- **History Utilities**: One-click clear dialogue, save chat to `.txt` files, and export conversation history to styled `.pdf` documents.

### 2. Natural Language Processing (NLP)
- **Tokenization & Stopword Filtering**: Separates keywords from noise using NLTK or built-in fallback parser.
- **Lemmatization**: Reduces words to root forms (e.g., "running" to "run").
- **Synonym Expansion**: Maps varied inputs (like "rates", "cost", "pricing") to common intent roots.
- **Fuzzy matching**: Handles spelling mistakes or slightly rephrased queries via `difflib.SequenceMatcher`.

### 3. Smart Conversational Memory
- **Name Recognition**: Parses strings like "My name is John" and replies with personalized greetings.
- **Context Tracking**: Remembers follow-up context tags to handle subsequent questions cleanly.

### 4. Extra Channels
- **Voice Recognition (STT)**: Microphone button translates spoken audio into text input.
- **Voice Synthesis (TTS)**: Text-to-Speech engine speaks responses aloud in a background thread to prevent GUI freezes.

### 5. Admin portal
- Add new FAQ categories directly in the GUI.
- Edit search patterns and bot responses.
- Delete obsolete intents.
- Save updates back to `intents.json`.

---

## 📁 Project Directory Structure

```text
Customer_Service_Chatbot/
├── chatbot.py               # Main entry point to run the application
├── gui.py                  # Tkinter UI implementation & Admin layout
├── chatbot_engine.py       # Core NLP processing & match logic
├── intents.json            # Knowledge base storing intents/answers
├── responses.json          # Fallback responses & theme definitions
├── utils.py                # File utilities, TTS, speech recognition, avatar generator
├── requirements.txt        # Package dependencies
└── README.md               # User guide (This file)
```

---

## 🛠 Installation & Setup

1. **Verify Python Installation**: Make sure Python 3.9+ is installed.
2. **Install Dependencies**:
   Open a terminal and navigate to the project directory, then run:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: For voice typing to work, your system must have microphone access. PyAudio is required by SpeechRecognition. If the microphone fails, make sure your audio drivers are configured correctly.*

3. **Run the Application**:
   Execute the wrapper script:
   ```bash
   python chatbot.py
   ```

---

## 💡 Code Verification & Testing

- To check that dependencies are met, run:
  ```bash
  python -c "import nltk, PIL, reportlab, pyttsx3, speech_recognition"
  ```
- NLTK datasets (`punkt`, `stopwords`, `wordnet`) are automatically downloaded upon the first launch. If you run offline, the bot activates a pure Python fallback tokenizer and lemmatizer.
