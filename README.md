# French Translator

A small web app that translates English text into French, shows how to pronounce it, and reads the translation aloud.

Type English into the input box and click **Translate**. The app shows:

- the French translation
- an English-style pronunciation guide (e.g. *bohn-zhoor, koh-mahn sah vah?*)
- an audio clip of the translation, which plays automatically

It uses OpenAI models:

- `gpt-4o-mini` for the translation and pronunciation guide
- `gpt-4o-mini-tts` for speech

The web interface is built with [Gradio](https://www.gradio.app/).

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- An OpenAI API key

## Setup

1. Install dependencies:

   ```sh
   uv sync
   ```

2. Create a `.env` file in the project root with your API key:

   ```sh
   OPENAI_API_KEY=sk-...
   ```

   The app loads this file on startup and exits with an error if the key is missing.

## Running

```sh
uv run python -m french_translator
```

Then open http://127.0.0.1:7860 in your browser.

## Project layout

```
src/french_translator/
├── __main__.py   # entry point: python -m french_translator
└── app.py        # translation, pronunciation, text-to-speech and Gradio UI
```
