from flask import Flask, request, abort, render_template

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)

from linebot.models import MessageEvent, TextMessage, ConfirmTemplate, TemplateSendMessage, PostbackAction, TextSendMessage, PostbackEvent, SourceGroup

app = Flask(__name__)

import os, dotenv, requests
import random

app = Flask(__name__)
button_disabled=False
button_disabled1=False
dotenv.load_dotenv()
CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]
 
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# グループメンバーのプロフィール情報を取得する関数
# def get_group_members(group_id):
#     members = []
#     url = f'https://api.line.me/v2/bot/group/{group_id}/members/ids'
#     headers = {
#         'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'
#     }
#     response = requests.get(url, headers=headers)
#     if response.status_code == 200:
#         members = response.json()['memberIds']
#     return members


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

# @handler.add(MessageEvent, message=TextMessage)
# def handle_message(event):
#     if isinstance(event.source, SourceGroup):
#         group_id = event.source.group_id
#     # 受け取ったメッセージがテキストの場合、確認テンプレートを送信する
#     if event.message.text.lower() == "confirm":
#         # グループのメンバーIDを取得
#         group_members = get_group_members(group_id)
#         user_actions = []
#         for member_id in group_members:
#             profile = line_bot_api.get_profile(member_id)
            
#             display_name = profile.display_name
                
#             # ラベルが表示名となるPostbackActionを作成
#             action = PostbackAction(label=display_name, data=display_name)
#             user_actions.append(action)

#         confirm_template = ConfirmTemplate(
#             text="約束に間に合わなかった人は?",
#             actions=[user_actions,PostbackAction(label="いない", data="no")]
#         )
#         template_message = TemplateSendMessage(
#             alt_text="this is a confirm template",
#             template=confirm_template
#         )
#         line_bot_api.reply_message(event.reply_token, template_message)


        # # ユーザー名のリストを文字列に変換して送信
        # member_names = '\n'.join(profiles)
        # reply_message = TextSendMessage(text=f'グループメンバー:\n{member_names}')
        # line_bot_api.reply_message(event.reply_token, reply_message)


    # テキストの最初の文字が@の場合、同じテキストを鸚鵡返し
    # elif text.startswith('@'):
    #     text1 = event.message.text 
    #     text2 = "間に合った人にline詫びギフトを送りましょう(>_<)"
            
    #     url="https://gift.line.me/item/6517019"
    #     text = text1 + " " +text2 + "\n" + url
    #     line_bot_api.reply_message(
    #         event.reply_token,
    #         TextSendMessage(text=text)
    #     )

   # メッセージイベントのハンドラ
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text.lower() == "確認":
        global button_disabled
        global button_disabled1
        button_disabled=False
        button_disabled1=False
        # 確認テンプレートの作成
        confirm_template = ConfirmTemplate(
            text="約束に間に合いましたか?",
            actions=[
                PostbackAction(label="Yes", data="yes"),
                PostbackAction(label="No", data="no")
            ]
        )
        template_message = TemplateSendMessage(
            alt_text="this is a confirm template",
            template=confirm_template
        )
        # 確認テンプレートを返信
        line_bot_api.reply_message(event.reply_token, template_message) 

# ポストバックイベントのハンドラ
@handler.add(PostbackEvent)
def handle_postback(event):
    finish_words = ["yes", "no"]
    finish_words1 = [ "0-100", "100-400"]

    postback_data = event.postback.data
    global button_disabled
    global button_disabled1
    # ポストバックデータに応じた処理
    if postback_data == "no" and not button_disabled:
        
        # 確認テンプレートの作成
        confirm_template = ConfirmTemplate(
            text="間に合った人にline詫びギフトを送りましょう(>_<)",
            actions=[
                PostbackAction(label="0-100", data="0-100"),
                PostbackAction(label="100-400", data="100-400")
            ]
        )

        template_message = TemplateSendMessage(
            alt_text="this is a confirm template",
            template=confirm_template
        )
        # 確認テンプレートを返信
        line_bot_api.reply_message(event.reply_token, template_message) 

    elif postback_data == "yes" and not button_disabled:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="全員間に合いました！！"))
        # ここにNoが選択されたときの処理を追加
    elif postback_data == "0-100" and not button_disabled1:

        text2 = "間に合った人にline詫びギフトを送りましょう(>_<)"
        gift_idx = random.randint(0, 2)
        url=["https://gift.line.me/item/7203592", "https://gift.line.me/item/7513743", "https://gift.line.me/item/7513744"]
        text = text2 + "\n" + url[gift_idx]

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=text)
        )
    elif postback_data == "100-400" and not button_disabled1:

        text2 = "間に合った人にline詫びギフトを送りましょう(>_<)"
        gift_idx = random.randint(0, 2)
        url=["https://gift.line.me/item/6875507", "https://gift.line.me/item/6517019", "https://gift.line.me/item/7051436"]
        text = text2 + "\n" + url[gift_idx]

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=text)
        )

    if event.postback.data in finish_words:
        button_disabled = True  # ボタンが押されたら無効にする
    if event.postback.data in finish_words1:
        button_disabled1 = True

    



# # ポストバックイベントのハンドラ
# @handler.add(PostbackEvent)
# def handle_postback(event):
#     postback_data = event.postback.data

#     # ポストバックデータに応じた処理
#     if postback_data == "yes":
#         line_bot_api.reply_message(event.reply_token, TextSendMessage(text="Yesが選択されました"))
#         # ここにYesが選択されたときの処理を追加
#     elif postback_data == "no":
#         line_bot_api.reply_message(event.reply_token, TextSendMessage(text="Noが選択されました"))
#         # ここにNoが選択されたときの処理を追加


if __name__ == "__main__":
    app.run()
