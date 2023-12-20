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
import atexit
import schedule
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
# データベースの準備等
cred = credentials.Certificate("key.json")

firebase_admin.initialize_app(cred)
db = firestore.client()

group_doc_ref = db.collection('groups')
member_doc_ref = db.collection('group_member')
# データベース準備終了

# LIFF URL
liff_url_base ="https://liff.line.me/2002096181-Ryql27BY"

# データベース使い方
format={
    "username":[],
    "answer":[],
    "group_count":None,
    "schedule": None,
}

format_schedule={
    "schedule": "schedule"
}


app = Flask(__name__)
button_disabled=False
dotenv.load_dotenv()
CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]
 
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 定期実行のためのスケジューラを作成
scheduler = BackgroundScheduler()
scheduler.start()

# アプリケーション終了時にスケジューラを停止
atexit.register(lambda: scheduler.shutdown())


# 基本いじらない
@app.route("/callback", methods=['POST'])
def callback():
    # ラインからのPOSTかを判定
    signature = request.headers['X-Line-Signature']

    # テキストを受け取ってる
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(events):

    
    # 受け取ったメッセージがテキストの場合、確認テンプレートを送信する
    if events.message.text.lower() == "確認":
        group_id = events.source.group_id # groupidを取得
        group_count=line_bot_api.get_group_members_count(group_id)
        format['group_count']=group_count

        group_doc = group_doc_ref.document(group_id) #ドキュメントを生成
        group_doc.set(format) #データベースに空データを格納
        # LIFF URLを生成
        # group_idをLIFF URLに埋め込む
        liff_url = f"{liff_url_base}?group_id={group_id}"

        # 生成したLIFF URLをユーザーに送信
        line_bot_api.reply_message(
            events.reply_token,
            TextSendMessage(text=f"{liff_url}")
        )

    # if events.message.text.lower() == "予定":
    #     group_id = events.source.group_id # groupidを取得
    #     format["schedule"]="1月1日"
    #     group_doc = group_doc_ref.document(group_id) #ドキュメントを生成
    #     group_doc.set(format) #データベースに空データを格納
    #     # LIFF URLを生成
    #     # group_idをLIFF URLに埋め込む
    #     liff_url = f"{liff_url_base}?group_id={group_id}"

    #     # 生成したLIFF URLをユーザーに送信
    #     line_bot_api.reply_message(
    #         events.reply_token,
    #         TextSendMessage(text="予定が保存されました")
    #     )

 # 予定の時間がデータベースに登録されている前提
    elif events.message.text.lower() == "テスト":
        group_id = events.source.group_id
        group_doc = group_doc_ref.document(group_id) 
        print("実行されました")
        # データベースから時間を取得
        schedule_data = group_doc.get().to_dict()
        schedule_time = schedule_data.get("schedule", "")  # スケジュールをデータベースから取ってくる（例：10:00　のような形式）

        if schedule_time:
            # スケジューラに追加
            schedule.every().day.at(schedule_time).do(send_reminder, group_id=group_id)

            # スケジュールが定期的に実行されるように無限ループ
            while True:
                n = schedule.idle_seconds()
                if n is None:
                    break
                elif n > 0:
                    time.sleep(n)
                schedule.run_pending()

                
# 定期実行する関数
def send_reminder(group_id):
    # group_idをLIFF URLに埋め込む
    liff_url = f"間に合ったかアンケートを入力するのだ！！\n{liff_url_base}?group_id={group_id}"
    # LINEボットを通じてメッセージを送信する処理
    message = TextSendMessage(text=f"{liff_url}")
    line_bot_api.push_message(group_id, messages=message)
    return schedule.CancelJob



    # # 予定確認の処理
    # elif input_text.startswith(CHECK_PREFIX):
    #     # ここでは実際の予定確認処理を省略
    #     return "登録された予定を確認します。"

    # # どちらにも一致しない場合
    # else:
    #     return "無効な入力です。"



if __name__ == "__main__":
    app.run(port=5002)
