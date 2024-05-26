import requests
import json

W2G_API_KEY='3y50ix1ny1y9v6qp40naq3y2cejodr77t9y05e3uath1ysc0bne0shy4iknnayr6'
def make_room(link):
    url = 'https://api.w2g.tv/rooms/create.json'
    headers = {
        'Content-Type': 'application/json',
    }
    payload = {
        'w2g_api_key': W2G_API_KEY,
        'share': link,
        'bg_color': '#ffffff',
        'bg_opacity': '100'
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  
        if response.status_code == 200:
            data = response.json()
            room_link = f"https://w2g.tv/rooms/{data['streamkey']}"
            
            return room_link
        else:
            return response.status_code,response.text
    except requests.exceptions.RequestException as e:
        return e
