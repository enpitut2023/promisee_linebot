from flask import Flask, request, abort, render_template

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
import os, dotenv

app = Flask(__name__)

dotenv.load_dotenv()
CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]
 
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)





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


import datetime
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    user_mentions = event.message.mention
    # メンションされたユーザーの表示名やユーザーIDなどを取得
    for mention in user_mentions:
        user_id = mention["userId"]
        display_name = mention["displayName"]
        line_bot_api.reply_message(
            event.reply_token,
            TextMessage(text=f"メンションされたユーザー: {display_name} (ID: {user_id})")
        )

    
if __name__ == "__main__":
    app.run()
