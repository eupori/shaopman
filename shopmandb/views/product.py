from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.parsers import FormParser
from drf_yasg.utils import swagger_auto_schema
from django.http import JsonResponse
from shopmandb.models import *
from shopmandb.views import *
from django.conf import settings
from bs4 import BeautifulSoup
from .payment import *
import requests
import json
import time
import ast
import xmltodict
import datetime
import json
import base64
import pandas as pd
import numpy as np
from django.http import JsonResponse
from django.http import Http404

JMF_API_URL = "https://bestf.co.kr/api/ig_member_info.php"

class ProductGetAPISerializer(serializers.Serializer):
    if_id = serializers.CharField(max_length=50, required=False)

    def get_data_or_errors(self):
        if self.is_valid():
            return True, self.data
        else:
            return False, self.errors

class ProductPostAPISerializer(serializers.Serializer):
    if_id = serializers.CharField(max_length=50, required=False)
    recipient_name = serializers.CharField(max_length=50, required=False)
    recipient_phone = serializers.CharField(max_length=50, required=False)
    shipping_name = serializers.CharField(max_length=50, required=False)
    post_number = serializers.CharField(max_length=50, required=False)
    address = serializers.CharField(max_length=50, required=False)
    detail_address = serializers.CharField(max_length=50, required=False)
    price = serializers.IntegerField(required=False)
    amount = serializers.IntegerField(required=False)
    mileage = serializers.IntegerField(required=False)
    deposit = serializers.IntegerField(required=False)
    option = serializers.CharField(max_length=50, required=False)
    option_price = serializers.IntegerField(required=False)
    final_price = serializers.IntegerField(required=False)
    payment_type = serializers.CharField(max_length=50, required=False)
    is_dawn = serializers.BooleanField(required=False)
    request = serializers.CharField(max_length=500, required=False)
    entrance_password = serializers.CharField(max_length=50, required=False)
    product_id = serializers.CharField(max_length=50, required=False)
    card = serializers.CharField(max_length=500, required=False)

class ProductSerializer(serializers.ModelSerializer):
    content = serializers.SerializerMethodField()
    option = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            "identifier",
            "name",
            "if_id",
            "image_path",
            "price",
            "weight",
            "description",
            "content",
            "maker",
            "origin",
            "min_order_count",
            "max_order_count",
            "is_discount",
            "discount_fee",
            "order_amount",
            "hit_count",
            "is_direct",
            "option",
            "is_active",
            "is_tax_free"
        )
    def get_content(self, obj):
        return ast.literal_eval(obj.content)
    def get_option(self, obj):
        return ast.literal_eval(obj.option)


def jmf_user_check(id):
    url = JMF_API_URL
    data={'ig_key': settings.JMF_API_KEY,
    'ig_type': 'infoMember',
    'memId': id}
    response = requests.request("POST", url, data=data)
    
    return json.loads(json.dumps(xmltodict.parse(response.text)))['igData']

def jmf_user_deposit_edit(id, val, reason_code):
    url = JMF_API_URL
    data={'ig_key': settings.JMF_API_KEY,
    'ig_type': 'memberDeposit',
    'memId': id,
    'deposit': str(int(val)*-1),
    'reasonCd': reason_code}
    response = requests.request("POST", url, data=data)
    return json.loads(json.dumps(xmltodict.parse(response.text)))['igData']


def jmf_user_mileage_edit(id, val, reason_code):
    url = JMF_API_URL
    data={'ig_key': settings.JMF_API_KEY,
    'ig_type': 'memberMileage',
    'memId': id,
    'mileage': str(int(val)*-1),
    'reasonCd': reason_code}
    response = requests.request("POST", url, data=data)
    return json.loads(json.dumps(xmltodict.parse(response.text)))['igData']


