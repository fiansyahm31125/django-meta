import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.schema import HumanMessage
from .models import ChatHistory


# Ganti nilai berikut dengan milik Anda
ACCESS_TOKEN = 'EAAIOgPPHbKwBPcBLVQ4RxFe18paoEX1Q8XPHYXEh3LJ3BKg78YsZCl6Mv1zNBNyZBizSf6L7X6ooc92EfMNbTSnNv8zdo8JREMa3hw9hPd3lqZAif3qA4vNt82xN18BZCBI5Jrow7GeDnjrndbyniTeOEAvyNbzgr5lUlDMSDaSIxZBY3aZCGXZAY9tcEXPfLBEZAAScWl8BHRywmqd4RHHmzBFONqJTZB4LwEbHW6JJQ3N4ZD'
PHONE_NUMBER_ID = '809841558871302'
WHATSAPP_API_URL = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

def send_text_message(to_number: str, text_message: str):
    """
    Fungsi pembantu untuk mengirim pesan teks ke WhatsApp.
    """
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {
            "body": text_message
        }
    }
    
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(WHATSAPP_API_URL, headers=headers, json=payload)
        response.raise_for_status() # Akan memicu error untuk status code 4xx/5xx
        return {"success": True, "response_data": response.json()}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}

@csrf_exempt
@require_http_methods(["POST"])
def send_whatsapp(request):
    try:
        data = json.loads(request.body)
        to_number = data.get('to')
        text_message = data.get('text_message')

        if not to_number or not text_message:
            return JsonResponse({"error": "Missing 'to' or 'text_message' in request body"}, status=400)
        
        result = send_text_message(to_number, text_message)
        
        if result["success"]:
            return JsonResponse(result["response_data"], status=200)
        else:
            return JsonResponse({"error": result["error"]}, status=500)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except Exception as e:
        return JsonResponse({"error": "Internal Server Error", "detail": str(e)}, status=500)

@csrf_exempt
@require_http_methods(['POST'])
def get_whatsapp(request):
    data = json.loads(request.body)
    try:
        if 'entry' in data and data['entry'][0]['changes'][0]['value']['messages']:
            message_info = data['entry'][0]['changes'][0]['value']['messages'][0]
            from_id = message_info['from']
            message_body = message_info['text']['body']
            
            print(f"Pesan baru dari {from_id}: {message_body}")
            
            # Memanggil fungsi pembantu untuk mengirim balasan
            response_message = "Pesan Anda sudah diterima! 😊"
            send_text_message(from_id, response_message)

    except (KeyError, IndexError) as e:
        print(f"Format data webhook tidak dikenal atau tidak valid: {e}")
    
    # Respons wajib ke Meta
    return JsonResponse({"status": "ok"}, status=200)

@csrf_exempt
def langchain(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            prompt_text = data.get('prompt')
            image = data.get('image')
            session_id = data.get('session_id', 'default')

            if not prompt_text:
                return JsonResponse({'error': 'Prompt not found in request body'}, status=400)

            os.environ["GOOGLE_API_KEY"] = "AIzaSyCTr-BWtHHrym0DquNZvWlgoowx21wqAdc"

            # ✅ Ambil history dari DB untuk memory
            history_messages = ChatHistory.objects.filter(session_id=session_id)
            memory = ConversationBufferMemory(return_messages=True)
            for h in history_messages:
                if h.role == 'user':
                    memory.chat_memory.add_user_message(h.message)
                else:
                    memory.chat_memory.add_ai_message(h.message)

            # ✅ Buat LLM
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                temperature=0,
                max_tokens=None,
                timeout=None,
                max_retries=2
            )

            # ✅ Buat Conversation Chain
            conversation = ConversationChain(
                llm=llm,
                memory=memory,
                verbose=True
            )

            # ✅ Proses input
            if image:
                message = HumanMessage(content=[
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": image}
                ])
                hasil_jawaban = llm.invoke([message])
                response_text = hasil_jawaban.content
            else:
                response_text = conversation.run(prompt_text)

            # ✅ Simpan chat ke DB
            ChatHistory.objects.create(session_id=session_id, role='user', message=prompt_text)
            ChatHistory.objects.create(session_id=session_id, role='ai', message=response_text)

            # ✅ Response JSON
            response_data = {
                'message': f'Received prompt: {prompt_text}',
                'result': response_text,
                'session_id': session_id,
                'status': 'success'
            }
            return JsonResponse(response_data)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


# https://webhook.site/#!/view/5e75fb63-918a-462c-9071-ebe2f8d379cc/26401106-6c39-4f92-9f2c-108a1bbd5692/1

# https://receive-smss.com/sms/359885874351/#gsc.tab=0

# https://webhook.site/5e75fb63-918a-462c-9071-ebe2f8d379cc

# https://github.com/daveebbelaar/python-whatsapp-bot/tree/main?tab=readme-ov-file#step-3-configure-webhooks-to-receive-messages

