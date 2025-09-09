import os
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import ChatHistory
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
from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings

import easyocr
import base64
from io import BytesIO
from PIL import Image
import docx
from PyPDF2 import PdfReader


@csrf_exempt
def langchain(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            prompt_text = data.get('prompt')
            image = data.get('image')
            session_id = data.get('session_id', 'default')
            type=data.get('type')
            mime_type=data.get('mime_type')

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
                    {
                        "type": type,
                        "source_type": "base64",
                        "mime_type": mime_type, # ganti sesuai jenis gambar
                        "data": image,
                    }
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



# Token akses harus disimpan di environment variables untuk keamanan
GRAPH_API_TOKEN = 'EAAIOgPPHbKwBPfpf5ZCSRZA5JB1mCCOQj3oalZAUdItaHZCqxQ4B1c2h5f1FD1nZBRZAFsN8ZA3WfpHaqfrfVs4Ezne2PRuy7d0ciUEQeE8BPER707G9njyCX5q3f9MRvT0zmXkVEwGY6Kb6pRLBo95TrRQ99ZB2F3rVd7pxYKDvA93kn3PWEFZCYpqJBP2RumRL235bySlUajPWqs5T9kbQCli4xr81iUnF3yM24xrjixhsZD'
PHONE_NUMBER_ID = '809841558871302'
WHATSAPP_API_URL = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"
WEBHOOK_VERIFY_TOKEN="arif"

@csrf_exempt
@require_http_methods(["POST"])
def send_whatsapp(request):
    try:
        data = json.loads(request.body)
        
        # Ekstrak 'to' dan 'message' dari body request
        to_number = data.get('to')
        text_message = data.get('message')

        if not to_number or not text_message:
            return JsonResponse({"error": "Missing 'to' or 'message' in request body"}, status=400)

        # Payload untuk mengirim pesan teks
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {
                "body": text_message
            }
        }
        
        headers = {
            'Authorization': f'Bearer {GRAPH_API_TOKEN}',
            'Content-Type': 'application/json'
        }

        # Mengirim permintaan POST ke API WhatsApp
        response = requests.post(WHATSAPP_API_URL, headers=headers, json=payload)
        
        return JsonResponse(response.json(), status=response.status_code)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": str(e)}, status=500)
    except Exception as e:
        return JsonResponse({"error": "Internal Server Error", "detail": str(e)}, status=500)


@csrf_exempt
def get_whatsapp(request):
    if request.method == 'GET':
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        print("Connecting Process")

        if mode and token and mode == 'subscribe' and token == WEBHOOK_VERIFY_TOKEN:
            return HttpResponse(challenge, status=200)
        else:
            return HttpResponse('Token verifikasi tidak valid', status=403)
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            # Logika untuk memproses pesan WhatsApp
            if 'entry' in data and data['entry'][0]['changes'][0]['value']['messages']:
                message_info = data['entry'][0]['changes'][0]['value']['messages'][0]
                print(f"Isi message Info/Data: {message_info}")
                from_id = message_info['from']
                message_type = message_info['type']

                message_body=None
                base64_image=None
                mime_type=None

                if message_type == 'text':
                    # Jika pesan adalah teks, ambil 'body'
                    message_body = message_info['text']['body']
                    print(f"Pesan teks baru dari {from_id}: {message_body}")
                elif message_type == 'image':
                    # Jika pesan adalah gambar, ambil 'id' dan 'caption'
                    media_id = message_info['image']['id']
                    caption = message_info['image'].get('caption', 'Tidak ada caption')
                    mime_type = message_info['image'].get('mime_type', 'image/jpeg')
                    
                    print(f"Pesan gambar baru dari {from_id} dengan Media ID: {media_id}")
                    print(f"Caption: {caption}")
                    # Unduh gambar menggunakan fungsi helper
                    base64_image=read_image(media_id)
                    if base64_image != None:
                        message_body="Coba Pahami gambar ini dan respon jawabannya ke customer gimana berdasar chat sebelumnya,buat jawabannya singkat,padat,,pilih 1 opsi saja!,Customer service:....." 
                elif message_type == 'document':
                    media_id = message_info['document']['id']
                    mime_type = message_info['document'].get('mime_type', 'application/octet-stream')
                    filename = message_info['document'].get('filename', 'unknown')

                    print(f"Pesan dokumen baru dari {from_id} dengan Media ID: {media_id}")
                    print(f"Filename: {filename}, MimeType: {mime_type}")

                    base64_image=read_image(media_id)
                    if base64_image != None:
                        message_body="Coba Pahami gambar ini dan respon jawabannya ke customer gimana berdasar chat sebelumnya,buat jawabannya singkat,padat,,pilih 1 opsi saja!,Customer service:....." 


                    # # ✅ Unduh file (base64)
                    # base64_doc = read_image(media_id)  

                    # # ✅ Simpan file sementara
                    # file_path = os.path.join(settings.MEDIA_ROOT, filename)
                    # with open(file_path, "wb") as f:
                    #     f.write(base64.b64decode(base64_doc))

                    # # ✅ Konversi dokumen ke teks
                    # extracted_text = extract_text_from_document(file_path, mime_type)

                    # print(f"Teks hasil ekstraksi: {extracted_text[:200]}...")

                    # if extracted_text!=None:
                    #     message_body=extracted_text

                question={
                    "session_id": from_id,
                    "prompt": message_body,
                    "image": base64_image,
                    "type":message_type,
                    "mime_type":mime_type
                }
                response=requests.post("http://127.0.0.1:8000/langchain/index", json=question)

                payload = {
                    "messaging_product": "whatsapp",
                    "to": from_id,
                    "type": "text",
                    "text": {
                        "body": response.json().get("result")
                    }
                }
            
            headers = {
                'Authorization': f'Bearer {GRAPH_API_TOKEN}',
                'Content-Type': 'application/json'
            }

            # Mengirim permintaan POST ke API WhatsApp
            response = requests.post(WHATSAPP_API_URL, headers=headers, json=payload)

            return HttpResponse(status=200)

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error saat memproses data: {e}")
            return HttpResponse(status=400)

    return HttpResponse(status=405) # Metode tidak diizinkan

