import json
import os

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

SYSTEM_PROMPT = (
    """
    You are a translator. Translate the user's text into French and provide the english like pronunciation of the French translation.
    You should respond in JSON with no commentary as in this example:
    
    {
        "translation": "Bonjour, comment ça va?",
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

def translate(text: str):
    if not text.strip():
        return "", None

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
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

    if translation != '':
        audio = create_audio_pronunciation(translation)
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
            gr.Button("Translate", variant="primary").click(
                translate, inputs=source, outputs=[target, audio_output]
            )
    return demo


def main() -> None:
    build_ui().launch()
