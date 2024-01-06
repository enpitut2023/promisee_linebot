from flask import Flask, request, abort, render_template

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)

from linebot.models import MessageEvent, TextMessage, ConfirmTemplate, TemplateSendMessage, PostbackAction, TextSendMessage, PostbackEvent, SourceGroup, FlexSendMessage, BubbleContainer, TextComponent, BoxComponent, ButtonComponent, PostbackAction, DatetimePickerAction, JoinEvent

from time import sleep

import time
import os
import dotenv
import requests
import firebase_admin
from firebase_admin import credentials, firestore
import requests
from datetime import datetime, timedelta
import pytz
import threading
import uuid
import schedule
import re

app = Flask(__name__)
# タイムゾーンを日本時間に設定
jp_timezone = pytz.timezone('Asia/Tokyo')
dotenv.load_dotenv()
CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]
CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]
 
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

timers = {}
liff_url_base = "https://liff.line.me/2002096181-Ryql27BY"

# データベース使い方
schedule_format = {
    "username": [],
    "answer": [],
    "group_count": None,
    "datetime": None,
    "group_id": None,
}


# サービス アカウント キー ファイルへのパスを環境変数から取得
firebase_admin_key_path = os.environ.get('FIREBASE_ADMIN_KEY_PATH')

# Firebase Admin SDK を初期化
cred = credentials.Certificate(firebase_admin_key_path)

firebase_admin.initialize_app(cred)
db = firestore.client()
group_doc_ref = db.collection('groups')
schedules_doc_ref = db.collection('schedules')

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

@handler.add(JoinEvent)
def handle_member_joined(event):
    # グループメンバーが参加したときの処理
    group_id = event.source.group_id
    welcome_message = f"よろしくなのだ！予定の日時を登録したいときは「予定登録」と送るのだ！"
    
    line_bot_api.push_message(
        group_id,
        TextSendMessage(text=welcome_message)
    )

@handler.add(MessageEvent, message=TextMessage)
def handle_message(events):
    if events.message.text.lower() == "確認":
        group_id = events.source.group_id
        group_count = line_bot_api.get_group_members_count(group_id)
        schedule_format['group_count'] = group_count
        group_doc = group_doc_ref.document(group_id)
        group_doc.set(format)
            # urlの発行時間を埋め込む
        current_time = datetime.now(pytz.timezone('Asia/Tokyo'))
        # 日時を文字列に変換
        current_time_str = current_time.strftime("%Y-%m-%d-%H-%M-%S")

        # liff_urlに日時を埋め込む
        liff_url = f"{liff_url_base}?group_id={group_id}/{current_time_str}"
        line_bot_api.reply_message(events.reply_token, TextSendMessage(text=f"間に合ったかアンケートに回答するのだ!\n{liff_url}"))

    elif events.message.text.lower() == "予定登録":
        group_id = events.source.group_id

        flex_message = FlexSendMessage(
            alt_text='予定日時を選択するのだ！',
            contents=BubbleContainer(
                body=BoxComponent(
                    layout='vertical',
                    contents=[
                        TextComponent(text='予定日時を選択するのだ！', weight='bold'),
                        ButtonComponent(
                            action=DatetimePickerAction(
                                label='予定日時選択',
                                data='datetime_postback',  # Postbackデータ
                                mode='datetime',
                                initial=datetime.now().strftime('%Y-%m-%dT%H:%M'),
                                max='2100-12-31T23:59',
                                min='1900-01-01T00:00'
                            )
                        )
                    ]
                )
            )
        )
        # Flex Messageと追加のテキストメッセージを送信
        line_bot_api.reply_message(
            events.reply_token,
            flex_message
        )


