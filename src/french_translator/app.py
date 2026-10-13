import json
import os

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionToolParam

load_dotenv()

SYSTEM_PROMPT_ENGLISH_TO_FRENCH = (
    """
    You are a translator. Translate the user's text into French and provide the english like pronunciation of the French translation.
    Do not write the pronunciation yourself: always get it by calling the get_pronunciation tool with your French translation.
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
    Do not write the pronunciation yourself: always get it by calling the get_pronunciation tool with the input French text.
    You should respond in JSON with no commentary as in this example:
    
    {
        "translation": "Hello, how are you?",
        "pronunciation": "bohn-zhoor, koh-mahn sah vah?"
    }
    """
)

PRONUNCIATION_SYSTEM_PROMPT = (
    "You are given a French text. Reply with only its english like phonetic "
    "pronunciation, for example 'bohn-zhoor, koh-mahn sah vah?', and no commentary."
)

PRONUNCIATION_TOOL: ChatCompletionToolParam = {
    "type": "function",
    "function": {
        "name": "get_pronunciation",
        "description": "Get the english like phonetic pronunciation of a French text.",
        "parameters": {
            "type": "object",
            "properties": {
                "french_text": {
                    "type": "string",
                    "description": "The French text to pronounce",
                },
            },
            "required": ["french_text"],
            "additionalProperties": False,
        },
    },
}

def check_api_key() -> None:
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError(
            "The OPENAI_API_KEY environment variable is not set. "
            "Please set it to your OpenAI API key."
        )
    if not os.environ.get("GEMINI_API_KEY"):
        raise ValueError(
            "The GEMINI_API_KEY environment variable is not set. "
            "Please set it to your Gemini API key."
        )

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

def set_up_client() -> tuple[OpenAI, OpenAI]:
    check_api_key()
    return (
        OpenAI(api_key=os.environ["OPENAI_API_KEY"]),
        OpenAI(api_key=os.environ["GEMINI_API_KEY"], base_url=GEMINI_BASE_URL),
    )

client, gemini_client = set_up_client()

def get_pronunciation(french_text: str) -> str:
    response = gemini_client.chat.completions.create(
        model="gemini-3.8-flash",
        messages=[
            {"role": "system", "content": PRONUNCIATION_SYSTEM_PROMPT},
            {"role": "user", "content": french_text},
        ],
    )
    return (response.choices[0].message.content or '').strip()


def handle_tool_calls(message) -> list[dict]:
    results = []
    for tool_call in message.tool_calls:
        arguments = json.loads(tool_call.function.arguments)
        if tool_call.function.name == "get_pronunciation":
            content = get_pronunciation(arguments.get("french_text", ""))
        else:
            content = f"Unknown tool: {tool_call.function.name}"
        print(f"Tool result: {content}")
        results.append({"role": "tool", "tool_call_id": tool_call.id, "content": content})
    return results


def translate(text: str, lang: str):
    if not text.strip():
        return "", None

    messages: list = [
        {"role": "system", "content": SYSTEM_PROMPT_ENGLISH_TO_FRENCH if lang == "English" else SYSTEM_PROMPT_FRENCH_TO_ENGLISH},
        {"role": "user", "content": text},
    ]

    def ask_openai():
        return client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=[PRONUNCIATION_TOOL],
            response_format={"type": "json_object"}
        )

    response = ask_openai()
    while response.choices[0].finish_reason == "tool_calls":
        tool_request = response.choices[0].message
        print(f"Tool request choice: {response.choices[0]}")
        messages.append(tool_request)
        messages.extend(handle_tool_calls(tool_request))
        response = ask_openai()

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
