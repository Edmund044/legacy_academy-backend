import requests

def send_whatsapp_notification(phone_number: str, message: str):
    url = "https://graph.facebook.com/v18.0/100614629341688/messages"

    headers = {
        "Authorization": "Bearer YOUR_ACCESS_TOKEN",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": "2547XXXXXXX",
        "type": "text",
        "text": {"body": "Hello from FastAPI 🚀"}
    }

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message: {response.status_code} - {response.text}")