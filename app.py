from flask import Flask, request, abort, render_template

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError, LineBotApiError
)

from linebot.models import MessageEvent, TextMessage, ConfirmTemplate, TemplateSendMessage, PostbackAction, TextSendMessage, PostbackEvent, SourceGroup, FlexSendMessage, BubbleContainer, TextComponent, BoxComponent, ButtonComponent, PostbackAction, DatetimePickerAction, JoinEvent

from linebot.models import CarouselContainer, FlexSendMessage, BubbleContainer, ImageComponent, BoxComponent, TextComponent, ButtonComponent, URIAction

from time import sleep

from linebot.models import (
    TextSendMessage,
    QuickReply,
    QuickReplyButton,
    PostbackAction,
)

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
question_url_base = "https://liff.line.me/2002096181-Ryql27BY"
gifts_url_base = "https://liff.line.me/2002642249-Lq0RX2ZN"

# ユーザー状態を保存
user_states = {}

# データベース使い方
schedule_format = {
    "username": [],
    "answer": [],
    "num_of_people": 99,
    "datetime": None,
    "group_id": None,
    "min_price": 0, 
    "max_price": None,
}

format={
    "username":[],
    "answer":[],
    "group_count":None,
    "schedule_id":None,
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
    group_doc = group_doc_ref.document(group_id)
    members_count = line_bot_api.get_group_members_count(group_id)

    format['group_count'] = members_count

    group_doc = group_doc_ref.document(group_id) #ドキュメントを生成
    group_doc.set(format)
    welcome_message = f"よろしくなのだ！予定の日時を登録したいときは「予定登録」と送るのだ！"
    
    line_bot_api.push_message(
        group_id,
        TextSendMessage(text=welcome_message)
    )

@handler.add(MessageEvent, message=TextMessage)
def handle_message(events):

    if events.message.text.lower() == "予定登録":
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

    elif events.message.text.lower() == "予定確認":
        group_id = events.source.group_id
        query = schedules_doc_ref.where('group_id', '==', group_id)

        # クエリを実行してデータを取得
        docs = query.stream()

        # データをリストに格納
        datas= []
        
        for doc in docs:
            datas.append(doc.to_dict())

        # 条件に一致するドキュメントがない場合は空のリストを返す
        if not datas:
            line_bot_api.reply_message(
                events.reply_token,
                TextSendMessage(text="予定が登録されていないのだ！")
            )
        
        else:
            messages = []
            for data in datas:
                message = TextSendMessage(text=f"約束の時間は{data['datetime']}\n人数は{data['num_of_people']}人\n送るギフトの価格帯は¥{data['min_price']}~¥{data['max_price']}なのだ！")
                messages.append(message)

            # 一度に複数のメッセージを送信
            line_bot_api.reply_message(events.reply_token, messages)


    # elif events.message.text.lower() == "テスト":
    #     group_id = events.source.group_id
    #     group_doc = db.collection('groups').document(group_id).get()
    #     group_data = group_doc.to_dict()
    #     min_price = 0
    #     max_price = 1000

    #     if 'min_price' in group_data:
    #         min_price = group_data['min_price']
    #     if 'max_price' in group_data:
    #         max_price = group_data['max_price']
    #     print("min_price:", min_price)
    #     print("max_price:", max_price)

    #     liff_url = f"{gifts_url_base}?min_price={min_price}&max_price={max_price}"

    #     line_bot_api.reply_message(events.reply_token, TextSendMessage(text=f"ギフト一覧なのだ！\n{liff_url}"))

        
    # elif events.message.text.lower() == "ギフト設定":
    #     carousel_container = CarouselContainer(
    #         contents=[
    #             BubbleContainer(
    #                 size='micro',
    #                 hero=ImageComponent(
    #                     url="https://d.line-scdn.net/stf/line-mall/item-photo-7203592-34809838.jpg?63448310c83a48fde0877ceb6f5dd027",
    #                     size="full",
    #                     aspect_ratio="3:2",
    #                     aspect_mode="cover",
    #                     action=PostbackAction(label="View", data="1-100")
    #                 ),
    #                 body=BoxComponent(
    #                     layout="vertical",
    #                     contents=[
    #                         TextComponent(text="~¥100", size="md", weight="bold", align="center"),
    #                     ]
    #                 )
    #             ),
    #             BubbleContainer(
    #                 size='micro',
    #                 hero=ImageComponent(
    #                     url="https://d.line-scdn.net/stf/line-mall/item-photo-7051436-38009042.jpg?82b2f5e297660b191f058b866ea2def5",
    #                     size="full",
    #                     aspect_ratio="3:2",
    #                     aspect_mode="cover",
    #                     action=PostbackAction(label="View", data="101-300")
    #                 ),
    #                 body=BoxComponent(
    #                     layout="vertical",
    #                     contents=[
    #                         TextComponent(text="¥101~¥300", size="md", weight="bold", align="center"),
    #                     ]
    #                 )
    #             ),
    #             BubbleContainer(
    #                 size='micro',
    #                 hero=ImageComponent(
    #                     url="https://d.line-scdn.net/stf/line-mall/item-photo-3669558-38454203.jpg?aec4f17fafbd42bd31771b28b86b4d92",
    #                     size="full",
    #                     aspect_ratio="3:2",
    #                     aspect_mode="cover",
    #                     action=PostbackAction(label="View", data="301-500")
    #                 ),
    #                 body=BoxComponent(
    #                     layout="vertical",
    #                     contents=[
    #                         TextComponent(text="¥301~¥500", size="md", weight="bold", align="center"),
    #                     ]
    #                 )
    #             )
    #         ]
    #     )

    #     flex_message = FlexSendMessage(
    #         alt_text='Flex Message',
    #         contents=carousel_container
    #     )
    #     line_bot_api.reply_message(
    #         events.reply_token,
    #         flex_message
    #     )

    # elif events.message.text.lower() == "人数登録":
    #     # ユーザー状態を「人数入力待ち」にする
    #     user_states[events.source.user_id] = "waiting_for_num"
    #     # ユーザーにメッセージを送信
    #     line_bot_api.reply_message(
    #         events.reply_token,
    #         TextSendMessage(text="参加人数を入力してください")
    #     )

    # 入力人数の処理（ユーザー状態が"waiting_for_num"の場合のみ）
    elif events.message.text.isdigit() and user_states.get(events.source.user_id) == "waiting_for_num":
        group_id = events.source.group_id
        group = db.collection('groups').document(group_id)
        schedule_id = group.get().to_dict()["schedule_id"] 
        schedules_doc = schedules_doc_ref.document(schedule_id)
         
        # データをデータベースに保存
        num_of_people = int(events.message.text)
        schedules_doc.update({'num_of_people': num_of_people})
       
        # ユーザー状態をクリア
        del user_states[events.source.user_id]

        # ギフトの価格帯設定
        carousel_container = CarouselContainer(
            contents=[
                BubbleContainer(
                    size='micro',
                    hero=ImageComponent(
                        url="https://d.line-scdn.net/stf/line-mall/item-photo-7203592-34809838.jpg?63448310c83a48fde0877ceb6f5dd027",
                        size="full",
                        aspect_ratio="3:2",
                        aspect_mode="cover",
                        action=PostbackAction(label="View", data="1-100")
                    ),
                    body=BoxComponent(
                        layout="vertical",
                        contents=[
                            TextComponent(text="~¥100", size="md", weight="bold", align="center"),
                        ]
                    )
                ),
                BubbleContainer(
                    size='micro',
                    hero=ImageComponent(
                        url="https://d.line-scdn.net/stf/line-mall/item-photo-7051436-38009042.jpg?82b2f5e297660b191f058b866ea2def5",
                        size="full",
                        aspect_ratio="3:2",
                        aspect_mode="cover",
                        action=PostbackAction(label="View", data="101-300")
                    ),
                    body=BoxComponent(
                        layout="vertical",
                        contents=[
                            TextComponent(text="¥101~¥300", size="md", weight="bold", align="center"),
                        ]
                    )
                ),
                BubbleContainer(
                    size='micro',
                    hero=ImageComponent(
                        url="https://d.line-scdn.net/stf/line-mall/item-photo-3669558-38454203.jpg?aec4f17fafbd42bd31771b28b86b4d92",
                        size="full",
                        aspect_ratio="3:2",
                        aspect_mode="cover",
                        action=PostbackAction(label="View", data="301-500")
                    ),
                    body=BoxComponent(
                        layout="vertical",
                        contents=[
                            TextComponent(text="¥301~¥500", size="md", weight="bold", align="center"),
                        ]
                    )
                )
            ]
        )

        flex_message = FlexSendMessage(
            alt_text='Flex Message',
            contents=carousel_container
        )

 # メッセージを送信
        line_bot_api.reply_message(
            events.reply_token,
            [
                TextSendMessage(text="予定人数を登録したのだ！"),
                TextSendMessage(text="次に遅れたときに送るギフトの価格帯を決めるのだ！"),
                flex_message          
            ]
            
        )






# 予定の保存処理
@handler.add(PostbackEvent)
def handle_postback(events):
    if events.postback.data == 'datetime_postback':

        # group_id = events.source.group_id
        # group_count = events.postback.params['group_count']
        # schedule_format['group_count'] = group_count #group_countをschedule_formatに追加

        # 日時選択のPostbackデータを受け取った場合
        selected_iso_datetime = events.postback.params['datetime']  # ISO 8601 形式の日時文字列

        # ISO 8601 形式の文字列を datetime オブジェクトに変換
        selected_datetime = datetime.fromisoformat(selected_iso_datetime)

        # 日時を指定された形式の文字列に変換
        formatted_datetime = selected_datetime.strftime("%Y年%m月%d日%H時%M分")

        group_id = events.source.group_id
        # 選択された日時に関する処理（必要に応じて）
        schedules_doc = schedules_doc_ref.document()
        # 生成されたドキュメントの ID を取得
        schedule_id = schedules_doc.id
        group_doc_ref.document(group_id).update({'schedule_id': schedule_id})
        
        
        schedule_format['datetime'] = formatted_datetime
        schedule_format['group_id'] = group_id
        schedules_doc.set(schedule_format)

        # ユーザーに対して応答メッセージを送信
        line_bot_api.reply_message(
            events.reply_token,
            [
                TextSendMessage(text=f"{formatted_datetime}に予定が登録されたのだ！"),
                TextSendMessage(text="次に予定に参加する人数を入力するのだ！半角数字のみで頼むのだ！(例: 3)")
                
            ]
        )

        # ユーザー状態を「人数入力待ち」にする
        user_states[events.source.user_id] = "waiting_for_num"
        

    

    if events.postback.data == '1-100':
        group_id = events.source.group_id
        group = db.collection('groups').document(group_id)
        schedule_id = group.get().to_dict()["schedule_id"]
        schedules_doc = schedules_doc_ref.document(schedule_id)
        schedule_data = schedules_doc.get().to_dict()
        
        schedules_doc.update({
            'min_price': 1,
            'max_price': 100
        })

        line_bot_api.reply_message(
            events.reply_token,
            [
                TextSendMessage(text="ギフトの値段が~¥100に設定されたのだ！"),
                TextSendMessage(text=f"約束の時間は{schedule_data['datetime']}\n人数は{schedule_data['num_of_people']}人\n送るギフトの価格帯は~¥100\nで予定登録が完了したのだ！")

            ]
            
            
        )
    elif events.postback.data == '101-300':
        group_id = events.source.group_id
        group = db.collection('groups').document(group_id)
        schedule_id = group.get().to_dict()["schedule_id"]
        schedules_doc = schedules_doc_ref.document(schedule_id)
        schedule_data = schedules_doc.get().to_dict()
        
        schedules_doc.update({
            'min_price': 101,
            'max_price': 300
        })

        line_bot_api.reply_message(
            events.reply_token,
            [
                TextSendMessage(text="ギフトの値段が¥101~¥300に設定されたのだ！"),
                TextSendMessage(text=f"約束の時間は{schedule_data['datetime']}\n人数は{schedule_data['num_of_people']}人\n送るギフトの価格帯は¥101~¥300\nで予定登録が完了したのだ！")
            ]
            
        )
    elif events.postback.data == '301-500':
        group_id = events.source.group_id
        group = db.collection('groups').document(group_id)
        schedule_id = group.get().to_dict()["schedule_id"] 
        schedules_doc = schedules_doc_ref.document(schedule_id)
        schedule_data = schedules_doc.get().to_dict()
        
        schedules_doc.update({
            'min_price': 301,
            'max_price': 500
        })

        line_bot_api.reply_message(
            events.reply_token,
            [
                TextSendMessage(text="ギフトの値段が¥301~¥500に設定されたのだ！"),
                TextSendMessage(text=f"約束の時間は{schedule_data['datetime']}\n人数は{schedule_data['num_of_people']}人\n送るギフトの価格帯は¥301~¥500\nで予定登録が完了したのだ！")
            ]
            
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
    # urlの発行時間を埋め込む
    current_time = datetime.now(pytz.timezone('Asia/Tokyo'))
    # 日時を文字列に変換
    desired_time_str = (current_time + timedelta(minutes=7)).strftime("%H時%M分")

    liff_url = f"{question_url_base}?schedule_id={schedule_id}"
    message = TextSendMessage(text=f"間に合ったか{desired_time_str}までにアンケートに回答するのだ!\n{liff_url}")
    line_bot_api.push_message(group_id, messages=message)
    print("定期的な処理が実行されました")
    cancel_timer(timer_id)

    # 7分後にタイマーを設定してイベントをスケジュール
    timer_id = str(uuid.uuid4()) 
    delay_7 = 7 * 60
    # タイマーを設定してイベントをスケジュール
    timer = threading.Timer(delay_7, delete_schedule, args=(schedule_id, timer_id))
    timer.start()



def cancel_timer(timer_id):
    if timer_id in timers:
        # タイマーが存在すればキャンセル
        timer = timers[timer_id]
        timer.cancel()

# スケジュールもdbから消去
def delete_schedule(schedule_id, timer_id):
    try:
        # 指定されたドキュメントIDに基づいてドキュメントを取得
        schedule_delete = schedules_doc_ref.document(schedule_id)
        
        # 時間になっても集まってない場合
        if schedule_delete.get().exists:
            min_price = 0
            max_price = 1000
            schedules_doc = schedules_doc_ref.document(schedule_id)
   
            schedule_data = schedules_doc.get().to_dict()
            if 'min_price' in schedule_data:
                min_price = schedule_data["min_price"]
            if 'max_price' in schedule_data:
                max_price = schedule_data['max_price']
        

            liff_url = f"{gifts_url_base}?min_price={min_price}&max_price={max_price}"

            
            message = TextSendMessage(text=f"送るギフトを選ぶのだ！\n{liff_url}")
            group_id = schedules_doc_ref.document(schedule_id).get().to_dict()["group_id"]
            line_bot_api.push_message(group_id, messages=message)          
            # ドキュメントを削除
            schedule_delete.delete()
            cancel_timer(timer_id)
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


