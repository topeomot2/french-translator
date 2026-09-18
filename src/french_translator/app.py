import os

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

SYSTEM_PROMPT = (
    "You are a translator. Translate the user's text into French. "
    "Return only the translation, with no commentary."
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


def translate(text: str) -> str:
    client = set_up_client()
    if not text.strip():
        return ""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    )
    return response.choices[0].message.content or ""


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="French Translator") as demo:
        gr.Markdown("# French Translator")
        source = gr.Textbox(label="English", lines=6, placeholder="Type something…")
        target = gr.Textbox(label="French", lines=6, interactive=False)
        gr.Button("Translate", variant="primary").click(
            translate, inputs=source, outputs=target
        )
    return demo


def main() -> None:
    build_ui().launch()
