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
import pytz
import threading
import uuid

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
        
        # group_id = events.source.group_id
        # group_doc = group_doc_ref.document(group_id) 
        # schedule_data = group_doc.get().to_dict()["schedule"]
        # schedule_time = datetime.strptime(schedule_data, "%Y年%m月%d日%H時%M分")
        # schedule_time_pytz = jp_timezone.localize(schedule_time)
        daily_schedule()
        return 'OK'
    else:
        return 'OK'


# 定期実行する処理
# 時間になったら実行する処理
def scheduled_task(group_id,timer_id):
    liff_url = f"間に合ったかアンケートを入力するのだ！！\n{liff_url_base}?group_id={group_id}"
    message = TextSendMessage(text=f"{liff_url}")
    line_bot_api.push_message(group_id, messages=message)
    print("定期的な処理が実行されました")
    cancel_timer(timer_id)

# 毎日0時に実行される処理
def daily_schedule():
    print("daily_scheduleが実行されました")
    today_schedules = daily_get_list()
    for schedule in today_schedules:
        time=schedule.to_dict()["datetime"]
        time=jp_timezone.localize(datetime.strptime(time, "%Y年%m月%d日%H時%M分"))
        current_time = datetime.now(pytz.timezone('Asia/Tokyo'))
        delay = max(0, (time - current_time).total_seconds())
        timer_id = str(uuid.uuid4()) 
        # タイマーを設定してイベントをスケジュール
        timer = threading.Timer(delay, scheduled_task, args=(schedule.to_dict()["group_id"], timer_id))
        timer.start()
        timers[timer_id] = timer 

def daily_get_list():
    # レコードから今日の日付と同じ日時のものを選択
    today_schedules = []
    
    today = datetime.now(jp_timezone).replace(hour=0, minute=0, second=0, microsecond=0)
    for doc in schedules_doc_ref.stream():
        schedule_data = doc.to_dict()
        if "datetime" in schedule_data:
            schedule_datetime = jp_timezone.localize(datetime.strptime(schedule_data["datetime"], "%Y年%m月%d日%H時%M分"))
            if schedule_datetime.date() == today.date():
                today_schedules.append(doc)
    return today_schedules

def cancel_timer(timer_id):
    if timer_id in timers:
        # タイマーが存在すればキャンセル
        timer = timers[timer_id]
        timer.cancel()
        del timers[timer_id]

# daily_schedule関数を毎日0時に呼び出す
# schedule_daily_job(daily_schedule)
if __name__ == "__main__":
    app.run(debug=False,port=5002)
