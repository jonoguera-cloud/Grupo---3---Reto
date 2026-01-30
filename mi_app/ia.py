import requests


def consultar_ia(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "phi3",
            "prompt": prompt,
            "stream": False
        }
    )
    return response.json()["response"]


def transcribe_audio(file_path, language='es'):
    """Intentar transcribir un archivo de audio.

    Estrategia:
    1) Si está configurada la variable de entorno OPENAI_API_KEY e instalado el paquete `openai`, intentar usar la API de OpenAI (whisper-1).
    2) Si falla, intentar usar la librería `whisper` local (si está instalada).
    3) Si todo falla, lanzar RuntimeError con instrucciones.
    """
    import os

    # Intento OpenAI (si está disponible)
    try:
        if os.getenv('OPENAI_API_KEY'):
            try:
                import openai
                openai.api_key = os.getenv('OPENAI_API_KEY')
                with open(file_path, 'rb') as af:
                    # SDKs pueden variar; intentar la llamada estándar
                    try:
                        resp = openai.Audio.transcribe("whisper-1", af)
                        # resp suele ser un dict con 'text'
                        if isinstance(resp, dict) and 'text' in resp:
                            return resp['text']
                        # Algunos SDKs devuelven un objeto con .text
                        return getattr(resp, 'text', '') or ''
                    except AttributeError:
                        # Intentar alternativa (por compatibilidad)
                        resp = openai.Transcription.create(file=af, model='whisper-1', language=language)
                        if isinstance(resp, dict) and 'text' in resp:
                            return resp['text']
            except Exception:
                # continuar al siguiente método
                pass
    except Exception:
        pass

    # Intento librería local `whisper`
    try:
        import whisper
        model = whisper.load_model('small')
        result = model.transcribe(file_path, language=language)
        return result.get('text', '')
    except Exception:
        pass

    raise RuntimeError(
        'No hay disponible ningún backend de transcripción. Instala `openai` y define OPENAI_API_KEY, o instala `whisper` localmente.'
    )
