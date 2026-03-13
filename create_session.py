import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# Hardcoded credentials
API_ID = 34506083
API_HASH = '5676893fa1c0fe15eca5dbbceb3ab6a2'
PHONE_NUMBER = '+12428018500'

async def create_session_string():
    """Create and print session string using hardcoded credentials"""
    print("Creating session string...")
    
    try:
        # Create Telegram client with string session
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        
        # Connect to Telegram
        print("Connecting to Telegram...")
        await client.connect()
        
        # Send code request if not authorized
        if not await client.is_user_authorized():
            print(f"Sending code to {PHONE_NUMBER}...")
            await client.send_code_request(PHONE_NUMBER)
            
            # Ask for code
            code = input("Enter the verification code you received: ")
            try:
                await client.sign_in(PHONE_NUMBER, code)
            except Exception as e:
                print(f"Error signing in: {e}")
                return None
        
        # Get session string
        session_str = client.session.save()
        
        print("\n" + "="*60)
        print("SESSION STRING GENERATED:")
        print("="*60)
        print(session_str)
        print("="*60)
        
        # Save to file
        with open("session_string.txt", "w") as f:
            f.write(session_str)
        print("Session string saved to session_string.txt")
        
        await client.disconnect()
        return session_str
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(create_session_string())
