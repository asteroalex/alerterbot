import asyncio
import json
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import types
from aiogram.dispatcher.filters import Text

API_TOKEN = "7577906602:AAE_h3DES98V779Lnm4v6mgUhAj3_qtrTPo"
ADMIN_IDS = [1267171169]  # Only one admin ID (first admin)

# Path to the file where data will be stored
CHANNELS_DB = "channels_data.json"

# Create bot object
bot = Bot(token=API_TOKEN)

# Create Dispatcher object
dp = Dispatcher()

user_channels = {}  # Dictionary for storing user channels and their notification status
waiting_for_admin_message = None  # Track which admin is waiting for a message

# Load data from the file
def load_channels():
    global user_channels
    try:
        with open(CHANNELS_DB, "r") as f:
            user_channels = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        user_channels = {}

# Save data to the file
def save_channels():
    with open(CHANNELS_DB, "w") as f:
        json.dump(user_channels, f, indent=4)

# Main menu
@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[ 
        [InlineKeyboardButton(text="Add to Channel ✅", callback_data="add_channel")],
        [InlineKeyboardButton(text="My Channels ⚡️", callback_data="my_channels")],
        [InlineKeyboardButton(text="Notification Types 📨", callback_data="notification_types")],
        [InlineKeyboardButton(text="Bot Channel 🤖", url="https://t.me/TGGiftsNews")]  # New button
    ], row_width=1)

    await message.answer(
        "Hello! I'm a bot assistant for sending important gift-related messages on Telegram\n\n"
        "Add me to your channel, and I will publish all important news about it",
        reply_markup=keyboard
    )

# Add channel handler
@dp.callback_query(lambda cb: cb.data == "add_channel")
async def add_channel(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[ 
        [InlineKeyboardButton(text="How to make me an admin ❓", url="https://teletype.in/@giftsalerterbot/channel")],
        [InlineKeyboardButton(text="Cancel ◀️", callback_data="main_menu")]
    ]) 

    await callback_query.message.edit_text(
        "Add me to your channel and make me an administrator\n\n"
        "After that, send me the @username of your channel",
        reply_markup=keyboard
    )

# Get @username of the channel
@dp.message(lambda message: message.text.startswith('@'))
async def receive_channel_username(message: types.Message):
    channel_username = message.text
    user_id = message.from_user.id

    # Check if the user is in the process of adding a channel
    if channel_username in user_channels.get(user_id, {}):
        await message.answer("This channel is already added.", reply_markup=InlineKeyboardMarkup(inline_keyboard=[ 
            [InlineKeyboardButton(text="Main Menu ◀️", callback_data="main_menu")]
        ]))
        return

    try:
        member = await bot.get_chat_member(channel_username, bot.id)
        if member.status in ["administrator", "creator"]:
            user_channels.setdefault(user_id, {})[channel_username] = True  # Add the channel with notifications enabled
            save_channels()  # Save changes to the file
            await message.answer(
                "Great! I will now be able to publish all important gift-related messages on Telegram",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[ 
                    [InlineKeyboardButton(text="Main Menu ◀️", callback_data="main_menu")]
                ])
            )
        else:
            raise Exception
    except Exception:
        await message.answer(
            "I'm not an admin in this channel, or I don't have enough rights to post in it.\n\n"
            "Please make me an admin in your channel and grant me all necessary permissions",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[ 
                [InlineKeyboardButton(text="How to make me an admin ❓", url="https://teletype.in/@giftsalerterbot/channel")],
                [InlineKeyboardButton(text="Cancel ◀️", callback_data="main_menu")]
            ])
        )

