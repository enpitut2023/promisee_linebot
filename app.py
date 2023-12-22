from flask import Flask, request, abort, render_template

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)

from linebot.models import MessageEvent, TextMessage, ConfirmTemplate, TemplateSendMessage, PostbackAction, TextSendMessage, PostbackEvent, SourceGroup
from time import sleep

import time
import os, dotenv, requests
import firebase_admin
from firebase_admin import credentials,firestore
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
import uuid

app = Flask(__name__)
# スケジューラの設定
scheduler = BackgroundScheduler()

# Flaskアプリケーションを初期化した後にスケジューラをスタートする
scheduler.start()

dotenv.load_dotenv()
CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]
 
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

cancel_flag = False
liff_url_base = "https://liff.line.me/2002096181-Ryql27BY"

# データベース使い方
format = {
    "username": [],
    "answer": [],
    "group_count": None,
    "schedule": None,
}

format_schedule = {
    "schedule": "schedule"
}

cred = credentials.Certificate("key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()
group_doc_ref = db.collection('groups')


# 時間になったら実行する処理
def my_job(arg1):
    liff_url = f"間に合ったかアンケートを入力するのだ！！\n{liff_url_base}?group_id={arg1}"
    message = TextSendMessage(text=f"{liff_url}")
    line_bot_api.push_message(arg1, messages=message)
    print("定期的な処理が実行されましたnanoda", datetime.now())



@app.route("/callback", methods=['POST'])
async def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(events):
    if events.message.text.lower() == "確認":
        group_id = events.source.group_id
        group_count = line_bot_api.get_group_members_count(group_id)
        format['group_count'] = group_count
        group_doc = group_doc_ref.document(group_id)
        group_doc.set(format)
        liff_url = f"{liff_url_base}?group_id={group_id}"
        line_bot_api.reply_message(events.reply_token, TextSendMessage(text=f"間に合ったかアンケートに回答するのだ\n{liff_url}"))


    elif events.message.text.lower() == "テスト":
        group_id = events.source.group_id
        print("実行されました")
        # スケジューラーにタスクを追加
        scheduler.add_job(my_job, 'date', run_date='2023-12-22 11:53:00',args=[group_id])
        return 'OK'
    else:
        return 'OK'

if __name__ == "__main__":
    if not scheduler.running:
        scheduler.start()
    app.run(debug=False,port=5002)
