import os
import sys
import tkinter as tk
from chatbot_engine import ChatbotEngine
from gui import ChatbotGUI

def main():
    # Define project directory structure relative to the workspace
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    assets_dir = os.path.join(project_dir, "assets")
    exports_dir = os.path.join(project_dir, "exports")
    history_dir = os.path.join(project_dir, "chat_history")
    
    # Create folders if they do not exist
    os.makedirs(assets_dir, exist_ok=True)
    os.makedirs(exports_dir, exist_ok=True)
    os.makedirs(history_dir, exist_ok=True)
    
    # Paths to JSON database files
    intents_path = os.path.join(project_dir, "intents.json")
    config_path = os.path.join(project_dir, "responses.json")
    
    print("=========================================")
    print("Starting AssistBot Customer Support System")
    print(f"Project Directory: {project_dir}")
    print("=========================================")
    
    # 1. Initialize NLP engine
    engine = ChatbotEngine(intents_path, config_path)
    
    # 2. Start GUI Main Loop
    root = tk.Tk()
    app = ChatbotGUI(root, engine, assets_dir, exports_dir, history_dir)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nApplication closed by user.")
        sys.exit(0)

if __name__ == "__main__":
    main()
