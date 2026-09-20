import time
import requests

# CONFIGURATION
ROBLOX_USER_ID = 11109225461
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1551199352062611496/WLnMU6kCjilGt_cOVKzMT_2n5aWBcSYaNoSbYowz9vj8QvFsxfa3pMGDLdqxFoJWBenC"
CHECK_INTERVAL = 30  # Polling delay in seconds

ROBLOX_API_URL = "https://presence.roblox.com/v1/presence/users"

was_in_game = False

def send_discord_notification(presence_data):
    last_location = presence_data.get("lastLocation", "Unknown Game")
    place_id = presence_data.get("placeId")
    root_place_id = presence_data.get("rootPlaceId") or place_id
    game_id = presence_data.get("gameId")  # Server JobId

    # Use rootPlaceId/placeId to construct the links
    effective_place_id = root_place_id if root_place_id else place_id

    # Construct the mobile deep link
    if effective_place_id and game_id:
        join_link = f"https://www.roblox.com/games/start?placeId={effective_place_id}&gameInstanceId={game_id}"
    elif effective_place_id:
        join_link = f"https://www.roblox.com/games/{effective_place_id}"
    else:
        join_link = f"https://www.roblox.com/users/{ROBLOX_USER_ID}/profile"

    game_page_link = f"https://www.roblox.com/games/{effective_place_id}" if effective_place_id else None

    # Construct Discord Webhook Payload
    embed_fields = [
        {
            "name": "🎮 Experience",
            "value": f"[{last_location}]({game_page_link})" if game_page_link else last_location,
            "inline": False
        },
        {
            "name": "🚀 Quick Join",
            "value": f"[👉 **CLICK HERE TO JOIN SERVER**]({join_link})",
            "inline": False
        }
    ]

    payload = {
        "content": f"🚨 **Roblox Alert!** User `11109225461` is playing a game!\n{join_link}",
        "embeds": [
            {
                "title": "Player Status: IN GAME",
                "color": 5763719,  # Green
                "fields": embed_fields,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
        ]
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print("Notification with Join Link sent to Discord!")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send webhook: {e}")

def check_presence():
    global was_in_game
    payload = {"userIds": [ROBLOX_USER_ID]}
    
    try:
        response = requests.post(ROBLOX_API_URL, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        data = response.json()
        
        presences = data.get("userPresences", [])
        if not presences:
            print("No presence data returned.")
            return

        user_presence = presences[0]
        presence_type = user_presence.get("userPresenceType", 0)  # 2 = InGame

        is_currently_in_game = (presence_type == 2)

        if is_currently_in_game and not was_in_game:
            print(f"User entered a game. Sending alert...")
            send_discord_notification(user_presence)
            was_in_game = True
        elif not is_currently_in_game and was_in_game:
            print("User left the game.")
            was_in_game = False
        else:
            print(f"Checking ID 11109225461... Status code: {presence_type}")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching Roblox API: {e}")

if __name__ == "__main__":
    print(f"Tracking Roblox User ID: {ROBLOX_USER_ID}...")
    while True:
        check_presence()
        time.sleep(CHECK_INTERVAL)
