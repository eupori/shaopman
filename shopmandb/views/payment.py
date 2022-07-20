from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.parsers import FormParser
from drf_yasg.utils import swagger_auto_schema
from django.http import JsonResponse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from shopmandb.models import *
from rest_framework import serializers
from shopmandb.views import order, views

import xmltodict
import requests
import datetime
import time
import json
import base64
import pandas as pd
import numpy as np
from django.http import JsonResponse
from django.http import Http404


class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentLog
        fields = (
            "receipt_id",
            "price",
            "card_no",
            "card_code",
            "card_name",
            "item_name",
            "order_id",
            "url",
            "payment_name",
            "pg_name",
            "pg",
            "method",
            "method_name",
            "requested_at",
            "purchased_at"
        )


class PaymentPostAPISerializer(serializers.Serializer):
    data = serializers.CharField(max_length=500)
    receipt_id= serializers.CharField(max_length=50)
    billing_key = serializers.CharField(max_length=50)
    sneak_peek = serializers.CharField(max_length=50)


def get_sat():
    payload=f'client_id={settings.OIDC_RP_CLIENT_ID}&client_secret={settings.OIDC_RP_CLIENT_SECRET}&grant_type=client_credentials'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    sat_response = requests.request("POST", settings.OIDC_OP_TOKEN_ENDPOINT, headers=headers, data=payload)
    return json.loads(sat_response.text)['access_token']

def search_user(username, SAT):
    headers = {
        "Authorization" : f"Bearer {SAT}"
    }
    sat_response = requests.request("GET", settings.OIDC_OP_SEARCH_ENDPOINT+f"?username={username}", headers=headers)
    return json.loads(sat_response.text), sat_response.status_code

def get_payload_from_token(request):  # 헤더에서 토큰만 반환
    auth = request.META.get('HTTP_TOKEN', b'').split(".")[1]
    auth += "=" * ((4 - len(auth) % 4) % 4)
    return json.loads(base64.b64decode(auth).decode("utf-8"))

def get_uat_from_refresh_token(refresh_token):
    payload=f'client_id={settings.OIDC_RP_CLIENT_ID}&client_secret={settings.OIDC_RP_CLIENT_SECRET}&grant_type=refresh_token&refresh_token={refresh_token}'
    headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
    }
    sat_response = requests.request("POST", settings.OIDC_OP_TOKEN_ENDPOINT, headers=headers, data=payload)
    return json.loads(sat_response.text), sat_response.status_code

def get_username_from_uat(request):
    refresh_token = request.META.get('HTTP_REFRESHTOKEN', b'')
    token = request.META.get('HTTP_TOKEN', b'')
    context = {}
    # OIDC_OP_USER_ENDPOINT
    if refresh_token == b'' or token == b'':
        return JsonResponse({"status":"blank", "msg":"token, refresh_token blank"}, status=401), False
    payload = get_payload_from_token(request)

    exp = datetime.datetime.fromtimestamp(int(payload['exp']))
    is_refresh = False
    if datetime.datetime.now() > exp:
        tokens, status = get_uat_from_refresh_token(refresh_token)
        if status == 200:
            context['token'] = tokens['access_token']
            
            is_refresh = True
        else:
            return JsonResponse({"status":"expire", "msg":"token, refresh_token expire"}, status=401), False
    else:
        context['token'] = token
    context['sub'] = payload['sub']
    context['username'] = payload["preferred_username"]
    return context, True

def jmf_user_check(id):
    url = "http://bestfruit.godomall.com/api/ig_member_info.php"
    data={'ig_key': settings.JMF_API_KEY,
    'ig_type': 'infoMember',
    'memId': id}
    response = requests.request("POST", url, data=data)
    
    return json.loads(json.dumps(xmltodict.parse(response.text)))['igData']

