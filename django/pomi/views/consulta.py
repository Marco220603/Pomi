import os, json, httpx
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, throttling
from pomi.apis.consultaSerializer import whatsAppIn
from pomi.apis.consultaServices import guardar_historico
import time
from dotenv import load_dotenv
import requests
from openai import OpenAI

# Cargar el el .env
load_dotenv()

RASA_URL = os.getenv("RASA_URL")

def call_openai_directly(query, context="", usuario_id="anonimo", model="ft:gpt-4o-mini-2024-07-18:personal:pomififvrs:BnAyJv1u"):
    """
    Función auxiliar para llamar directamente a OpenAI sin pasar por la vista de Django
    """
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ No se encontró OPENAI_API_KEY en variables de entorno")
            return None
            
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
        
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.3
        )

        gpt_text = response.choices[0].message.content
        print(f"✅ GPT generó respuesta para {usuario_id}")
        
        return {
            "status": "ok",
            "response": gpt_text
        }

    except Exception as e:
        import traceback
        print("❌ Error GPT:\n", traceback.format_exc())
        return {
            "error": str(e),
            "status": "error"
        }

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
        print(f"🔄 RASA_URL: {RASA_URL}")
        
        # Variable para controlar si usar OpenAI
        use_openai_fallback = False
        rasa_msg = []
        rasa_error_detail = ""
        
        try:
            print(f"🔄 Enviando request a Rasa: {RASA_URL}")
            print(f"📦 Body enviado: {body}")
            
            r = requests.post(
                RASA_URL, 
                json=body, 
                timeout=5  # Timeout de 30 segundos
            )
            r.raise_for_status()
            
            # Validar que la respuesta no esté vacía
            if not r.content:
                print("❌ Respuesta vacía de Rasa")
                use_openai_fallback = True
                rasa_error_detail = "Respuesta vacía de Rasa"
            else:
                try:
                    rasa_msg = r.json()  # Rptas de Rasa
                    print(f"✅ Status Code: {r.status_code}")
                    print(f"📨 Respuesta de Rasa: {rasa_msg}")
                except json.JSONDecodeError as json_error:
                    print(f"❌ Error al parsear JSON de Rasa: {json_error}")
                    print(f"📄 Contenido crudo: {r.text[:200]}...")
                    use_openai_fallback = True
                    rasa_error_detail = f"Error al parsear JSON: {json_error}"
                    
        except requests.Timeout:
            print("⏰ Timeout al conectar con Rasa - usando OpenAI como fallback")
            use_openai_fallback = True
            rasa_error_detail = "Timeout al conectar con Rasa"
            
        except requests.ConnectionError:
            print("🔌 Error de conexión con Rasa - usando OpenAI como fallback")
            use_openai_fallback = True
            rasa_error_detail = "Error de conexión con Rasa"
            
        except requests.RequestException as e:
            print(f"❌ Error de request con Rasa: {str(e)} - usando OpenAI como fallback")
            use_openai_fallback = True
            rasa_error_detail = f"Error de request: {str(e)}"
        
        
        # Medir tiempo de fin de Rasa
        end_time = time.time()
        response_time = end_time - start_time
        
        # Procesar respuesta de Rasa solo si no hubo error de conexión
        whatsapp_msgs = []
        final_msg = ""
        
        if not use_openai_fallback:
            # Procesar respuesta de Rasa de forma más robusta
            if not rasa_msg:
                print("⚠️ Respuesta de Rasa vacía o None")
                use_openai_fallback = True
            elif isinstance(rasa_msg, dict):
                print("📝 Procesando respuesta como diccionario")
                if "response" in rasa_msg and rasa_msg["response"]:
                    whatsapp_msgs.append(str(rasa_msg["response"]))
                elif "text" in rasa_msg and rasa_msg["text"]:
                    whatsapp_msgs.append(str(rasa_msg["text"]))
                elif "custom" in rasa_msg and isinstance(rasa_msg["custom"], dict) and "gpt_response" in rasa_msg["custom"]:
                    whatsapp_msgs.append(str(rasa_msg["custom"]["gpt_response"]))
                else:
                    print(f"⚠️ Estructura de diccionario no reconocida: {rasa_msg}")
                    use_openai_fallback = True
            elif isinstance(rasa_msg, list):
                print(f"📝 Procesando respuesta como lista con {len(rasa_msg)} elementos")
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
                        whatsapp_msgs.append(msg.strip())
            elif isinstance(rasa_msg, str):
                print("📝 Procesando respuesta como string")
                if rasa_msg.strip():
                    whatsapp_msgs.append(rasa_msg.strip())
                else:
                    use_openai_fallback = True
            else:
                print(f"⚠️ Tipo de respuesta no reconocido: {type(rasa_msg)}")
                use_openai_fallback = True

            # Limpiar mensajes vacíos y duplicados
            whatsapp_msgs = [msg.strip() for msg in whatsapp_msgs if msg and msg.strip()]
            whatsapp_msgs = list(dict.fromkeys(whatsapp_msgs))
            
            if whatsapp_msgs:
                final_msg = "\n".join(whatsapp_msgs)
                print(f"🔍 Mensaje final de Rasa: '{final_msg}'")
                
                # Verificar patrones de error en la respuesta
                error_patterns = [
                    "❌ no puedo responder ahora", "no puedo responder ahora",
                    "no puedo responder", "lo siento, no pude procesar",
                    "no entiendo", "disculpa, no comprendo",
                    "no sé cómo ayudarte", "fallback", "default response", "acción default"
                ]
                
                final_msg_normalized = final_msg.lower().strip()
                
                if any(pattern in final_msg_normalized for pattern in error_patterns):
                    print(f"⚠️ Respuesta de Rasa contiene patrón de error")
                    use_openai_fallback = True
                
                # Verificar si es muy genérico o corto
                generic_responses = ["ok", "bien", "sí", "no", "gracias", "hola", "adiós"]
                if len(final_msg_normalized) < 10 or final_msg_normalized in generic_responses:
                    print(f"⚠️ Mensaje demasiado genérico o corto")
                    use_openai_fallback = True
            else:
                print("⚠️ No se pudieron extraer mensajes válidos de Rasa")
                use_openai_fallback = True
        
        # Si hay que usar OpenAI como fallback
        if use_openai_fallback:
            print(f"🤖 Usando OpenAI como fallback. Razón: {rasa_error_detail or 'Respuesta inadecuada de Rasa'}")
            
            openai_context = f"El usuario preguntó: '{user_text}'."
            if rasa_error_detail:
                openai_context += f" Rasa falló: {rasa_error_detail}"
            
            try:
                openai_start_time = time.time()
                openai_response = call_openai_directly(
                    query=user_text,
                    context=openai_context,
                    usuario_id=sender
                )
                openai_response_time = time.time() - openai_start_time
                
                print(f"⏱️ OpenAI respondió en {openai_response_time:.2f} segundos")
                print(f"📨 Respuesta de OpenAI: {openai_response}")
                
                if openai_response and openai_response.get("status") == "ok":
                    openai_text = openai_response.get("response", "").strip()
                    if openai_text and len(openai_text) > 5:
                        final_msg = openai_text
                        print(f"✅ OpenAI respondió exitosamente")
                    else:
                        final_msg = "❌ Lo siento, no pude procesar tu consulta. Intenta reformular tu pregunta."
                else:
                    final_msg = "❌ Lo siento, no pude procesar tu consulta. Intenta más tarde."
                    
            except Exception as e:
                print(f"❌ Excepción en OpenAI: {str(e)}")
                final_msg = "❌ Lo siento, no pude procesar tu consulta. Por favor, intenta nuevamente."
        
        # Validaciones finales
        if not final_msg or not final_msg.strip():
            final_msg = "❌ Lo siento, no pude procesar tu consulta en este momento."
        
        # Limpiar y formatear el mensaje correctamente
        final_msg = final_msg.strip()
        
        # Reemplazar múltiples saltos de línea por uno solo
        import re
        final_msg = re.sub(r'\n{3,}', '\n\n', final_msg)
        
        # Eliminar espacios al inicio y final de cada línea
        final_msg = '\n'.join(line.strip() for line in final_msg.split('\n'))
        
        if len(final_msg) > 2000:
            final_msg = final_msg[:1997] + "..."
        
        # Calcular tiempo total
        total_time = time.time() - start_time
        
        print(f"💾 Mensaje final: '{final_msg[:100]}...'")
        print(f"⏱️ Tiempo total: {round(total_time, 4)} segundos")
        
        # Guardar consulta y respuesta en el histórico
        try:
            datos_feedbackgpt = {
                "celular": celular,
                "sender_id": sender,
                "pregunta": user_text,
                "respuesta": final_msg,
                "tiempo": round(total_time, 4)
            }
            
            nuevo_registro = guardar_historico(datos_feedbackgpt)
            print(f"✅ Registro guardado: ID {nuevo_registro.id if hasattr(nuevo_registro, 'id') else 'N/A'}")
            
        except Exception as e:
            print(f"❌ Error al guardar: {str(e)}")
        
        # Retornar la respuesta adaptada
        return Response(
            {
                "response": final_msg,
                "processing_time": round(total_time, 4),
                "timestamp": timezone.now().isoformat(),
                "fallback_used": use_openai_fallback
            },
            status=status.HTTP_200_OK
        )
        