import os, json, httpx
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, throttling
from pomi.apis.consultaSerializer import whatsAppIn
from pomi.apis.consultaServices import guardar_historico
from pomi.views.openia import gpt_response
import time
from dotenv import load_dotenv
import requests

# Cargar el el .env
load_dotenv()

RASA_URL = os.getenv("RASA_URL")

class ChatWebhookView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [throttling.UserRateThrottle]
    
    def post(self, request):
        payload = whatsAppIn(data=request.data)
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        
        sender = data["sender"]
        user_text = data["text"]
        celular = data["from_number"]
        
        # Medir tiempo de inicio
        start_time = time.time()
        
        #1. Enviar a Rasa
        body = {"sender_id": sender, "message": user_text}
        print(f"{RASA_URL}")
        
        
        # try:    
        #     with httpx.Client(timeout=360.0) as client:
        #         r = client.post(f"{RASA_URL}", json=body)
        #         r.raise_for_status()
        #         rasa_msg = r.json() # Rptas de Rasa
        # except httpx.HTTPError as e:
        #     print(f"detail: {str(e)}")
        #     return Response({"detail": str(e), "response": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
        
        try:
            r = requests.post(RASA_URL, json=body)
            r.raise_for_status()
            rasa_msg = r.json()  # Rptas de Rasa
            print(f"{r}")
            print(f"{rasa_msg}")
        except requests.RequestException as e:
            print(f"detail: {str(e)}")
            return Response({"detail": str(e), "response": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
        
        
        # Medir tiempo de fin
        end_time = time.time()
        response_time = end_time - start_time
        
        #  Comprobar si rasa_msg es un diccionario o una lista
        whatsapp_msgs = []
        if isinstance(rasa_msg, dict):
            # Si es un diccionario, procesarlo directamente
            if "response" in rasa_msg:
                whatsapp_msgs.append(rasa_msg["response"])
            elif "text" in rasa_msg:
                whatsapp_msgs.append(rasa_msg["text"])
            elif "custom" in rasa_msg and "gpt_response" in rasa_msg["custom"]:
                whatsapp_msgs.append(rasa_msg["custom"]["gpt_response"])
        else:
            # Si es una lista, iterar sobre ella
            for msg in rasa_msg:
                if isinstance(msg, dict):
                    if "text" in msg:
                        whatsapp_msgs.append(msg["text"])
                    elif "custom" in msg and "gpt_response" in msg["custom"]:
                        whatsapp_msgs.append(msg["custom"]["gpt_response"])
                    elif "response" in msg:
                        whatsapp_msgs.append(msg["response"])
                elif isinstance(msg, str):
                    # Si es un string, añadirlo directamente
                    whatsapp_msgs.append(msg)
            # Podrías agregar más condiciones para otros formatos aquí

        # Si no hay mensajes extraídos, proporcionar una respuesta predeterminada
        if not whatsapp_msgs:
            whatsapp_msgs = ["Lo siento, no pude procesar la respuesta."]

        final_msg = "\n".join(whatsapp_msgs)
        
        # Verificar si Rasa no pudo responder y usar OpenAI como fallback
        if "❌ No puedo responder ahora." in final_msg:
            print("🤖 Rasa no pudo responder, usando OpenAI...")
            
            # Crear un request mock para la función de OpenAI
            class MockRequest:
                def __init__(self, body_data):
                    self.body = json.dumps(body_data).encode('utf-8')
            
            # Preparar datos para OpenAI
            openai_data = {
                "query": user_text,
                "context": "",
                "usuario_id": sender
            }
            
            mock_request = MockRequest(openai_data)
            
            try:
                # Llamar a la función de OpenAI
                openai_response = gpt_response(mock_request)
                
                if openai_response.status_code == 200:
                    openai_content = json.loads(openai_response.content.decode('utf-8'))
                    if openai_content.get("status") == "ok":
                        final_msg = openai_content.get("response", final_msg)
                        print(f"✅ OpenAI respondió: {final_msg[:100]}...")
                    else:
                        print(f"❌ Error en respuesta de OpenAI: {openai_content}")
                else:
                    print(f"❌ Error HTTP de OpenAI: {openai_response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error al llamar OpenAI: {str(e)}")
                # Mantener la respuesta original de Rasa si falla OpenAI
        
        #3) Guarda consulta respuesta en un historico
        datos_feedbackgpt = {
            "celular": celular,
            "pregunta": user_text,
            "respuesta": final_msg,
            "tiempo": response_time
        }
        
        nuevo_registro = guardar_historico(datos_feedbackgpt)
        print(f"Respuesta de Rasa: {final_msg}")
        #3) Retornar la respuesta adaptada
        return Response(
            {"response": final_msg},
            status=status.HTTP_200_OK
        )
        