def jmf_user_deposit_edit(id, val, reason_code):
    url = "http://bestfruit.godomall.com/api/ig_member_info.php"
    data={'ig_key': settings.JMF_API_KEY,
    'ig_type': 'memberDeposit',
    'memId': id,
    'deposit': str(int(val)*-1),
    'reasonCd': reason_code}
    response = requests.request("POST", url, data=data)
    return json.loads(json.dumps(xmltodict.parse(response.text)))['igData']


def jmf_user_mileage_edit(id, val, reason_code):
    url = "http://bestfruit.godomall.com/api/ig_member_info.php"
    data={'ig_key': settings.JMF_API_KEY,
    'ig_type': 'memberMileage',
    'memId': id,
    'mileage': str(int(val)*-1),
    'reasonCd': reason_code}
    response = requests.request("POST", url, data=data)
    return json.loads(json.dumps(xmltodict.parse(response.text)))['igData']

def make_order(real_result,sneak_peek, order_id):
    box = Box.objects.get(identifier=real_result["box_id"])

    final_price = box.price - int(real_result["mileage"]) - int(real_result["deposit"])
    userbox_id = real_result["user_box_id"]
    userbox = UserBox.objects.get(identifier=userbox_id)
    value = userbox.value

    amount = 1

    sub = Subscription.objects.create(
        identifier=order.create_sub_identifier(),
        shipping_range=real_result["range"] if not sneak_peek else "sneak",
        weekday=real_result["weekday"] if not sneak_peek else "sneak",
        expected_day= datetime.datetime.strptime(str(datetime.datetime.today().date()),'%Y-%m-%d') + 
        datetime.timedelta(days=7*(int(real_result["range"])+1)) if not sneak_peek else None,
        user_id=real_result['user_id'],
        box= box,
        card = real_result['card'],
        survey_id = real_result['survey_ids'],
        recipient_name=real_result["recipient_name"],
        recipient_phone=real_result["recipient_phone"],
        shipping_name=real_result["shipping_name"],
        post_number=real_result["post_number"],
        address=real_result["address"],
        address_detail=real_result["detail_address"],
        entrance_password=real_result["entrance_password"],
        request=real_result["request"],
        is_active = "0" if not sneak_peek else "2",
    )

    new_order = Order.objects.create(
        identifier=order_id,
        user_id=real_result['user_id'],
        orderer_name = real_result['orderer_name'],
        orderer_phone = real_result['orderer_phone'],
        recipient_name=real_result["recipient_name"],
        recipient_phone=real_result["recipient_phone"],
        shipping_name=real_result["shipping_name"],
        post_number=real_result["post_number"],
        address=real_result["address"],
        address_detail=real_result["detail_address"],
        shipping_fee=int(real_result["final_price"]) + int(real_result["mileage"]) - int(real_result["price"]),
        price=int(real_result["price"]),
        amount=amount,
        mileage=real_result["mileage"],
        deposit=real_result["deposit"],
        payment_type= real_result["payment_type"],
        final_price=int(real_result["final_price"]),
        is_paid=True,
        status="20",
        card=str(real_result["card"]),
        is_dawn=real_result["is_dawn"],
        request=real_result["request"],
        estimate_date=real_result['estimate_date'] if not sneak_peek else None,
        # estimate_date=real_result['estimate_date'],
        entrance_password=real_result["entrance_password"],
        mileage_status="2",
        sub=sub,
        is_test= False if not sneak_peek else True 
    )

    userbox.subscription = sub
    userbox.order = new_order
    userbox.is_seleted = True if not sneak_peek else False
    userbox.save()

    target_id = userbox.target
    order_userbox = UserBox.objects.filter(target = target_id)
    order_userbox.update(subscription=sub)

    return new_order

