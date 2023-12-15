from flask import Flask, request, abort, render_template

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)

from linebot.models import MessageEvent, TextMessage, ConfirmTemplate, TemplateSendMessage, PostbackAction, TextSendMessage, PostbackEvent, SourceGroup


import os, dotenv, requests
import firebase_admin
from firebase_admin import credentials,firestore
import requests

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
    "groupcount":None,
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
    print(events)
    SCHEDULE_REGISTER_PREFIX = "予定登録"
    SCHEDULE_CHECK_PREFIX = "予定確認"
    
    # 受け取ったメッセージがテキストの場合、確認テンプレートを送信する
    if events.message.text.lower() == "確認":
        group_id = events.source.group_id # groupidを取得


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

    if events.message.text.lower() == "予定":
        group_id = events.source.group_id # groupidを取得
        group_doc = group_doc_ref.document(group_id) #ドキュメントを生成
        group_doc.set(format_schedule) #データベースに空データを格納
        # LIFF URLを生成
        # group_idをLIFF URLに埋め込む
        liff_url = f"{liff_url_base}?group_id={group_id}"

        # 生成したLIFF URLをユーザーに送信
        line_bot_api.reply_message(
            events.reply_token,
            TextSendMessage(text="予定が保存されました")
        )


    # 予定登録の処理
    elif events.message.text.lower().startswith(SCHEDULE_REGISTER_PREFIX):
        schedule = events.message.text.lower()[len(SCHEDULE_REGISTER_PREFIX):].strip()
        group_id = events.source.group_id # groupidを取得
        group_doc = group_doc_ref.document(group_id) #ドキュメントを生成
        format_schedule.schedule = schedule
        group_doc.set(format_schedule) #データベースに空データを格納

        line_bot_api.reply_message(
            events.reply_token,
            TextSendMessage(text="予定が保存されました")
        )
    

    # # 予定確認の処理
    # elif input_text.startswith(CHECK_PREFIX):
    #     # ここでは実際の予定確認処理を省略
    #     return "登録された予定を確認します。"

    # # どちらにも一致しない場合
    # else:
    #     return "無効な入力です。"


   # メッセージイベントのハンドラ
# @handler.add(MessageEvent, message=TextMessage)
# def handle_message(event):
#     if event.message.text.lower() == "確認":
#         global button_disabled
#         button_disabled=False
#         # 確認テンプレートの作成
#         confirm_template = ConfirmTemplate(
#             text="約束に間に合いましたか?",
#             actions=[
#                 PostbackAction(label="Yes", data="yes"),
#                 PostbackAction(label="No", data="no")
#             ]
#         )
#         template_message = TemplateSendMessage(
#             alt_text="this is a confirm template",
#             template=confirm_template
#         )
#         # 確認テンプレートを返信
#         line_bot_api.reply_message(event.reply_token, template_message) 

# # ポストバックイベントのハンドラ
# @handler.add(PostbackEvent)
# def handle_postback(event):
#     postback_data = event.postback.data
#     global button_disabled
#     # ポストバックデータに応じた処理
#     if postback_data == "no" and not button_disabled:
        
#         # ここにYesが選択されたときの処理を追加
#         text2 = "間に合った人にline詫びギフトを送りましょう(>_<)"
            
#         url="https://gift.line.me/item/6517019"
#         text = text2 + "\n" + url

#         line_bot_api.reply_message(
#             event.reply_token,
#             TextSendMessage(text=text)
#         )
#     elif postback_data == "yes" and not button_disabled:
#         line_bot_api.reply_message(event.reply_token, TextSendMessage(text="全員間に合いました！！"))
#         # ここにNoが選択されたときの処理を追加

#     if event.postback.data == "yes" or event.postback.data == "no":
#         button_disabled = True  # ボタンが押されたら無効にする


if __name__ == "__main__":
    app.run()






