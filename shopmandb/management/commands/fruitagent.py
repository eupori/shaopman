from django.core.management.base import BaseCommand, CommandError
from shopmandb.models import *
from shopmandb.views import *
from django.conf import settings

import shopmandb.models as models
import requests
import datetime
import time
import json

def send_notification(firebase_data, title, body, tab):
    headers = {
        "Authorization": settings.FIREBASE_AUTH_TOKEN,
        "Content-Type": "application/json; UTF-8",
    }
    payload = {
        "to": firebase_data,
        "notification": {
            "body": body,  # 메시지 알림 내용 (상단바-알림창에 출력될 내용)
            "title": title,  # 메시지 알림 제목 (상단바-알림창에 출력될 제목)
            "android_channel_id": "1",
            "tag": str(datetime.datetime.now()),
        },
        "data": {
            "body": body,  # 메시지 내용(앱 - 채팅 탭에서 확인 가능)
            "title": title,  # 메시지 제목(앱 - 채팅 탭에서 확인가능 / 없어도 됨)
            "tab": tab,
            "click_action": "NOTIFICATION_REDIRECT_MARCROGEN",
        },
    }
    if firebase_data is not None:
        response = requests.post(
            settings.FIREBASE_SEND_MESSAGE_URL, data=json.dumps(payload), headers=headers
        )
def do_d_day(subscription):
        #구독 ID, 배송 주기, 요일, 결제 예정일, 사용자 id, box, 결제 정보, 설문조사 id
        #설문조사 리스트를 통해 과일 추천 받기
        
        header = {"api-key":settings.FRUITS_API_KEY}
        recommend_fruits = requests.request("GET", settings.FRUITS_URL+
                        "/api/survey/sub?survey_ids="+subscription.survey_id+"&username="+
                        subscription.user_id, headers=header)     #fruit에 api 요청

        try:

            result = []
            input_data = json.loads(recommend_fruits.text)["data"]
            status, res_list = create_userbox(None, input_data, subscription.box, subscription.user_id, False, subscription)
        except Exception as e:
            AgentLog.objects.create(
                user_id = subscription.user_id,
                subscription = subscription,
                status = 500,
                message = e
            )
            raise ValueError("올바르지 않은 값입니다.")
            

        if len(res_list) == 0:
            # 조합이 안될시
            pass
        #app에 추천된 박스 notification
        #firebase fcm 이용

        header = {"api-key":settings.FRUITS_API_KEY}
        user_data = requests.request("GET", settings.FRUITS_URL+"/api/user/"+subscription.user_id, headers=header)  #fruit에 api 요청
        user = json.loads(user_data.text)
        token = user["firebase_token"]
        title = f"과일궁합"
        body = "다음 배송될 과일이 추천되었습니다. 항목을 선택해주세요."
        
        send_notification(token, title, body, 1)

        AgentLog.objects.create(
                user_id = subscription.user_id,
                subscription = subscription,
                status = 200,
                message = "박스 생성 및 노티 발송 성공"
            )

        #앱이랑 추천 과일 주고 받는 api 필요

        #userbox 저장

        #Q:사용자가 선택 항목을 바꾸면?
        #A:디비에 저장한 후 변경한다.

