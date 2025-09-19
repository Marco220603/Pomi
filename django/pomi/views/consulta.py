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
            
            print(f"🔄 Enviando request a Rasa: {RASA_URL}")
            print(f"📦 Body enviado: {body}")
            
            r = requests.post(
                RASA_URL, 
                json=body, 
                timeout=30  # Timeout de 30 segundos
            )
            r.raise_for_status()
            
            # Validar que la respuesta no esté vacía
            if not r.content:
                print("❌ Respuesta vacía de Rasa")
                rasa_msg = []
            else:
                try:
                    rasa_msg = r.json()  # Rptas de Rasa
                    print(f"✅ Status Code: {r.status_code}")
                    print(f"📨 Respuesta de Rasa: {rasa_msg}")
                except json.JSONDecodeError as json_error:
                    print(f"❌ Error al parsear JSON de Rasa: {json_error}")
                    print(f"📄 Contenido crudo: {r.text[:200]}...")
                    rasa_msg = []
                    
        except requests.Timeout:
            print("⏰ Timeout al conectar con Rasa")
            return Response(
                {"detail": "Timeout al conectar con el servicio de chat", "response": "❌ El servicio está tardando más de lo esperado. Intenta nuevamente."}, 
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )
        except requests.ConnectionError:
            print("🔌 Error de conexión con Rasa")
            return Response(
                {"detail": "Error de conexión con el servicio de chat", "response": "❌ No se puede conectar con el servicio de chat. Intenta más tarde."}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except requests.RequestException as e:
            print(f"❌ Error de request: {str(e)}")
            return Response(
                {"detail": str(e), "response": "❌ Error al procesar tu consulta. Intenta nuevamente."}, 
                status=status.HTTP_502_BAD_GATEWAY
            )
        
        
        # Medir tiempo de fin
        end_time = time.time()
        response_time = end_time - start_time
        
        # Procesar respuesta de Rasa de forma más robusta
        whatsapp_msgs = []
        
        # Validar que rasa_msg no sea None o vacío
        if not rasa_msg:
            print("⚠️ Respuesta de Rasa vacía o None")
            whatsapp_msgs = ["❌ No puedo responder ahora."]
        elif isinstance(rasa_msg, dict):
            print("📝 Procesando respuesta como diccionario")
            # Si es un diccionario, procesarlo directamente
            if "response" in rasa_msg and rasa_msg["response"]:
                whatsapp_msgs.append(str(rasa_msg["response"]))
            elif "text" in rasa_msg and rasa_msg["text"]:
                whatsapp_msgs.append(str(rasa_msg["text"]))
            elif "custom" in rasa_msg and isinstance(rasa_msg["custom"], dict) and "gpt_response" in rasa_msg["custom"]:
                whatsapp_msgs.append(str(rasa_msg["custom"]["gpt_response"]))
            else:
                print(f"⚠️ Estructura de diccionario no reconocida: {rasa_msg}")
                whatsapp_msgs = ["❌ No puedo responder ahora."]
        elif isinstance(rasa_msg, list):
            print(f"📝 Procesando respuesta como lista con {len(rasa_msg)} elementos")
            # Si es una lista, iterar sobre ella
            for i, msg in enumerate(rasa_msg):
                print(f"  Elemento {i}: {type(msg)} - {msg}")
                if isinstance(msg, dict):
                    if "text" in msg and msg["text"]:
                        whatsapp_msgs.append(str(msg["text"]))
                    elif "custom" in msg and isinstance(msg["custom"], dict) and "gpt_response" in msg["custom"]:
                        whatsapp_msgs.append(str(msg["custom"]["gpt_response"]))
                    elif "response" in msg and msg["response"]:
                        whatsapp_msgs.append(str(msg["response"]))
                elif isinstance(msg, str) and msg.strip():
                    # Si es un string no vacío, añadirlo directamente
                    whatsapp_msgs.append(msg.strip())
        elif isinstance(rasa_msg, str):
            print("📝 Procesando respuesta como string")
            if rasa_msg.strip():
                whatsapp_msgs.append(rasa_msg.strip())
            else:
                whatsapp_msgs = ["❌ No puedo responder ahora."]
        else:
            print(f"⚠️ Tipo de respuesta no reconocido: {type(rasa_msg)} - {rasa_msg}")
            whatsapp_msgs = ["❌ No puedo responder ahora."]

        # Si no hay mensajes extraídos después de todo el procesamiento
        if not whatsapp_msgs or all(not msg.strip() for msg in whatsapp_msgs):
            print("⚠️ No se pudieron extraer mensajes válidos")
            whatsapp_msgs = ["❌ No puedo responder ahora."]

        # Limpiar mensajes vacíos y duplicados
        whatsapp_msgs = [msg.strip() for msg in whatsapp_msgs if msg and msg.strip()]
        whatsapp_msgs = list(dict.fromkeys(whatsapp_msgs))  # Remover duplicados manteniendo orden
        
        final_msg = "\n".join(whatsapp_msgs)
        print(f"🔍 Mensaje final de Rasa: '{final_msg}'")
        print(f"📊 Longitud del mensaje: {len(final_msg)} caracteres")
        
        # Verificar si Rasa no pudo responder y usar OpenAI como fallback
        # Verificamos múltiples variaciones del mensaje de error
        error_patterns = [
            "❌ no puedo responder ahora",
            "no puedo responder ahora",
            "no puedo responder",
            "lo siento, no pude procesar",
            "no entiendo",
            "disculpa, no comprendo",
            "no sé cómo ayudarte",
            "fallback",
            "default response",
            "acción default"
        ]
        
        # Normalizar el mensaje para comparación
        final_msg_normalized = final_msg.lower().strip()
        
        # Verificar patrones de error
        should_use_openai = any(
            pattern in final_msg_normalized 
            for pattern in error_patterns
        )
        
        # También verificar si el mensaje es demasiado corto o genérico
        if not should_use_openai:
            generic_responses = [
                "ok", "bien", "sí", "no", "gracias", "hola", "adiós",
                "entiendo", "comprendo", "perfecto", "claro"
            ]
            if (
                len(final_msg_normalized) < 10 or  # Muy corto
                final_msg_normalized in generic_responses or  # Muy genérico
                final_msg_normalized.startswith("acción ") or
                final_msg_normalized.startswith("action ")
            ):
                should_use_openai = True
                print(f"⚠️ Mensaje demasiado genérico o corto, usando OpenAI")
        
        print(f"🤖 ¿Debería usar OpenAI? {should_use_openai}")
        print(f"🎯 Patrones encontrados: {[p for p in error_patterns if p in final_msg_normalized]}")
        
        if should_use_openai:
            print("🤖 Rasa no pudo responder, usando OpenAI como fallback...")
            
            # Crear un request mock para la función de OpenAI
            class MockRequest:
                def __init__(self, body_data):
                    self.body = json.dumps(body_data).encode('utf-8')
            
            # Preparar datos para OpenAI con más contexto
            openai_data = {
                "query": user_text,
                "context": f"El usuario escribió: '{user_text}'. Rasa respondió: '{final_msg}' pero necesitamos una mejor respuesta.",
                "usuario_id": sender
            }
            
            print(f"📤 Enviando a OpenAI: {openai_data}")
            mock_request = MockRequest(openai_data)
            
            try:
                # Llamar a la función de OpenAI con timeout
                openai_start_time = time.time()
                openai_response = gpt_response(mock_request)
                openai_response_time = time.time() - openai_start_time
                
                print(f"⏱️ OpenAI respondió en {openai_response_time:.2f} segundos")
                print(f"📊 Status Code OpenAI: {openai_response.status_code}")
                
                if openai_response.status_code == 200:
                    try:
                        openai_content = json.loads(openai_response.content.decode('utf-8'))
                        print(f"📨 Respuesta completa de OpenAI: {openai_content}")
                        
                        if openai_content.get("status") == "ok":
                            openai_text = openai_content.get("response", "").strip()
                            if openai_text and len(openai_text) > 5:  # Validar que no esté vacía
                                final_msg = openai_text
                                print(f"✅ OpenAI respondió exitosamente: {final_msg[:100]}...")
                            else:
                                print(f"⚠️ Respuesta de OpenAI vacía o muy corta: '{openai_text}'")
                        else:
                            print(f"❌ OpenAI retornó error: {openai_content}")
                    except json.JSONDecodeError as e:
                        print(f"❌ Error al parsear JSON de OpenAI: {e}")
                        print(f"📄 Contenido crudo: {openai_response.content.decode('utf-8')[:200]}...")
                elif openai_response.status_code == 429:
                    print("⏰ OpenAI: Rate limit alcanzado")
                elif openai_response.status_code >= 500:
                    print(f"🔧 OpenAI: Error del servidor ({openai_response.status_code})")
                else:
                    print(f"❌ Error HTTP de OpenAI: {openai_response.status_code}")
                    print(f"📄 Contenido: {openai_response.content.decode('utf-8')[:200]}...")
                    
            except Exception as e:
                print(f"❌ Excepción al llamar OpenAI: {str(e)}")
                print(f"🔍 Tipo de error: {type(e).__name__}")
                # Mantener la respuesta original de Rasa si falla OpenAI
            
            print(f"🏁 Mensaje final después de fallback: '{final_msg}'")
        
        # Validaciones finales antes de guardar
        if not final_msg or not final_msg.strip():
            final_msg = "❌ Lo siento, no pude procesar tu consulta en este momento. Por favor, intenta reformular tu pregunta."
            print("⚠️ Mensaje final vacío, usando respuesta de emergencia")
        
        # Limitar longitud del mensaje si es muy largo
        if len(final_msg) > 2000:
            final_msg = final_msg[:1997] + "..."
            print("✂️ Mensaje truncado por ser muy largo")
        
        print(f"💾 Mensaje final para guardar: '{final_msg}'")
        print(f"⏱️ Tiempo total de procesamiento: {round(response_time, 4)} segundos")
        
        # Guardar consulta y respuesta en el histórico
        try:
            datos_feedbackgpt = {
                "celular": celular,
                "pregunta": user_text,
                "respuesta": final_msg,
                "tiempo": round(response_time, 4)  # Limitar a 4 decimales
            }
            
            nuevo_registro = guardar_historico(datos_feedbackgpt)
            print(f"✅ Registro guardado en histórico: ID {nuevo_registro.id if hasattr(nuevo_registro, 'id') else 'N/A'}")
            
        except Exception as e:
            print(f"❌ Error al guardar en histórico: {str(e)}")
            # Continuar con la respuesta aunque falle el guardado
        
        print(f"🎯 Respuesta final enviada al usuario: {final_msg}")
        
        # Retornar la respuesta adaptada
        return Response(
            {
                "response": final_msg,
                "processing_time": round(response_time, 4),
                "timestamp": timezone.now().isoformat()
            },
            status=status.HTTP_200_OK
        )
        