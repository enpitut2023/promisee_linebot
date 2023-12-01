from flask import Flask, request, abort, render_template

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)

from linebot.models import MessageEvent, TextMessage, ConfirmTemplate, TemplateSendMessage, PostbackAction

app = Flask(__name__)
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

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 受け取ったメッセージがテキストの場合、確認テンプレートを送信する
    if event.message.text.lower() == "confirm":
        confirm_template = ConfirmTemplate(
            text="Are you sure?",
            actions=[
                PostbackAction(label="Yes", data="yes"),
                PostbackAction(label="No", data="no")
            ]
        )
        template_message = TemplateSendMessage(
            alt_text="this is a confirm template",
            template=confirm_template
        )
        line_bot_api.reply_message(event.reply_token, template_message)


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text1 = event.message.text 
    text2 = "間に合った人にline詫びギフトを送りましょう(>_<)"
    
    url="https://gift.line.me/item/6517019"
    text = text1 + " " +text2 + url
    # テキストの最初の文字が@の場合、同じテキストを鸚鵡返し
    if text.startswith('@'):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=text)
        )

    


    
if __name__ == "__main__":
    app.run()