# Notification types handler
@dp.callback_query(lambda cb: cb.data == "notification_types")
async def notification_types(callback_query: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[ 
        [InlineKeyboardButton(text="Main Menu ◀️", callback_data="main_menu")]
    ]) 

    await callback_query.message.edit_text(
        "Currently, the bot publishes the following gift-related information:\n\n"
        "➣ Appearance of new gifts (each gift is sent as a separate message with detailed information - gift name, price, and if applicable - gift limit)\n"
        "➣ When a limited gift is almost sold out, the bot will send a notification that only a small amount of the gift is left (usually around 1000/5000 items remaining)\n"
        "➣ When a limited gift is completely sold out (the exact information about the gift, its price, and any purchase limits will be published)",
        reply_markup=keyboard
    )

# /sendinfo command handler
@dp.message_handler(commands=["sendinfo"])
async def send_info(message: types.Message):
    global waiting_for_admin_message

    if message.from_user.id not in ADMIN_IDS:
        await message.answer("You do not have permission to use this command.")
        return

    # If another admin is already waiting for a message, we inform and stop.
    if waiting_for_admin_message is not None:
        await message.answer("Another admin is already sending a message. Please wait.")
        return

    waiting_for_admin_message = message.from_user.id  # Mark this admin as waiting for the message

    await message.answer(
        "You are in the admin panel! Send the message you want to publish to all channels."
    )

# Process the admin message
@dp.message(lambda message: message.from_user.id in ADMIN_IDS)
async def process_admin_message(msg: types.Message):
    global waiting_for_admin_message

    # Only process if this admin is the one waiting for the message
    if msg.from_user.id != waiting_for_admin_message:
        return  # Ignore messages from other admins if they are not in the "waiting" state

    admin_message = msg.text
    footer = "\n\nSend by @GiftAlerterBot"

    # Send message to all channels
    for user_id, channels in user_channels.items():
        for channel, status in channels.items():
            try:
                # If the channel is not @TGGiftsNews and notification is enabled, append footer
                if channel != "@TGGiftsNews" and status:
                    message_to_send = admin_message + footer
                else:
                    message_to_send = admin_message
                
                # Send the message to the channel if notifications are enabled
                if status:
                    await bot.send_message(channel, message_to_send)

            except Exception as e:
                print(f"Error sending message to channel {channel}: {e}")

    await msg.answer("Message successfully sent!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[ 
        [InlineKeyboardButton(text="Main Menu ◀️", callback_data="main_menu")]
    ]))

    waiting_for_admin_message = None  # Reset the state after the message is sent

# My channels handler
@dp.callback_query(lambda cb: cb.data == "my_channels")
async def my_channels(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    channels = user_channels.get(user_id, {})

    # Create the keyboard for the list of channels
    inline_buttons = []
    if channels:
        for channel, status in channels.items():
            symbol = "✅" if status else "❌"
            inline_buttons.append([InlineKeyboardButton(text=f"{channel} {symbol}", callback_data=f"toggle_{channel}")])

    # "Back" button should always be at the bottom
    inline_buttons.append([InlineKeyboardButton(text="Back ◀️", callback_data="main_menu")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=inline_buttons)

    await callback_query.message.edit_text(
        "Your list of added channels:\n\n"
        "✅ - channel receives notifications about gifts\n"
        "❌ - bot does not send notifications to this channel\n\n"
        "Click the buttons to enable or disable message notifications",
        reply_markup=keyboard
    )

# Toggle notification status handler
@dp.callback_query(lambda cb: cb.data.startswith("toggle_"))
async def toggle_channel_status(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    channel = callback_query.data.replace("toggle_", "")

    if channel in user_channels.get(user_id, {}):
        # Toggle the notification status
        if user_channels[user_id][channel]:
            user_channels[user_id][channel] = False
        else:
            user_channels[user_id][channel] = True
        
        save_channels()  # Save the changes to the file
        await my_channels(callback_query)

# Main menu handler
@dp.callback_query(lambda cb: cb.data == "main_menu")
async def main_menu(callback_query: types.CallbackQuery):
    await send_welcome(callback_query.message)

if __name__ == "__main__":
    load_channels()  # Load data from the file on bot startup
    asyncio.run(dp.start_polling(bot))  # Pass bot to start_polling
