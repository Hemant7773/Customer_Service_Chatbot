import os
import sys
import datetime
import threading
from PIL import Image, ImageDraw, ImageFont

# Graceful imports for optional speech tools and reportlab
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


def get_timestamp():
    """Returns current timestamp in HH:MM:SS format."""
    return datetime.datetime.now().strftime("%I:%M:%S %p")


def get_datestamp():
    """Returns current date in YYYY-MM-DD format."""
    return datetime.datetime.now().strftime("%Y-%m-%d")


def generate_default_assets(target_dir):
    """
    Generates default bot, user, and logo images if they do not exist.
    This guarantees that the GUI has working assets without manual downloads.
    """
    os.makedirs(target_dir, exist_ok=True)
    
    bot_path = os.path.join(target_dir, "bot.png")
    user_path = os.path.join(target_dir, "user.png")
    logo_path = os.path.join(target_dir, "logo.png")
    
    # Check if we need to generate bot avatar
    if not os.path.exists(bot_path):
        img = Image.new("RGBA", (100, 100), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        # Blue circle
        draw.ellipse([5, 5, 95, 95], fill=(26, 115, 232, 255))
        # Draw eyes and mouth for a robot face
        draw.rectangle([30, 35, 45, 45], fill=(255, 255, 255, 255))
        draw.rectangle([55, 35, 70, 45], fill=(255, 255, 255, 255))
        draw.rounded_rectangle([35, 60, 65, 70], radius=5, fill=(255, 255, 255, 255))
        # Antennas
        draw.line([50, 5, 50, 20], fill=(255, 255, 255, 255), width=4)
        draw.ellipse([45, 2, 55, 12], fill=(255, 200, 0, 255))
        img.save(bot_path, "PNG")

    # Check if we need to generate user avatar
    if not os.path.exists(user_path):
        img = Image.new("RGBA", (100, 100), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        # Teal circle
        draw.ellipse([5, 5, 95, 95], fill=(0, 150, 136, 255))
        # Simple person silhouette
        draw.ellipse([35, 20, 65, 50], fill=(255, 255, 255, 255))
        draw.chord([15, 55, 85, 110], start=180, end=360, fill=(255, 255, 255, 255))
        img.save(user_path, "PNG")

    # Check if we need to generate logo
    if not os.path.exists(logo_path):
        img = Image.new("RGBA", (200, 200), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        # Main speech bubble
        draw.rounded_rectangle([20, 30, 180, 150], radius=15, fill=(26, 115, 232, 255))
        # Tail of speech bubble
        draw.polygon([(40, 150), (40, 180), (70, 150)], fill=(26, 115, 232, 255))
        # Heart or support icon center (smiley face)
        draw.ellipse([80, 60, 95, 75], fill=(255, 255, 255, 255))
        draw.ellipse([105, 60, 120, 75], fill=(255, 255, 255, 255))
        draw.arc([80, 80, 120, 110], start=0, end=180, fill=(255, 255, 255, 255), width=5)
        img.save(logo_path, "PNG")


def save_chat_to_txt(chat_history, filepath):
    """
    Saves the chat history to a text file.
    chat_history: list of dicts with keys 'sender', 'message', 'timestamp'
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("=" * 50 + "\n")
            f.write(f"CUSTOMER SERVICE CHAT LOG - {get_datestamp()}\n")
            f.write("=" * 50 + "\n\n")
            for msg in chat_history:
                f.write(f"[{msg['timestamp']}] {msg['sender']}: {msg['message']}\n")
            f.write("\n" + "=" * 50 + "\n")
            f.write("End of Chat Log. Thank you for choosing our support services.\n")
        return True, f"Chat saved successfully to {os.path.basename(filepath)}"
    except Exception as e:
        return False, str(e)


def export_chat_to_pdf(chat_history, filepath):
    """
    Exports the chat history to a formatted PDF.
    Uses reportlab if available, else falls back to writing a styled HTML page.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    if not PDF_AVAILABLE:
        # Fallback to saving an HTML file with PDF extension or warning the user
        html_path = filepath.replace(".pdf", ".html")
        try:
            with open(html_path, "w", encoding="utf-8") as f:
                f.write("<html><head><style>")
                f.write("body { font-family: Arial, sans-serif; margin: 40px; background: #f5f7fb; }")
                f.write(".header { text-align: center; border-bottom: 2px solid #1A73E8; padding-bottom: 10px; margin-bottom: 20px; }")
                f.write(".msg { margin: 10px 0; padding: 10px; border-radius: 8px; max-width: 80%; }")
                f.write(".bot { background: #e8f0fe; color: #1a73e8; margin-right: auto; }")
                f.write(".user { background: #1a73e8; color: #ffffff; margin-left: auto; }")
                f.write(".timestamp { font-size: 0.8em; color: #777; margin-bottom: 5px; }")
                f.write("</style></head><body>")
                f.write("<div class='header'><h2>Customer Support Chat Log</h2><p>Date: " + get_datestamp() + "</p></div>")
                for msg in chat_history:
                    css_class = "bot" if msg["sender"] == "Bot" else "user"
                    f.write(f"<div class='msg {css_class}'>")
                    f.write(f"<div class='timestamp'>[{msg['timestamp']}] {msg['sender']}</div>")
                    f.write(f"<div>{msg['message']}</div>")
                    f.write("</div>")
                f.write("</body></html>")
            return True, f"ReportLab not installed. Saved as HTML log: {os.path.basename(html_path)}"
        except Exception as e:
            return False, f"PDF export failed and HTML fallback failed: {str(e)}"

    try:
        doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()
        
        # Define styles
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=20,
            textColor=colors.HexColor('#1A73E8'),
            spaceAfter=15,
            alignment=1 # Center
        )
        
        sub_style = ParagraphStyle(
            'SubStyle',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=10,
            textColor=colors.HexColor('#555555'),
            spaceAfter=25,
            alignment=1
        )
        
        bot_text_style = ParagraphStyle(
            'BotText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=colors.HexColor('#202124')
        )
        
        user_text_style = ParagraphStyle(
            'UserText',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=colors.HexColor('#FFFFFF')
        )
        
        story = []
        
        # Header elements
        story.append(Paragraph("CUSTOMER SERVICE ASSISTANT", title_style))
        story.append(Paragraph(f"Conversation Log - Generated on {get_datestamp()}", sub_style))
        story.append(Spacer(1, 10))
        
        # Chat Table formatting
        table_data = []
        for msg in chat_history:
            sender = msg["sender"]
            message = msg["message"]
            timestamp = msg["timestamp"]
            
            # Format text as Paragraph so it wraps properly
            if sender == "Bot":
                text_p = Paragraph(f"<b>[{timestamp}] AssistBot:</b><br/>{message}", bot_text_style)
                cell = Table([[text_p]], colWidths=[400])
                cell.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#E8F0FE')),
                    ('PADDING', (0,0), (-1,-1), 10),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 10),
                ]))
                table_data.append([cell, ""]) # Left aligned
            else:
                text_p = Paragraph(f"<b>[{timestamp}] User:</b><br/>{message}", user_text_style)
                cell = Table([[text_p]], colWidths=[400])
                cell.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1A73E8')),
                    ('PADDING', (0,0), (-1,-1), 10),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 10),
                ]))
                table_data.append(["", cell]) # Right aligned
                
        # Main chat display table
        chat_table = Table(table_data, colWidths=[250, 250])
        chat_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ]))
        
        story.append(chat_table)
        doc.build(story)
        return True, f"PDF export successful: {os.path.basename(filepath)}"
    except Exception as e:
        return False, f"PDF generation error: {str(e)}"