class ProductView(APIView):
    permission_classes = [permissions.AllowAny,]
    parser_classes = (FormParser,)
    @swagger_auto_schema(query_serializer=ProductGetAPISerializer(),)

    def get(self, request, *args, **kwargs):
        get_input = ProductGetAPISerializer(data=request.GET)
        # print(get_input.get_data_or_errors()[0] == True)
        refresh_token = request.META.get('HTTP_REFRESHTOKEN', b'')
        token = request.META.get('HTTP_TOKEN', b'')
        context = {}
        context['token'] = token

        #token을 디코딩 -> exp 확인 날자가 지나면 tokken을 재발급(refresh 토큰을 이용해서)
        payload = mix.get_payload_from_token(request)
        exp = datetime.datetime.fromtimestamp(int(payload['exp']))

        is_refresh = False
        if datetime.datetime.now() > exp:
            tokens, status = mix.get_uat_from_refresh_token(refresh_token)
            if status == 200:
                context['refresh_token'] = tokens['refresh_token']
                context['token'] = tokens['access_token']
                is_refresh = True
            else:
                Log.objects.create(
                    url = "/product",
                    method = "GET",
                    request_code = request.GET,
                    response_code = "401",
                    message = "token, refresh_token expire",
                    user_id = "unknown"
                )
                return JsonResponse({"status":"expire", "msg":"token, refresh_token expire"}, status=401)

        if_id=request.GET.get("if_id")
        # product_list = []
        url = "https://openhub.godo.co.kr/godomall5/goods/Goods_Search.php"

        payload={'partner_key': 'JUNBJTEyTCVBQiUxNSVDNiVBNyVBOA==',
        'key': 'JTNEJTgwJTk5JTk4JTFGJUE3JThFJUE4OSVGNiVDNWclQjclQzM2JUYyJUVFJTQwJTA4MCVFRCU3RTUlRjclRDklRTIlQjE0JTI1NiVEQ00lMTJiRiVEQyU5RiUyRiVFRCU1QkJNJUQ4ZA==',
        'goodsCd':if_id if if_id else '',
        'goodsDisplayMobileFl': 'n',
        'cateCd':'002',
        'soldOutFl': 'n',
        'goodsPriceString':None,
        }
        files=[
        ]
        headers = {}
        response = requests.request("POST", url, headers=headers, data=payload, files=files)

        dict_data = json.loads(json.dumps(xmltodict.parse(response.text)))

        if response.status_code != 200 or dict_data["data"]["header"]["code"] != "000":
            return JsonResponse({"data":{"status": response.status_code, "response_code": dict_data["data"]["header"]["code"]}, "token":context['token'], "message": "데이터 호출 중 문제가 발생하였습니다."}, status=response.status_code)

        if dict_data["data"]["header"]["total"] != "0":

            tmp_list = []
            if isinstance(dict_data["data"]["return"]['goods_data'], list):
                tmp_list = dict_data["data"]["return"]['goods_data']
            else:
                tmp_list = [dict_data["data"]["return"]['goods_data']]
            data_list = []
            for each in tmp_list:
                if each['goodsCd'] is not None and 'optionData' in each and each["goodsDisplayMobileFl"] == "y" and each["goodsSellMobileFl"] == "y" and each["soldOutFl"] == "n":
                    if each['goodsDescription'] != '<p>&nbsp;</p>':
                        bsObject = BeautifulSoup(each['goodsDescription'], "html.parser")
                        description_img = []
                        description_ptag = bsObject.find('div')
                        
                        if description_ptag is not None and each['optionData'] is not None:
                            
                            for i in description_ptag.findAll('img'):
                                if "https://www.bestf.co.kr" in i.get('src').split('\\"')[1]:
                                    description_img.append(i.get('src').split('\\"')[1])
                                else:
                                    description_img.append("https://www.bestf.co.kr" + i.get('src').split('\\"')[1])
                                
                            option = {"optionName":each['optionName'],}
                            if isinstance(each['optionData'],list):
                                option_list = each['optionData']
                            else:
                                option_list = [each['optionData']]
                            option["contents"] = []
                            for option_data in option_list:
                                option["contents"].append({
                                    "name":option_data['optionValue1'],
                                    "price":int(float(option_data['optionPrice']))
                                })

                            data = {
                                "identifier": each['goodsNo'],
                                "name": each['goodsNm'],
                                "if_id": each['goodsCd'],
                                "image_path": each['listImageData']['#text'] if 'listImageData' in each else "",
                                "price": int(float(each['goodsPrice'])),
                                "weight": int(float(each['goodsWeight'])),
                                "description": each['shortDescription'],
                                "content": description_img,
                                "maker": each['makerNm'],
                                "origin": each['originNm'],
                                "min_order_count": int(each['minOrderCnt']),
                                "max_order_count": int(each['maxOrderCnt']),
                                "is_discount": False if each['goodsDiscountFl'] == 'n' else True,
                                "discount_fee": int(float(each['goodsDiscount'])),
                                "order_amount": int(each['orderCnt']),
                                "hit_count": int(each['hitCnt']),
                                "option": option,
                                "is_tax_free": False if each["taxFreeFl"] == "t" else True,
                                "is_active": True
                            }               

                            data_list.append(data)
                            Product.objects.update_or_create(identifier=data['identifier'],defaults=data)

            exclude_ids = [item["identifier"] for item in data_list] + ["P00000ZN"]
            Product.objects.exclude(identifier__in=exclude_ids).update(is_active=False)

        username = get_username_from_uat(request)[0]['username']
        if request.GET.get("if_id") is None:
            product_list = Product.objects.filter(is_active=True).order_by('-updated_at')
        else:
            product_list = Product.objects.filter(if_id=request.GET.get("if_id"), is_active=True).order_by('-updated_at')

        if len(product_list) == 0:
            Log.objects.create(
                url = "/product",
                method = "GET",
                request_code = request.GET,
                response_code = "200",
                message = "데이터가 없습니다.",
                user_id = username
            )
            return JsonResponse({"data":[], "message":"데이터가 없습니다.", "token":context['token']})

        product_json = ProductSerializer(product_list, many=True).data

        Log.objects.create(
            url = "/product",
            method = "GET",
            request_code = request.GET,
            response_code = "200",
            message = product_json,
            user_id = username
        )
            
        return JsonResponse({"data":product_json, "token":context['token']})
        # return JsonResponse({"data":data_list, "token":context['token']})
        # return JsonResponse({"data":[], "token":context['token']})

    @swagger_auto_schema(request_body=ProductPostAPISerializer(),)
    def post(self, request, *args, **kwargs):
        refresh_token = request.META.get('HTTP_REFRESHTOKEN', b'')
        token = request.META.get('HTTP_TOKEN', b'')
        # data= request.POST.get("data")
        context = {}
        context['token'] = token

        #token을 디코딩 -> exp 확인 날자가 지나면 tokken을 재발급(refresh 토큰을 이용해서)
        payload = mix.get_payload_from_token(request)
        exp = datetime.datetime.fromtimestamp(int(payload['exp']))

        is_refresh = False
        if datetime.datetime.now() > exp:
            tokens, status = mix.get_uat_from_refresh_token(refresh_token)
            if status == 200:
                context['refresh_token'] = tokens['refresh_token']
                context['token'] = tokens['access_token']
                is_refresh = True
            else:
                Log.objects.create(
                    url = "/product",
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

        mileage = int(request.POST.get("mileage"))
        deposit = int(request.POST.get("deposit"))

        #마일리지, 예치금 확인
        user_info = jmf_user_check(username)

        if (int(float(user_info['igDataVal']['mileage'])) < mileage) or (int(float(user_info['igDataVal']['deposit'])) < deposit):
            Log.objects.create(
                url = "/product",
                method = "POST",
                request_code = request.POST,
                response_code = "402",
                message = "mileage or deposit error",
                user_id = username
            )
            return JsonResponse({"message":"mileage or deposit error", "token":context['token']}, status=402)

        shipping_fee = int(request.POST.get("price")) - Product.objects.get(identifier=request.POST.get("product_id")).price

        if int(request.POST.get("final_price")) == 0:
            if mileage > 0 : 
                jmf_user_mileage_edit(id=username,val=mileage,reason_code="01005001")
            if deposit > 0 : 
                jmf_user_deposit_edit(id=username,val=deposit,reason_code="01006003")

            new_order = Order.objects.create(
                identifier=order.create_order_identifier(),
                user_id=username,
                orderer_name=attr_dict,
                recipient_name=request.POST.get('recipient_name'),
                recipient_phone=request.POST.get("recipient_phone"),
                shipping_name=request.POST.get("shipping_name"),
                post_number=request.POST.get("post_number"),
                address=request.POST.get("address"),
                address_detail=request.POST.get("detail_address"),
                shipping_fee=shipping_fee,
                price=request.POST.get("price"),
                amount=request.POST.get("amount"),
                mileage=request.POST.get("mileage"),
                deposit=request.POST.get("deposit"),
                option=request.POST.get("option"),
                option_price=request.POST.get("option_price"),
                final_price=request.POST.get("final_price"),
                payment_type= request.POST.get("payment_type"),
                is_paid=True,
                status='20',
                is_dawn=True if request.POST.get("is_dawn") == "true" else False,
                product = Product.objects.get(identifier=request.POST.get("product_id")),
                request=request.POST.get("request"),
                entrance_password=request.POST.get("entrance_password"),
                card="",
                mileage_status='2'
                )

            views.send_order_email(new_order)
            payment_log = PaymentLog.objects.create(
                price=0,
                item_name=Product.objects.get(identifier=request.POST.get("product_id")).name,
                order=new_order,
                user_id=username
                )

            Log.objects.create(
                url = "/product",
                method = "POST",
                request_code = request.POST,
                response_code = "200",
                message = new_order,
                user_id = username
            )
            return JsonResponse({"purchased_time":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "token":context['token']}, status=200)
        else:
            headers = {"Content-Type": "application/json"}
            data = '{"application_id": "5ffd22185b294800202a17fc", "private_key": "XNUYmHvVSUhY6nxtbqoLsOQL11ZuLm9cKOEXJZCR1Xc="}'
            response = requests.post("https://api.bootpay.co.kr/request/token", headers=headers, data=data)
            response = json.loads(response.text)

            headers = {"Authorization": response['data']['token']}
            receipt_id=request.POST.get("receipt_id")
            response = requests.request("GET", "https://api.bootpay.co.kr/receipt/"+receipt_id, headers=headers)
            card_data = json.loads(request.POST.get("card"))
            complete_data = datetime.datetime.strptime(card_data['purchased_at'],"%Y-%m-%d %H:%M:%S")

            if(response.status_code == 200):
                if mileage > 0 : 
                    jmf_user_mileage_edit(id=username,val=mileage,reason_code="01005001")
                if deposit > 0 : 
                    jmf_user_deposit_edit(id=username,val=deposit,reason_code="01006003")

                try:
                    new_order = Order.objects.create(
                        identifier=order.create_order_identifier(),
                        user_id=username,
                        recipient_name=request.POST.get('recipient_name'),
                        recipient_phone=request.POST.get("recipient_phone"),
                        shipping_name=request.POST.get("shipping_name"),
                        post_number=request.POST.get("post_number"),
                        address=request.POST.get("address"),
                        address_detail=request.POST.get("detail_address"),
                        shipping_fee=shipping_fee,
                        price=request.POST.get("price"),
                        amount=request.POST.get("amount"),
                        mileage=request.POST.get("mileage"),
                        deposit=request.POST.get("deposit"),
                        option=request.POST.get("option"),
                        option_price=request.POST.get("option_price"),
                        final_price=request.POST.get("final_price"),
                        payment_type= request.POST.get("payment_type"),
                        is_paid=True,
                        status='0',
                        is_dawn=True if request.POST.get("is_dawn") == "true" else False,
                        product = Product.objects.get(identifier=request.POST.get("product_id")),
                        request=request.POST.get("request"),
                        entrance_password=request.POST.get("entrance_password"),
                        card=request.POST.get("card"),
                        )

                    payment_log = PaymentLog.objects.create(
                        receipt_id=card_data["receipt_id"],
                        price=card_data["price"],
                        card_no=card_data["card_no"],
                        card_code=card_data["card_code"],
                        card_name=card_data["card_name"],
                        item_name=card_data["item_name"],
                        pg_order_id=card_data["order_id"],
                        url=card_data["url"],
                        payment_name=card_data["payment_name"],
                        pg_name=card_data["pg_name"],
                        pg=card_data["pg"],
                        method=card_data["method"],
                        method_name=card_data["method_name"],
                        requested_at=card_data["requested_at"],
                        purchased_at=card_data["purchased_at"],
                        order=new_order,
                        user_id=username
                        )

                    views.send_order_email(new_order)

                    Log.objects.create(
                        url = "/product",
                        method = "POST",
                        request_code = request.POST,
                        response_code = "200",
                        message = new_order,
                        user_id = username
                    )

                    return JsonResponse({"purchased_time":card_data['purchased_at'], "token":context['token']}, status=200)
                except Exception as e:

                    #인증키 발급
                    headers = {"Content-Type": "application/json"}
                    data = '{"application_id": "5ffd22185b294800202a17fc", "private_key": "XNUYmHvVSUhY6nxtbqoLsOQL11ZuLm9cKOEXJZCR1Xc="}'
                    response = requests.post("https://api.bootpay.co.kr/request/token", headers=headers, data=data)
                    response = json.loads(response.text)

                    #구독시 주문 취소가 안되는 상황 확인하기

                    #취소 요청
                    receipt_id=request.POST.get("receipt_id")
                    headers = {"Authorization": response['data']['token']}
                    body = {"receipt_id": card_data['receipt_id'], "price": card_data['price'], "name": username, "reason": "주문 실패"}
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
                            item_name = Product.objects.get(identifier=request.POST.get("product_id")).name,
                            payment_name = "결제 취소",
                            pg_order_id = response_data['tid'],
                            purchased_at = response_data['revoked_at'],
                            user_id=username
                            )

                        Log.objects.create(
                            url = "/product",
                            method = "POST",
                            request_code = request.POST,
                            response_code = "501",
                            message = "주문 중 오류가 발생하여 결제가 취소되었습니다.",
                            user_id = username
                        )
                        return JsonResponse({"message":"주문 중 오류가 발생하여 결제가 취소되었습니다.", "token":context['token']},status=500)

                    else:

                        Log.objects.create(
                            url = "/product",
                            method = "POST",
                            request_code = request.POST,
                            response_code = "501",
                            message = "처리중 오류가 발생했습니다.",
                            user_id = username
                        )

                        return JsonResponse({"message":"처리중 오류가 발생했습니다.", "token":context['token']},status=500)
                    
                    Log.objects.create(
                        url = "/product",
                        method = "POST",
                        request_code = request.POST,
                        response_code = "501",
                        message = "처리중 오류가 발생했습니다.",
                        user_id = username
                    )
                    return JsonResponse({"data":"fail", "token":context['token']}, status=400)
            
        return JsonResponse({"data":"fail", "token":context['token']}, status=400)


