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
import datetime

cancel_flag = False
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
        schedule_time = schedule_data.get("schedule", "")  # スケジュールをデータベースから取ってくる
        # schedule_time= "2023年12月20日16時30分"

        if schedule_time:
            # 指定された時刻に実行される関数をスケジュール
            target_datetime = datetime.datetime.strptime(schedule_time, "%Y年%m月%d日%H時%M分")
            print(target_datetime)  
            current_datetime = datetime.datetime.now()
            # 現在時刻と指定時刻の差を求めている
            time_difference = (target_datetime - current_datetime).total_seconds()
            print(time_difference)

            # 指定時間までスリープ
            while time_difference > 0:
                if cancel_flag:
                    print("実行がキャンセルされました")
                    return
                time.sleep(1)
                current_datetime = datetime.datetime.now()
                time_difference = (target_datetime - current_datetime).total_seconds()
            
            # time.sleep(max(0, time_difference))
            # 指定時間に関数を実行
            send_reminder(group_id)

                
# 時間になったら実行する関数
def send_reminder(group_id):
    # group_idをLIFF URLに埋め込む
    liff_url = f"間に合ったかアンケートを入力するのだ！！\n{liff_url_base}?group_id={group_id}"
    # LINEボットを通じてメッセージを送信する処理
    message = TextSendMessage(text=f"{liff_url}")
    line_bot_api.push_message(group_id, messages=message)




    # # 予定確認の処理
    # elif input_text.startswith(CHECK_PREFIX):
    #     # ここでは実際の予定確認処理を省略
    #     return "登録された予定を確認します。"

    # # どちらにも一致しない場合
    # else:
    #     return "無効な入力です。"



if __name__ == "__main__":
    app.run(port=5002)