def do_d_day_2d(subscription):
    # 결제 및 주문서 생성 
    # user_box = subscription.userbox_set.filter(is_selected=True).last()
    target = UserBox.objects.filter(subscription=subscription).last().target
    user_box = UserBox.objects.get(target=target, is_selected=True)
    # 자동 결제 
    # 결제가 성공하면, 주문을 생성한다. 
    # subscription 업데이트 
    # 자동 실행 수행 결과 

    headers = {"Content-Type": "application/json"}
    data = '{"application_id": "5ffd22185b294800202a17fc", "private_key": "XNUYmHvVSUhY6nxtbqoLsOQL11ZuLm9cKOEXJZCR1Xc="}'
    response = requests.post("https://api.bootpay.co.kr/request/token", headers=headers, data=data)
    response = json.loads(response.text)
    
    card = json.loads(subscription.card)

    print("subsription : ", subscription.id)
    print("subsription : ", subscription.card)
    print("subsription : ", type(subscription.card))
    print("card type : ", type(card))
    print("card : ", card)

    receipt_id=card["receipt_id"]
    billing_key = card["billing_key"]
    # receipt_id="6034ba4623868400210270fe"
    # billing_key = "6034ba4523868400250263f2"
    item_name = "과일궁합 정기배송"
    # order_id = str(int(round(time.time() * 1000)))
    order_id = order.create_order_identifier()
    headers = {"Authorization": response['data']['token']}
    body = {"billing_key": billing_key, "price": subscription.box.price, "item_name": item_name, "order_id": order_id, "tax_free": subscription.box.price}
    # body = {"billing_key": billing_key, "price": 1000, "item_name": item_name, "order_id": order_id}
    response = requests.request("POST", "https://api.bootpay.co.kr/subscribe/billing", headers=headers, data=body)
    response_data = json.loads(response.text)["data"]

    print(response.status_code)
    print(response.text)
    print("response_data : ")
    print(json.loads(response.text))
    
    if response.status_code == 200:
        response = requests.request("GET", "https://api.bootpay.co.kr/receipt/"+receipt_id, headers=headers)
    else:
        AgentLog.objects.create(
                user_id = subscription.user_id,
                subscription = subscription,
                status = response.status_code,
                message = "구독 주문 결제 실패."+json.loads(response.text)["message"]
            )
        return False

    print("결제 성공")
    
    if(response.status_code == 200):
        try:
            #주문서 생성
            #구독 생성
            #카드 정보 등록
            #hlkim
            card = {
                "private_key": "XNUYmHvVSUhY6nxtbqoLsOQL11ZuLm9cKOEXJZCR1Xc",
                "application_id": "5ffd22185b294800202a17fc",
                "billing_key": billing_key,
                "receipt_id": response_data["receipt_id"],
                "price": response_data["price"],
                "card_no": response_data["card_no"],
                "card_code": response_data["card_code"],
                "card_name": response_data["card_name"],
                "item_name": response_data["item_name"],
                "order_id": response_data["order_id"],
                "url": response_data["url"],
                "payment_name": response_data["payment_name"],
                "pg_name": response_data["pg_name"],
                "pg": response_data["pg"],
                "method": response_data["method"],
                "method_name": response_data["method_name"],
                "requested_at": response_data["requested_at"],
                "purchased_at": response_data["purchased_at"],
            }

        
            before_order = Order.objects.filter(sub__identifier=subscription.identifier).last()
            if not before_order is None:

                parm = {
                    "user_id" : subscription.user_id,
                    "username" : subscription.recipient_name,   # 설문조사 시 입력한 이름(주문자 이름)
                    "box_id" : subscription.box.identifier,      # 50000, 70000, 90000
                    "deposit" : 0,
                    "mileage" : 0,
                    "recipient_name" : subscription.recipient_name,
                    "shipping_name" : subscription.shipping_name,
                    "post_number": subscription.post_number,
                    "address" : subscription.address,
                    "detail_address" : subscription.address_detail,
                    "entrance_password" : subscription.entrance_password,
                    "recipient_phone" : subscription.recipient_phone,
                    "request" : subscription.request,
                    "is_dawn" : before_order.is_dawn,   #새벽배송 여부
                    "range" : subscription.shipping_range,     # 2주에 한번
                    "weekday" : subscription.weekday,    # 수
                    "payment_type" : before_order.payment_type,
                    "estimate_date" : before_order.estimate_date+datetime.timedelta(days=(int(subscription.shipping_range)+1)*7),     # 배송 예정일
                    "user_box_id" : user_box.identifier,          # 추천 과일로 구성된 과일 박스(UserBox)
                    "card": json.dumps(subscription.card),
                    "survey_ids": subscription.survey_id
                }
                box = Box.objects.get(identifier=parm["box_id"])

                final_price = box.price - int(parm["mileage"]) - int(parm["deposit"])
                userbox_id = parm["user_box_id"]
                userbox = UserBox.objects.get(identifier=userbox_id)
                value = userbox.value

                amount = 1

                order_obj = Order.objects.create(
                    identifier=order_id,
                    user_id=parm['user_id'],
                    orderer_name=parm["recipient_name"],
                    recipient_name=parm["recipient_name"],
                    recipient_phone=parm["recipient_phone"],
                    shipping_name=parm["shipping_name"],
                    post_number=parm["post_number"],
                    address=parm["address"],
                    address_detail=parm["detail_address"],
                    shipping_fee=0,
                    price=box.price,
                    amount=amount,
                    mileage=parm["mileage"],
                    deposit=parm["deposit"],
                    payment_type= parm["payment_type"],
                    final_price=final_price,
                    is_paid=True,
                    status="20",
                    mileage_status="2",
                    is_dawn=parm["is_dawn"],
                    request=parm["request"],
                    estimate_date=parm["estimate_date"],
                    entrance_password=parm["entrance_password"],
                    card=parm["card"],
                    sub=subscription
                )

                userbox.subscription = subscription
                userbox.order = order_obj
                userbox.save()

                views.send_order_email(order_obj)

                payment_log = PaymentLog.objects.create(
                    receipt_id=response_data["receipt_id"],
                    price=response_data["price"],
                    card_no=response_data["card_no"],
                    card_code=response_data["card_code"],
                    card_name=response_data["card_name"],
                    item_name=response_data["item_name"],
                    pg_order_id=response_data["order_id"],
                    url=response_data["url"],
                    payment_name=response_data["payment_name"],
                    pg_name=response_data["pg_name"],
                    pg=response_data["pg"],
                    method=response_data["method"],
                    method_name=response_data["method_name"],
                    requested_at=response_data["requested_at"],
                    purchased_at=response_data["purchased_at"],
                    order=order_obj,
                    user_id=parm['user_id']
                    )

                if order_obj is not None:
                    #갱신
                    subscription.expected_day = subscription.expected_day + datetime.timedelta(days=(int(subscription.shipping_range)+1)*7)

                    print("estimated_date :", parm['estimate_date'])
                    # subscription.expected_day = parm['estimate_date'] - datetime.timedelta(days=7)
                    print("다음 결제 예정일 : ", subscription.expected_day)
                    subscription.save()

                    header = {"api-key":settings.FRUITS_API_KEY}
                    user_data = requests.request("GET", settings.FRUITS_URL+"/api/user/"+subscription.user_id, headers=header)  #fruit에 api 요청
                    user = json.loads(user_data.text)
                    token = user["firebase_token"]
                    title = f"과일궁합"
                    body = "정기배송 결제가 완료되었습니다."
                    send_notification(token, title, body, 1)

                    print("결제 완료", parm['user_id'])

                    AgentLog.objects.create(
                        user_id = subscription.user_id,
                        subscription = subscription,
                        status = 200,
                        message = "결제 및 주문 성공"
                    )
        except Exception as e:
            print(e)
            #인증키 발급
            headers = {"Content-Type": "application/json"}
            data = '{"application_id": "5ffd22185b294800202a17fc", "private_key": "XNUYmHvVSUhY6nxtbqoLsOQL11ZuLm9cKOEXJZCR1Xc="}'
            response = requests.post("https://api.bootpay.co.kr/request/token", headers=headers, data=data)
            response = json.loads(response.text)

            #취소 요청
            receipt_id=response_data["receipt_id"]
            headers = {"Authorization": response['data']['token']}
            body = {"receipt_id": receipt_id, "price": subscription.box.price, "name": subscription.user_id, "reason": "주문 실패"}
            response = requests.request("POST", "https://api.bootpay.co.kr/cancel", headers=headers, data=body)
            response_data = json.loads(response.text)
            if response.status_code == 500:
                AgentLog.objects.create(
                        user_id = subscription.user_id,
                        subscription = subscription,
                        status = 500,
                        message = "결제 취소 실패."+e
                    )
                return False
            else:
                response_data = response_data["data"]

            print(response_data)

            if response.status_code == 200:
                payment_log = PaymentLog.objects.create(
                    receipt_id=response_data["receipt_id"],
                    price=response_data['request_cancel_price'],
                    item_name = "과일궁합 정기배송",
                    payment_name = "결제 취소",
                    pg_order_id = response_data['tid'],
                    purchased_at = response_data['revoked_at'],
                    user_id=subscription.user_id
                    )

                AgentLog.objects.create(
                        user_id = subscription.user_id,
                        subscription = subscription,
                        status = 500,
                        message = "구독 주문 생성 실패."+e
                    )
                return False
            else:
                AgentLog.objects.create(
                        user_id = subscription.user_id,
                        subscription = subscription,
                        status = 500,
                        message = "결제 취소 실패."+e
                    )
                return False
            return False


class Command(BaseCommand):
    help = 'Automatic agent for fruits shopman'


    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        original = None
        today = datetime.date.today()
        print(today)
        after_two_days = today + datetime.timedelta(days=2)
        # after_two_days = today + datetime.timedelta(minutes=1)

        #주문 예정일을 통해서 박스 조합
        #결제 예정일의 2일 전에 박스 조합
        for subscription in Subscription.objects.filter(expected_day=after_two_days, is_active="0"):
            do_d_day(subscription=subscription)
            print(subscription.user_id)
            print("make userbox")

        #결제 2일전에 만들어진 박스를 이용해 결제 및 주문 생성
        for subscription in Subscription.objects.filter(expected_day=today, is_active="0"):
            do_d_day_2d(subscription)
            print(subscription.user_id)
            print("payment success")