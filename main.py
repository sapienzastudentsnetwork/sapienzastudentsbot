#!/usr/bin/env python

# Copyright (C) 2025, Matteo Collica (Matypist)
#
# This file is part of the "Sapienza Students Bot" (SapienzaStudentsBot)
# project, the original source of which is the following GitHub repository:
# <https://github.com/sapienzastudentsnetwork/sapienzastudentsbot>.

from os import getenv as os_getenv

import pytz
from telegram import __version__ as tg_ver
from telegram.constants import ParseMode
from telegram.ext import Application, CallbackQueryHandler, Defaults, MessageHandler, filters, ChatMemberHandler

from tgib.data.database import Database, SessionTable, AccountTable, ChatTable
from tgib.global_vars import GlobalVariables
from tgib.handlers.messages import Messages
from tgib.handlers.statuschanges import StatusChanges
from tgib.handlers.commands import Commands
from tgib.handlers.queries import Queries
from tgib.i18n.locales import Locale
from tgib.logs import Logger

try:
    from telegram import __version_info__

except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This code is not compatible with your current PTB version {tg_ver}. It requires a version later than v20.0."
    )


def add_application_handlers(application: Application):
    application.add_handlers([
        MessageHandler(filters=filters.StatusUpdate.MIGRATE,
                       callback=StatusChanges.migrate_handler),

        MessageHandler(filters=filters.COMMAND, callback=Commands.commands_handler),

        MessageHandler(filters=filters.TEXT, callback=Messages.text_messages_handler),

        CallbackQueryHandler(callback=Queries.callback_queries_handler),

        ChatMemberHandler(callback=StatusChanges.my_chat_member_handler,
                          chat_member_types=ChatMemberHandler.MY_CHAT_MEMBER)
    ])


def main() -> None:
    Logger.init_logger(os_getenv("EXCEPTION_LOG_CHAT_ID"), os_getenv("ADMIN_ACTIONS_LOG_CHAT_ID"))

    Locale.init_locales()

    Database.init_db()

    Queries.register_fixed_queries()

    defaults = Defaults(parse_mode=ParseMode.HTML, tzinfo=pytz.timezone('Europe/Rome'), disable_web_page_preview=True)

    application = Application.builder().token(os_getenv("TOKEN")).defaults(defaults).build()
    application: Application

    application.job_queue.run_once(callback=SessionTable.expire_old_sessions, when=0)

    add_application_handlers(application)

    application.job_queue.run_once(callback=ChatTable.fetch_chats, when=0, data=application.bot)

    GlobalVariables.set_accounts_count(AccountTable.get_account_records_count())

    GlobalVariables.bot_owner = os_getenv("OWNER_CHAT_ID")

    GlobalVariables.bot_instance = application.bot

    GlobalVariables.job_queue = application.job_queue

    GlobalVariables.contact_username = os_getenv("CONTACT_USERNAME")

    if not GlobalVariables.contact_username:
        GlobalVariables.contact_username = "username"

    application.run_polling()


if __name__ == "__main__":
    main()
