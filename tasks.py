import os
from celery import Celery
from celery.utils.log import get_task_logger
from flask import Flask, request, abort, render_template

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)

from linebot.models import MessageEvent, TextMessage, ConfirmTemplate, TemplateSendMessage, PostbackAction, TextSendMessage, PostbackEvent, SourceGroup
from time import sleep
from datetime import datetime

app = Celery('tasks', broker=os.getenv("CELERY_BROKER_URL"))
logger = get_task_logger(__name__)
CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
liff_url_base = "https://liff.line.me/2002096181-Ryql27BY"

@app.task
# 時間になったら実行する処理
def process_scheduled_task(arg1):
    liff_url = f"間に合ったかアンケートを入力するのだ！！\n{liff_url_base}?group_id={arg1}"
    message = TextSendMessage(text=f"{liff_url}")
    line_bot_api.push_message(arg1, messages=message)
    print("定期的な処理が実行されました", datetime.now())

