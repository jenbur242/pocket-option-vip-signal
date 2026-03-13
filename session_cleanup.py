from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from termcolor import colored, cprint
from pyfiglet import figlet_format

# Hardcoded credentials
API_ID = '34506083'
API_HASH = '5676893fa1c0fe15eca5dbbceb3ab6a2'
PHONE_NUMBER = '+12428018500'

def create_session_with_hardcoded_credentials():
    """Create session string using hardcoded credentials with Telethon"""
    cprint("Creating session with hardcoded credentials using Telethon...", "cyan")
    
    try:
        # Using Telethon (more stable with Python 3.14)
        with TelegramClient(StringSession(), int(API_ID), API_HASH) as client:
            cprint("Connecting to Telegram...", "yellow")
            
            # Export session string
            session_str = client.session.save()
            
            cprint("=" * 50, "green")
            cprint("SESSION STRING GENERATED:", "yellow", attrs=['bold'])
            cprint(session_str, "cyan")
            cprint("=" * 50, "green")
            
            # Save to file
            with open("session_string.txt", "w") as f:
                f.write(session_str)
            cprint("Session string saved to session_string.txt", "green")
            
            return session_str
            
    except Exception as e:
        cprint(f"Error creating session: {e}", "red")
        return None

def main():
    while True:
        cprint(colored(figlet_format('Telegram', "smslant"), "cyan", attrs=['bold']))
        cprint(colored("Session generator\n", "magenta", attrs=['bold']))
        cprint("[p] Pyrogram\n[t] Telethon\n[h] Use hardcoded credentials", "yellow")
        opt = input(colored("Choose your option: ", "green")).lower()
        
        if "h" in opt:
            cprint("Using hardcoded credentials...", "magenta")
            session_str = create_session_with_hardcoded_credentials()
            if session_str:
                cprint("Session created successfully!", "green")
            break
            
        elif "p" in opt:
            cprint("You've selected pyrogram", "magenta")
            APP_ID = int(input(colored("Enter APP ID here: ", "green")))
            API_HASH = input(colored("Enter API HASH here: ", "green"))
            with Client(":memory:", api_id=APP_ID, api_hash=API_HASH) as app:
                app.storage.SESSION_STRING_FORMAT=">B?256sQ?"
                session_str = app.export_session_string()
                if app.get_me().is_bot:
                    user_name = input(colored("Enter the username: ", "green"))
                    msg = app.send_message(user_name, session_str)
                else:
                    msg = app.send_message("me", session_str)
                msg.reply_text(
                    "⬆️ This String Session is generated using https://tgsession.infotelbot.com \nPlease subscribe @InFoTelGroup ",
                    quote=True,
                )
                cprint("please check your Telegram Saved Messages/user's PM for the StringSession ", "yellow")
            break

        elif "t" in opt:
            cprint("You've selected Telethon", "magenta")
            APP_ID = int(input(colored("Enter APP ID here: ", "green")))
            API_HASH = input(colored("Enter API HASH here: ", "green"))
            with TelegramClient(StringSession(), APP_ID, API_HASH) as client:
                session_str = client.session.save()
                if client.is_bot():
                    user_name = input("Enter the username: ")
                    msg = client.send_message(user_name, session_str)
                else:
                    msg = client.send_message("me", session_str)
                msg.reply(
                    "⬆️ This String Session is generated using https://tgsession.infotelbot.com \nPlease subscribe @InFoTelGroup "
                )
                cprint("please check your Telegram Saved Messages/User's PM for the StringSession ", "yellow")
            break
            
        else:
            cprint("Invalid option try again", "red")
        

if __name__ == "__main__":
    # Auto-create session with hardcoded credentials
    cprint(colored(figlet_format('Auto Session', "smslant"), "cyan", attrs=['bold']))
    cprint(colored("Creating session with hardcoded credentials...\n", "magenta", attrs=['bold']))
    
    session_str = create_session_with_hardcoded_credentials()
    
    if session_str:
        cprint("\nSession string successfully created and saved!", "green", attrs=['bold'])
        cprint("You can now use this session string in your application.", "yellow")
    else:
        cprint("Failed to create session string.", "red", attrs=['bold'])
        
    # Optional: Run interactive mode
    # main()