# 予定の保存処理
@handler.add(PostbackEvent)
def handle_postback(events):
    if events.postback.data == 'datetime_postback':

        group_id = events.source.group_id
        group_count = line_bot_api.get_group_members_count(group_id)
        schedule_format['group_count'] = group_count #group_countをschedule_formatに追加

        # 日時選択のPostbackデータを受け取った場合
        selected_iso_datetime = events.postback.params['datetime']  # ISO 8601 形式の日時文字列

        # ISO 8601 形式の文字列を datetime オブジェクトに変換
        selected_datetime = datetime.fromisoformat(selected_iso_datetime)

        # 日時を指定された形式の文字列に変換
        formatted_datetime = selected_datetime.strftime("%Y年%m月%d日%H時%M分")

        group_id = events.source.group_id
        # 選択された日時に関する処理（必要に応じて）
        schedules_doc = schedules_doc_ref.document()
        schedule_format['datetime'] = formatted_datetime
        schedule_format['group_id'] = group_id
        schedules_doc.set(schedule_format)

        # ユーザーに対して応答メッセージを送信
        line_bot_api.reply_message(
            events.reply_token,
            TextSendMessage(text=f"{formatted_datetime}に予定が登録されたのだ！")
        )



# 定期実行により叩かれるAPI
@app.route('/daily_schedule', methods=['POST'])
def handle_daily_schedule():
    print("daily_scheduleAPIが叩かれました")
    time_schedules = request.get_json()

    # run_schedule関数を別スレッドで実行
    threading.Thread(target=run_schedule, args=(time_schedules,), daemon=True).start()

    return "OK"

# 定期実行する関数
def run_schedule(time_schedules):
    print("run_scheduleが実行されました")

    for doc_id in time_schedules:
        time=schedules_doc_ref.document(doc_id).get().to_dict()["datetime"]
        time=jp_timezone.localize(datetime.strptime(time, "%Y年%m月%d日%H時%M分"))
        current_time = datetime.now(pytz.timezone('Asia/Tokyo'))
        delay = max(0, (time - current_time).total_seconds())
        timer_id = str(uuid.uuid4()) 
        # タイマーを設定してイベントをスケジュール
        timer = threading.Timer(delay, scheduled_task, args=(doc_id, timer_id))
        timer.start()

    return "OK"

# 時間になったら、実行する関数
def scheduled_task(schedule_id,timer_id):
    group_id = schedules_doc_ref.document(schedule_id).get().to_dict()["group_id"]
    # # urlの発行時間を埋め込む
    # current_time = datetime.now(pytz.timezone('Asia/Tokyo'))
    # # 日時を文字列に変換
    # current_time_str = current_time.strftime("%Y-%m-%d-%H-%M-%S")
    liff_url = liff_url_base + f'?schedule_id={schedule_id}'
    message = TextSendMessage(text=f"間に合ったかアンケートに回答するのだ!\n{liff_url}")
    line_bot_api.push_message(group_id, messages=message)
    print("定期的な処理が実行されました")
    cancel_timer(timer_id,schedule_id)



def cancel_timer(timer_id, schedule_id):
    if timer_id in timers:
        # タイマーが存在すればキャンセル
        timer = timers[timer_id]
        timer.cancel()
        delete_schedule(schedule_id)

# タイマーキャンセルと同時にスケジュールもdbから消去
def delete_schedule(schedule_id):
    try:
        # 指定されたドキュメントIDに基づいてドキュメントを取得
        schedule_delete = schedules_doc_ref.document(schedule_id)
        
        # ドキュメントが存在するか確認
        if schedule_delete.get().exists:
            # ドキュメントを削除
            schedule_delete.delete()
            print(f"スケジュール {schedule_id} が削除されました。")
        else:
            print(f"スケジュール {schedule_id} は存在しません。")
    except Exception as e:
        print(f"スケジュールの削除中にエラーが発生しました: {e}")



# Flaskアプリケーションを開始する関数
def start_flask_app():
    app.run(debug=False, port=5002)

if __name__ == "__main__":

    # Flaskアプリケーションを実行するスレッド
    flask_app_thread = threading.Thread(target=start_flask_app)
    flask_app_thread.start()


