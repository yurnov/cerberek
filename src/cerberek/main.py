"""
Main module for the Cerberek Telegram antispam bot.

This module initializes the bot, loads necessary configurations and keywords,
and sets up handlers to monitor and manage messages in a Telegram group chat.
"""

import logging
import os
import sys

import yaml
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

# Load environment variables
load_dotenv()
token = os.getenv('TELEGRAM_BOT_TOKEN')
group_chat_id = os.getenv('GROUP_CHAT_ID')
logging_level = os.getenv('LOGGING_LEVEL', 'INFO').upper()
logger.info("Telegram Bot Token: <censored>, Group Chat ID: %s, Loggin level %s", group_chat_id, logging_level)
action = os.getenv('ACTION', 'kick').lower()
if action not in ['kick', 'readonly']:
    logger.warning("Invalid action: %s. Defaulting to 'kick'.", action)
    action = 'kick'
if action == 'radonly':
    logger.warning("Action set to 'readonly'. Users will not be kicked, but messages will be deleted.")
    readonly_days = os.getenv('READONLY_DAYS', '7')
    try:
        readonly_days = int(readonly_days)
        if readonly_days < 1:
            raise ValueError("READONLY_DAYS must be a positive integer.")
    except ValueError:
        logger.warning("Invalid READONLY_DAYS value: %s. Defaulting to 7 days.", readonly_days)
        readonly_days = 7

# Set logging level
if logging_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
    logger.setLevel(logging_level)
else:
    logger.setLevel(logging.INFO)
    logger.warning("Invalid logging level: %s. Defaulting to INFO.", logging_level)

if not token or not group_chat_id:
    logger.error("Please set the TELEGRAM_BOT_TOKEN and GROUP_CHAT_ID environment variables.")
    sys.exit(1)


# Load keywords from YAML file
def load_keywords():
    """
    Load keywords from a YAML file.

    """
    try:
        with open('/app/keywords.yaml', 'r', encoding="utf-8") as file:
            return yaml.safe_load(file)

    except Exception as e:  # pylint: disable=W0718
        logger.error("Error loading keywords: %s", e)
        sys.exit(1)


# Check if user is admin
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Check if the user is an admin in the group
    """

    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    logger.debug("Checking if user %s is admin in chat %s.", user_id, chat_id)
    member = await context.bot.get_chat_member(chat_id, user_id)
    return bool(member.status in ['administrator', 'creator'] if member is not None else False)


# Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle incoming messages in the chat.

    This function performs the following tasks:
    1. Retrieves the list of keywords from the bot's context data.
    2. Ignores messages from admins to prevent accidental kicks.
    3. Checks if the message contains any of the predefined keywords.
    4. Deletes the message and kicks the user if a keyword is found.

    Args:
        update (telegram.Update): The incoming update containing the message.
        context (telegram.ext.ContextTypes.DEFAULT_TYPE): The context for the update, including bot data.

    Note:
        - The function assumes that the keywords are stored in a dictionary under the key "keywords" in bot data.
        - Only non-admin users are subject to keyword checks.
        - The user is banned from the chat if a keyword is detected in their message.
    """

    keywords = context.bot_data["keywords"]
    if not keywords or not isinstance(keywords, dict):
        logger.error("No keywords found in bot data.")
        return

    if not update.message or not update.message.text:
        return

    message_text = update.message.text.strip().lower()

    if await is_admin(update, context):
        logger.debug("Admin message received, ignoring.")
        return

    keyword = None
    for word in keywords["keywords"]:
        if word in message_text:
            keyword = word
            break

    if keyword:
        logger.info("Keyword %s found in message: %s", keyword, message_text)
        from_user_id = update.effective_user.id if update.effective_user else None
        from_chat_id = update.effective_chat.id if update.effective_chat else None

        if from_user_id and from_chat_id:
            from_username = update.effective_user.username

            try:
                # Delete the message
                await update.message.delete()
                logger.info("Message containing keyword '%s' deleted.", keyword)
            except Exception as e:  # pylint: disable=W0718
                logger.error("Failed to delete message: %s", e)

            if action == 'readonly':
                try:
                    # Restrict the user to read-only mode
                    await context.bot.restrict_chat_member(
                        chat_id=from_chat_id,
                        user_id=from_user_id,
                        permissions={
                            'can_send_messages': False,
                            'can_send_media_messages': False,
                            'can_send_polls': False,
                            'can_send_other_messages': False,
                            'can_add_web_page_previews': False,
                            'can_invite_users': False,
                            'can_pin_messages': False,
                        },
                        until_date=readonly_days * 24 * 60 * 60,  # Restrict for the specified number of days
                    )
                    logger.info(
                        "User %s restricted to read-only mode for %d days due to keyword: %s",
                        from_username,
                        readonly_days,
                        keyword,
                    )
                except Exception as e:
                    logger.error("Failed to restrict user: %s", e)
                    return

            elif action == 'kick':

                try:
                    # Kick the user
                    await context.bot.ban_chat_member(chat_id=from_chat_id, user_id=from_user_id, revoke_messages=True)
                    logger.info(
                        "User %s kicked for using keyword: %s",
                        from_username,
                        keyword,
                    )
                except Exception as e:  # pylint: disable=W0718
                    logger.error("Failed to kick user: %s", e)


def main():
    """
    The main entry point for the application.

    This function performs the following tasks:
    1. Loads keywords required for the bot's functionality.
    2. Sets up the bot application using the ApplicationBuilder.
    3. Adds bot data, such as keywords, to the application's context.
    4. Registers message handlers to process incoming messages.
    5. Starts the bot using polling to listen for updates.

    Note:
        Ensure that the required environment variables and dependencies
        are properly configured before running this function.
    """

    # Load keywords
    keywords = load_keywords()

    # Set up the Application
    application = ApplicationBuilder().token(token).build()

    # Add bot data
    application.bot_data['keywords'] = keywords

    # Add handlers
    # application.add_handler(MessageHandler(filters.TEXT & filters.Chat(group_chat_id), handle_message))
    application.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Start the bot
    application.run_polling()


if __name__ == '__main__':
    main()
