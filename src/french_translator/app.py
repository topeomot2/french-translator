import json
import os

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

SYSTEM_PROMPT_ENGLISH_TO_FRENCH = (
    """
    You are a translator. Translate the user's text into French and provide the english like pronunciation of the French translation.
    You should respond in JSON with no commentary as in this example:
    
    {
        "translation": "Bonjour, comment ça va?",
        "pronunciation": "bohn-zhoor, koh-mahn sah vah?"
    }
    """
)

SYSTEM_PROMPT_FRENCH_TO_ENGLISH = (
    """
    You are a translator. Translate the user's text into English and provide the english like pronunciation of the input French text.
    You should respond in JSON with no commentary as in this example:
    
    {
        "translation": "Hello, how are you?",
        "pronunciation": "bohn-zhoor, koh-mahn sah vah?"
    }
    """
)

def check_api_key() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError(
            "The OPENAI_API_KEY environment variable is not set. "
            "Please set it to your OpenAI API key."
        )

def set_up_client() -> OpenAI:
    check_api_key()
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])

client = set_up_client()

def translate(text: str, lang: str):
    if not text.strip():
        return "", None

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_ENGLISH_TO_FRENCH if lang == "English" else SYSTEM_PROMPT_FRENCH_TO_ENGLISH},
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"}
    )
    message = response.choices[0].message.content or ''

    if message.strip() == '':
        return "No translation available.", None
    
    json_response = json.loads(message)

    output = None
    audio = None

    translation = json_response.get("translation", "").strip()
    pronunciation = json_response.get("pronunciation", "").strip()

    if lang == "English" and translation != '':
        audio = create_audio_pronunciation(translation)
        output = f"""
        ## {translation}
        {pronunciation}
        """
    elif lang == "French" and translation != '':
        audio = create_audio_pronunciation(text)
        output = f"""
        ## {translation}
        {pronunciation}
        """
    else:
        output = "No translation available."
    return output, audio


def create_audio_pronunciation(sentence):
    response = client.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=sentence,
    )
    return response.content

def on_lang_change(lang):
    return gr.update(label=lang)

def build_ui() -> gr.Blocks:
    with gr.Blocks(title="French Translator") as demo:
        gr.Markdown("# French Translator")
        with gr.Row():
            target = gr.Markdown(label="French", container=True)
        with gr.Row():
            audio_output = gr.Audio(autoplay=True)
        with gr.Row():
            source = gr.Textbox(label="English", lines=6, placeholder="Type something…")
        with gr.Row():
            source_lang = gr.Radio(
                label="From Which Language?",
                choices=["French", "English"],
                value="English",
            )
            source_lang.change(on_lang_change, inputs=source_lang, outputs=source)
        with gr.Row():
            gr.Button("Translate", variant="primary").click(
                translate, inputs=[source, source_lang], outputs=[target, audio_output]
            )
    return demo


def main() -> None:
    build_ui().launch()
