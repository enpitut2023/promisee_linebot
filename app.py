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


@app.route("/")
def hello():
    return render_template("index.html")


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(200)

    return 'OK'


import datetime
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text == '現在時刻':
        reply_message = datetime.datetime.now().strftime('%Y年%m月%d日 %H:%M:%Sです')
    else:
        reply_message = "「現在時刻」と送信してください。"
    line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_message))
    
if __name__ == "__main__":
    app.run()