from openai import OpenAI
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from django.http import JsonResponse
import json
import os

api_key = os.getenv("OPENAI_API_KEY")

@csrf_exempt
@api_view(['POST'])
def gpt_response(request):
    try:
        data = json.loads(request.body)
        query = data.get("query", "")
        context = data.get("context", "")
        usuario_id = data.get("usuario_id", "anonimo")
        model = data.get("model", "ft:gpt-4o-mini-2024-07-18:personal:pomififvrs:BnAyJv1u")

        messages = [
            {
                "role": "system",
                "content": (
                    "Responde como un asistente académico de la Universidad Peruana de Ciencias Aplicadas (UPC), "
                    "especializado exclusivamente en temas académicos y administrativos de la UPC."
                )
            },
            {
                "role": "user",
                "content": f"{context}\n\n{query}" if context else query
            }
        ]
        client = OpenAI()  # Inicializa cliente
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3
        )

        gpt_text = response.choices[0].message.content

        print(f"✅ GPT generó respuesta para {usuario_id}")

        return JsonResponse({
            "status": "ok",
            "response": gpt_text
        })

    except Exception as e:
        import traceback
        print("❌ Error GPT:\n", traceback.format_exc())
        return JsonResponse({"error": str(e)}, status=500)