def conversation(request,user):
    if request.method == "GET":
        try:
            # Menggunakan .all() untuk mengambil SEMUA objek ChatHistory
            # Menggunakan .order_by('-timestamp') untuk mengurutkan dari yang terbaru
            chathistorys = ChatHistory.objects.filter(session_id=user).order_by('timestamp')
        except ChatHistory.DoesNotExist:
            chathistorys = [] # Jika tidak ada data, kembalikan list kosong

        # Meneruskan data (chathistorys) ke template HTML
        context = {
            'chathistorys': chathistorys
        }
        
        return render(request, 'conversation.html', context)
    else:
        try:
            user_message = request.POST.get("user_message") 
            # question={
            #     "session_id": user,
            #     "prompt": user_message,
            #     "image": None
            # }
            # response=requests.post("http://127.0.0.1:8000/langchain/index", json=question)
            # payload = {
            #     "messaging_product": "whatsapp",
            #     "to": user,
            #     "type": "text",
            #     "text": {
            #         "body": response.json().get("result")
            #     }
            # }
            payload = {
                "messaging_product": "whatsapp",
                "to": user,
                "type": "text",
                "text": {
                    "body": user_message
                }
            }
            headers = {
                'Authorization': f'Bearer {GRAPH_API_TOKEN}',
                'Content-Type': 'application/json'
            }

            # Mengirim permintaan POST ke API WhatsApp
            response = requests.post(WHATSAPP_API_URL, headers=headers, json=payload)

            ChatHistory.objects.create(session_id=user, role='ai', message=user_message)

            # back to conver
            try:
                # Menggunakan .all() untuk mengambil SEMUA objek ChatHistory
                # Menggunakan .order_by('-timestamp') untuk mengurutkan dari yang terbaru
                chathistorys = ChatHistory.objects.all().order_by('timestamp')
            except ChatHistory.DoesNotExist:
                chathistorys = [] # Jika tidak ada data, kembalikan list kosong

            # Meneruskan data (chathistorys) ke template HTML
            context = {
                'chathistorys': chathistorys
            }
            
            return render(request, 'conversation.html', context)
        
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error saat memproses data: {e}")
            return HttpResponse(status=400)
        

def read_ocr(base64_image):
    # Step 1: Decode base64 to image
    image_data = base64.b64decode(base64_image)
    image = Image.open(BytesIO(image_data))

    # Step 2: Simpan sementara (optional, kalau EasyOCR butuh file)
    image.save("temp_image.jpg")

    # Step 3: Jalankan OCR dengan EasyOCR
    reader = easyocr.Reader(['en'])  # atau ['id'] untuk bahasa Indonesia
    results = reader.readtext("temp_image.jpg")

    # Step 4: Gabungkan hasil teks
    text = "\n".join([result[1] for result in results])

    print("Hasil OCR:")
    print(text)

    return text
        

def read_image(media_id):
    """
    Mengunduh gambar dari WhatsApp API menggunakan media_id.
    """
    headers = {
        "Authorization": f"Bearer {GRAPH_API_TOKEN}"
    }
    
    try:
        # Step 1: Dapatkan URL unduhan
        response_metadata = requests.get(f"https://graph.facebook.com/v16.0/{media_id}", headers=headers)
        response_metadata.raise_for_status()
        download_url = response_metadata.json().get('url')

        if not download_url:
            print(f"Gagal mendapatkan URL unduhan untuk Media ID: {media_id}")
            return

        # Step 2: Unduh file gambar
        response_image = requests.get(download_url, headers=headers)
        response_image.raise_for_status()

        # # Step 3: Simpan file ke disk
        # file_name = f"gambar_{media_id}.jpg"
        # with open(file_name, 'wb') as f:
        #     f.write(response_image.content)
            
        # print(f"Gambar berhasil diunduh dan disimpan sebagai {file_name}")
        # Mengubah konten gambar menjadi Base64
        # print(f"ini response {response_image.content}")
        base64_image_content = base64.b64encode(response_image.content).decode('utf-8')

        # print("Konten gambar dalam format Base64 berhasil dibuat.")
        # # Anda bisa cetak sebagian stringnya untuk verifikasi
        # print(f"Base64 string (sebagian): {base64_image_content[:50]}...")
        # return read_ocr(base64_image_content)
        return base64_image_content

    except requests.exceptions.HTTPError as err:
        print(f"Kesalahan HTTP saat mengunduh gambar: {err}")
    except Exception as e:
        print(f"Kesalahan umum saat mengunduh gambar: {e}")


def extract_text_from_document(file_path, mime_type):
    if mime_type == 'application/pdf':
        # Ekstraksi PDF
        with open(file_path, "rb") as pdf_file:
            reader = PdfReader(pdf_file)
            return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    elif mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword']:
        # Ekstraksi DOCX
        doc = docx.Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])
    elif mime_type == 'text/plain':
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return None

def list_conversation(request):
    if request.method == "GET":
        listchats = ChatHistory.objects.values_list('session_id', flat=True)

        # Ubah ke set untuk menghilangkan duplikat, lalu kembali ke list jika perlu
        unique_session_ids_set = set(listchats)

        # Konversi kembali ke list jika diperlukan
        unique_session_id_list = list(unique_session_ids_set)


        context = {
            'listchats': unique_session_id_list
        }
        return render(request,'whatsapp/listchat.html',context)
    else:
        pass