# TTS speaking utility runs in background thread to avoid freezing GUI
_tts_engine = None
_tts_lock = threading.Lock()

def _speak_thread(text):
    global _tts_engine
    with _tts_lock:
        if not TTS_AVAILABLE:
            return
        try:
            if _tts_engine is None:
                _tts_engine = pyttsx3.init()
                # Adjust speaking rate
                _tts_engine.setProperty('rate', 150)
                # Adjust volume
                _tts_engine.setProperty('volume', 0.9)
            _tts_engine.say(text)
            _tts_engine.runAndWait()
        except Exception:
            # TTS engine might be busy or unsupported on this device
            pass

def speak_text(text):
    """
    Speaks the given text in a separate thread.
    Does not block the caller.
    """
    if TTS_AVAILABLE:
        t = threading.Thread(target=_speak_thread, args=(text,), daemon=True)
        t.start()


def listen_speech():
    """
    Uses SpeechRecognition to listen to microphone.
    Returns: (success_boolean, text_result_or_error_msg)
    """
    if not SR_AVAILABLE:
        return False, "SpeechRecognition library not installed. Add it to requirements.txt and install."
    
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            # Adjust for ambient noise
            r.adjust_for_ambient_noise(source, duration=0.8)
            # Listen
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
        
        # Recognize speech using Google Web Speech API (free, does not need key)
        text = r.recognize_google(audio)
        return True, text
    except sr.WaitTimeoutError:
        return False, "Listening timed out. No speech detected."
    except sr.UnknownValueError:
        return False, "Could not understand audio. Please speak clearly."
    except sr.RequestError as e:
        return False, f"Speech recognition service error: {e}"
    except OSError:
        return False, "No working microphone detected. Please connect a mic."
    except Exception as e:
        return False, f"Microphone error: {str(e)}"