class PaymentValidationView(APIView):
    permission_classes = [permissions.AllowAny,]
    
    @swagger_auto_schema(request_body=PaymentPostAPISerializer(),)
    def post(self, request, *args, **kwargs):
        refresh_token = request.META.get('HTTP_REFRESHTOKEN', b'')
        token = request.META.get('HTTP_TOKEN', b'')
        # data= request.POST.get("data")
        context = {}
        context['token'] = token

        #token을 디코딩 -> exp 확인 날자가 지나면 tokken을 재발급(refresh 토큰을 이용해서)
        payload = get_payload_from_token(request)
        exp = datetime.datetime.fromtimestamp(int(payload['exp']))

        is_refresh = False
        if datetime.datetime.now() > exp:
            tokens, status = get_uat_from_refresh_token(refresh_token)
            if status == 200:
                context['refresh_token'] = tokens['refresh_token']
                context['token'] = tokens['access_token']
                is_refresh = True
            else:
                Log.objects.create(
                    url = "/payment_validation",
                    method = "POST",
                    request_code = request.POST,
                    response_code = "401",
                    message = "token, refresh_token expire",
                    user_id = "unknown"
                )
                return JsonResponse({"status":"expire", "msg":"token, refresh_token expire"}, status=401)

        context, status = get_username_from_uat(request)
        username = context['username']
        users, status = search_user(username, get_sat()) 
        attr_dict = {
            "name":"",
            "phone":"",
        }
        is_fruit_match = False
        for item in users:
            if item['id'] == context['sub']:
                if 'attributes' in item:
                    if "name" in item['attributes']:
                        attr_dict['name'] = item['attributes']['name'][0]
                    if "phone" in item['attributes']:
                        attr_dict['phone'] = item['attributes']['phone'][0]
                    if "fruit_match" in item['attributes']:
                        is_fruit_match = True
                break

        #결제 access key 발급
        headers = {"Content-Type": "application/json"}
        data = '{"application_id": "5ffd22185b294800202a17fc", "private_key": "XNUYmHvVSUhY6nxtbqoLsOQL11ZuLm9cKOEXJZCR1Xc="}'
        response = requests.post("https://api.bootpay.co.kr/request/token", headers=headers, data=data)
        response = json.loads(response.text)

        request_json = json.loads(request.POST.get("data"))

        #결제 요청
        receipt_id=request.POST.get("receipt_id")
        billing_key = request.POST.get("billing_key")
        sneak_peek = request.POST.get("sneak_peek")
        sneak_peek = True if sneak_peek == 'true' else False
        item_name = "과일궁합 정기배송"
        # order_id = str(int(round(time.time() * 1000)))
        order_id = order.create_order_identifier()
        headers = {"Authorization": response['data']['token']}
        body = {"billing_key": billing_key, "price": request_json["final_price"], "item_name": item_name, "order_id": order_id, "tax_free":request_json["final_price"]}
        response = requests.request("POST", "https://api.bootpay.co.kr/subscribe/billing", headers=headers, data=body)
        response_data = json.loads(response.text)["data"]

        Log.objects.create(
                url = "/bootpay",
                method = "POST",
                request_code = request.POST,
                response_code = "200",
                message = json.dumps(response_data),
                user_id = "unknown"
            )

        response = requests.request("GET", "https://api.bootpay.co.kr/receipt/"+response_data["receipt_id"], headers=headers)

        prev_user_box = UserBox.objects.get(identifier=request_json['user_box_id'])
        
        user_box = UserBox.objects.get(target=prev_user_box.target,is_selected=True)
        user_box.is_selected = False
        user_box.save()

        prev_user_box.is_selected = True
        prev_user_box.save()


        if(response.status_code == 200 ):
            try:
                #주문서 생성
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
                card = json.dumps(card)

                parm = {
                    "user_id" : username,
                    "username" : request_json['username'],   # 설문조사 시 입력한 이름(주문자 이름)
                    "box_id" : request_json['box_id'],      # 50000, 70000, 90000
                    "deposit" : request_json['deposit'],
                    "mileage" : request_json['mileage'],
                    "price" : request_json['price'],
                    "final_price" : request_json['final_price'],
                    "orderer_phone" : attr_dict['phone'],
                    "orderer_name" : attr_dict['name'],
                    "recipient_name" : request_json['recipient_name'],
                    "shipping_name" : request_json['shipping_name'],
                    "post_number": request_json['post_number'],
                    "address" : request_json['address'],
                    "detail_address" : request_json['detail_address'],
                    "entrance_password" : request_json['entrance_password'],
                    "recipient_phone" : request_json['recipient_phone'],
                    "request" : request_json['request'],
                    "is_dawn" : request_json['is_dawn'],   #새벽배송 여부
                    "range" : request_json['range'],     # 2주에 한번
                    "weekday" : request_json['weekday'],    # 수
                    "payment_type" : request_json['payment_type'],
                    "estimate_date" : request_json['estimate_date'],     # 배송 예정일
                    "user_box_id" : request_json['user_box_id'],          # 추천 과일로 구성된 과일 박스(UserBox)
                    "card": card,
                    "survey_ids": request_json['survey_ids']
                }
                order_response = make_order(parm, sneak_peek, order_id)
                views.send_order_email(order_response)

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
                    order=order_response,
                    user_id=username
                    )

                Log.objects.create(
                    url = "/payment_validation",
                    method = "POST",
                    request_code = request.POST,
                    response_code = "200",
                    message = json.dumps(parm),
                    user_id = "unknown"
                )

                
                if int(request_json['mileage']) > 0:
                    mileage_response = jmf_user_mileage_edit(order_response.user_id, int(request_json['mileage']),'01005001') # 마일리지 사용
                    if mileage_response['result'] == '200':
                        print('마일리지 차감 성공')
                        order_response.mileage_status = '2'
                        order_response.save()
                    else:
                        print('마일리지 차감 실패')
                        print(mileage_response)
                    
                return JsonResponse({"message":"success", "purchased_time":str(datetime.datetime.now()), "token":context['token']}, status=response.status_code)

            except Exception as e:

                Log.objects.create(
                    url = "/payment_validation",
                    method = "POST",
                    request_code = request.POST,
                    response_code = "500",
                    message = e,
                    user_id = "unknown"
                )

                #인증키 발급
                headers = {"Content-Type": "application/json"}
                data = '{"application_id": "5ffd22185b294800202a17fc", "private_key": "XNUYmHvVSUhY6nxtbqoLsOQL11ZuLm9cKOEXJZCR1Xc="}'
                response = requests.post("https://api.bootpay.co.kr/request/token", headers=headers, data=data)
                response = json.loads(response.text)

                #취소 요청
                receipt_id=request.POST.get("receipt_id")
                headers = {"Authorization": response['data']['token']}
                body = {"receipt_id": response_data["receipt_id"], "price": request_json["final_price"], "name": username, "reason": "주문 실패"}
                response = requests.request("POST", "https://api.bootpay.co.kr/cancel", headers=headers, data=body)
                response_data = json.loads(response.text)
                if response.status_code == 500:
                    return JsonResponse({"message":response_data['message'], "reason":response_data, "token":context['token']},status=500)
                else:
                    response_data = response_data["data"]

                if response.status_code == 200:
                    payment_log = PaymentLog.objects.create(
                            receipt_id=response_data["receipt_id"],
                            price=response_data['request_cancel_price'],
                            item_name = "과일궁합 정기배송",
                            payment_name = "결제 취소",
                            pg_order_id = response_data['tid'],
                            purchased_at = response_data['revoked_at'],
                            user_id=username
                            )
                    return JsonResponse({"message":"주문 중 오류가 발생하여 결제가 취소되었습니다." + str(e)  , "token":context['token']},status=500)
                else:
                    return JsonResponse({"message":"처리중 오류가 발생했습니다.", "token":context['token']},status=500)
                return JsonResponse({"data":"fail", "token":context['token']}, status=400)
        else:
            Log.objects.create(
                url = "/payment_validation",
                method = "POST",
                request_code = request.POST,
                response_code = "500",
                message = e,
                user_id = "unknown"
            )


        return JsonResponse({"message":"fail", "purchased_time":response_data["purchased_at"], "token":context['token']}, status=400)


class Feedback(APIView):
    permission_classes = [permissions.AllowAny,]
    def post(self, request, *args, **kwargs):
        return HttpResponse("OK", content_type='text/plain')
