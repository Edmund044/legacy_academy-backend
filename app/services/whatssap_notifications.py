import requests

def send_whatsapp_notification(phone_number: str, message: str):
    url = "https://graph.facebook.com/v18.0/100614629341688/messages"

    headers = {
        "Authorization": "Bearer EAAcyoE0AizABRJdZAeQt4ig3kH8WEjZCb6cqmlZC4bliWhiNsVj6mbJc0H3NE6UtKRIeYWhBtyXcEtedRRHn80b28GJ1If7NaJNmoaQ3WSQ6gX0NONRp3gd5IJ7MkM42RS1dnuic6UTogW5kCsGfsUEqGladBfB5wwnFAl3zjApOPNG0vQBkSKY01pEPrlJiAZDZD",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": message}
    }

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message: {response.status_code} - {response.text}")