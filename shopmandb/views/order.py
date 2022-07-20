from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.parsers import FormParser
from rest_framework_api_key.permissions import HasAPIKey
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from django.http import JsonResponse
from django.conf import settings
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from shopmandb.models import *
from .payment import *
from dateutil.relativedelta import relativedelta
import requests
import json
import time
import datetime

def create_order_identifier():
    now = time.localtime()
    if Order.objects.all().count() != 0:
        new_id=Order.objects.last().id+1
    else:
        new_id=1
    first_id = (
        str(now.tm_year)[-2:]
        + str(now.tm_mon).zfill(2)
        + str(now.tm_mday).zfill(2)
        + "O-"
    )
    identifier = first_id + str(new_id).zfill(4)
    return identifier

def create_sub_identifier():
    if Subscription.objects.all().count() != 0:
        new_id = Subscription.objects.last().id+1
    else:
        new_id = 1
    identifier = "Sub" + str(new_id).zfill(4)
    return identifier

# status = request.POST.get('status', '0')
# num_pages = request.POST.get('num_pages', 20)   # 한 페이지에 데이터 몇개 보여질지
# page = request.POST.get('page', 1)  # 현재 페이지
# order_by = request.POST.get('order_by', 'id')
# decending = request.POST.get('decending', True)

class ShippingGetAPISerializer(serializers.Serializer):
    order_id = serializers.CharField(max_length=50)


class OrderWmsGetAPISerializer(serializers.Serializer):
    status = serializers.CharField(max_length=10)
    num_pages = serializers.IntegerField(required=False)
    page = serializers.IntegerField(required=False)
    order_by = serializers.CharField(required=False)
    decending = serializers.CharField(required=False)


class OrderGetAPISerializer(serializers.Serializer):
    status = serializers.CharField(max_length=1)


class OrderDeleteAPISerializer(serializers.Serializer):
    order_id = serializers.CharField(max_length=50)
    reason = serializers.CharField(max_length=100, required=False)
    status = serializers.CharField(max_length=50)
    receipt_id = serializers.CharField(max_length=50)


class OrderView(APIView):
    permission_classes = [permissions.AllowAny,]

    #주문 조회
    @swagger_auto_schema(query_serializer=OrderGetAPISerializer(),)
    def get(self, request, *args, **kwargs):
        refresh_token = request.META.get('HTTP_REFRESHTOKEN', b'')
        token = request.META.get('HTTP_TOKEN', b'')
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
					url = "/order",
					method = "GET",
					request_code = request.GET,
					response_code = "401",
					message = "token, refresh_token expire",
					user_id = "unknown"
				)
                return JsonResponse({"status":"expire", "msg":"token, refresh_token expire"}, status=401)

        username = get_username_from_uat(request)[0]['username']

        request_status = request.GET.get('status')
        order_list = None
        if request_status is not None:
            request_status = request_status.split(',')
            order_list = Order.objects.filter(user_id=username, status__in=request_status).order_by("-id")
        else:
            order_list = Order.objects.filter(user_id=username).order_by("-id")

        result = []
        for each in order_list:
            name = ""
            shipping_range = ""
            weekday = ""
            image = ""
            email = ""
            product_id = ""
            recipient_name = each.recipient_name
            recipient_phone = each.recipient_phone
            shipping_name = each.shipping_name
            post_number = each.post_number
            address = each.address
            address_detail = each.address_detail
            shipping_fee = each.shipping_fee
            price = each.price
            amount = each.amount
            payment_type = each.payment_type
            final_price = each.final_price
            is_paid = each.is_paid
            status = "0" if each.status=="20" else each.status
            is_dawn = each.is_dawn
            dtime = each.dtime
            request_massage = each.request
            shipping_place = each.shipping_place
            invoice_number = each.invoice_number
            invoice_company = each.invoice_company
            estimate_date = each.estimate_date
            created_at = each.created_at
            complete_date = each.complete_date
            entrance_password = each.entrance_password

            if each.sub is None:
                name = each.product.name
                product_id = each.product.identifier
                image = str(each.product.image_path)
            else:
                name = each.sub.box.name+" - 체험분" if each.is_test else each.sub.box.name
                shipping_range = each.sub.shipping_range
                weekday = each.sub.weekday
                image = f"{request.scheme}://{request.get_host()}/media/{str(each.sub.box.image)}"

            data = {
                "order_id":each.id,
                "name":name,
                "product_id":product_id,
                "shipping_range":shipping_range,
                "weekday":weekday,
                "image":image,
                "email":email,
                "recipient_name":recipient_name,
                "recipient_phone":recipient_phone,
                "shipping_name":shipping_name,
                "post_number":post_number,
                "address":address,
                "address_detail":address_detail,
                "shipping_fee":shipping_fee,
                "price":price,
                "amount":amount,
                "payment_type":payment_type,
                "final_price":final_price,
                "is_paid":is_paid,
                "status":status,
                "is_dawn":is_dawn,
                "dtime":dtime,
                "request":request_massage,
                "shipping_place":shipping_place,
                "invoice_number":invoice_number,
                "invoice_company":invoice_company,
                "estimate_date": "" if estimate_date is None else estimate_date.strftime('%Y-%m-%d'),
                "complete_date": "" if complete_date is None else complete_date.strftime('%Y-%m-%d'),
                "entrance_password":entrance_password,
                "created_at":created_at
            }
            result.append(data)


        return JsonResponse({"data":result})

    @swagger_auto_schema(query_serializer=OrderDeleteAPISerializer(),)
    def delete(self, request, *args, **kwargs):
        refresh_token = request.META.get('HTTP_REFRESHTOKEN', b'')
        token = request.META.get('HTTP_TOKEN', b'')
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
					url = "/order",
					method = "DELETE",
					request_code = request.GET,
					response_code = "401",
					message = "token, refresh_token expire",
					user_id = "unknown"
				)
                return JsonResponse({"status":"expire", "msg":"token, refresh_token expire"}, status=401)

        username = get_username_from_uat(request)[0]['username']

        order_id = request.GET.get('order_id')
        reason = request.GET.get('reason')
        status = request.GET.get('status')

        order = Order.objects.get(id=order_id)

        if order.final_price == 0:  #0원 결제
            order.status = status
            order.cancel_reason = reason
            if order.mileage:
                order.mileage_status = '3'
            else:
                order.mileage_status = '2'
            order.save()
            return JsonResponse({"message":"처리되었습니다.", "token":context['token']},status=200)
        else:
            card_info = json.loads(order.card)

            #인증키 발급
            headers = {"Content-Type": "application/json"}
            data = '{"application_id": "5ffd22185b294800202a17fc", "private_key": "XNUYmHvVSUhY6nxtbqoLsOQL11ZuLm9cKOEXJZCR1Xc="}'
            response = requests.post("https://api.bootpay.co.kr/request/token", headers=headers, data=data)
            response = json.loads(response.text)

            #구독시 주문 취소가 안되는 상황 확인하기

            #취소 요청
            receipt_id=request.POST.get("receipt_id")
            headers = {"Authorization": response['data']['token']}
            body = {"receipt_id": card_info['receipt_id'], "price": card_info['price'], "name": order.recipient_name, "reason": reason}
            response = requests.request("POST", "https://api.bootpay.co.kr/cancel", headers=headers, data=body)
            response_data = json.loads(response.text)
            if response.status_code == 500:
                return JsonResponse({"message":response_data['message'], "reason":response_data, "token":context['token']},status=500)
            else:
                response_data = response_data["data"]

            if response.status_code == 200:
                order.status = status
                order.cancel_reason = reason
                if order.mileage:
                    order.mileage_status = '3'
                else:
                    order.mileage_status = '2'
                order.save()


                payment_log = PaymentLog.objects.create(
                    receipt_id=response_data["receipt_id"],
                    price=response_data['request_cancel_price'],
                    item_name = order.product.name if order.product else order.sub.box.name,
                    payment_name = "결제 취소",
                    pg_order_id = response_data['tid'],
                    purchased_at = response_data['revoked_at'],
                    order = order,
                    user_id=username
                    )
                return JsonResponse({"message":"처리되었습니다.", "data":response_data, "token":context['token']},status=200)
            else:
                return JsonResponse({"message":"처리중 오류가 발생했습니다.", "token":context['token']},status=500)

        return JsonResponse({"message":"처리중 오류가 발생했습니다.", "token":context['token']},status=501)


class OrderUpdateView(APIView):
    permission_classes = [permissions.AllowAny,]
    def post(self, request, id):
        refresh_token = request.META.get('HTTP_REFRESHTOKEN', b'')
        token = request.META.get('HTTP_TOKEN', b'')
		
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
					url = "/order",
					method = "POST",
					request_code = request.POST,
					response_code = "401",
					message = "token, refresh_token expire",
					user_id = "unknown"
				)
                return JsonResponse({"status":"expire", "msg":"token, refresh_token expire"}, status=401)

        try:
            request_data = request.POST

            tmp_dict = {}
            for key in request_data.keys():
                if request_data[key] != 'null':
                    tmp_dict[key] = request_data[key]
                        
            order = Order.objects.filter(id=id)
            order.update(**tmp_dict)
            order = order[0]
            data = {
                "id": order.id,
                "recipient_name": order.recipient_name,
                "recipient_phone": order.recipient_phone,
                "shipping_name": order.shipping_name,
                "post_number": order.post_number,
                "address": order.address,
                "address_detail": order.address_detail,
                "entrance_password": order.entrance_password,
                "request" : order.request,
            }
            return JsonResponse({"data" : data, "token":context['token']}, status=200)
        except Exception as e:
            print(e)
            return JsonResponse({"data" : "", "token":context['token']}, status=200)

class OrderWmsListView(APIView):
    permission_classes = [permissions.AllowAny,]
    
    def update_order(self, order):
        # 박스 구성
        userbox = order.userbox_order.last()
        userbox_content = []
        # userbox_content = ""
        if userbox is not None:
            values = json.loads(userbox.value)
            for value in values:
                box_dict = {}
                box_dict['itemCode'] = value['item_code'] if 'item_code' in value else 'temp'
                box_dict['itemName'] = value['name']
                box_dict['주문양'] = int(value['amount'])
                box_dict['수량'] = value['unit']
                userbox_content.append(box_dict)
                # userbox_content = userbox_content + f"{value['name']} {int(value['amount'])} {value['unit']}|"
            order_data = {
                "주문번호" : order.identifier,
                "주문상태" : order.status,
                "송장번호" : order.invoice_number if order.invoice_number else "",
                "송장업체" : order.invoice_company if order.invoice_company else "",
                "채널" : "궁합과일",
                "회원 아이디" : order.user_id,
                "상품명" : order.sub.box.name,
                "상품수량" : order.amount,
                "판매가" : order.sub.box.price,
                "총 결제 금액" : order.final_price,
                "총 품목 금액" : order.sub.box.price,
                "총 배송 금액" : order.shipping_fee,
                "사용된 총 예치금" : order.deposit,
                "사용된 총 마일리지" : order.mileage,
                "주문일자" : order.created_at.strftime("%Y-%m-%d"),
                "수취인 이름" : order.recipient_name,
                "수취인 핸드폰 번호" : order.recipient_phone,
                "수취인 우편번호(5자리)" : order.post_number,
                "수취인 주소" : order.address,
                "수취인 나머지 주소" : order.address_detail,
                "주문시 남기는 글" : order.request,
                "현관 비밀번호" : order.entrance_password,
                "구독 아이디" : order.sub.identifier if order.sub else order.sub.identifier,
                "유저박스 아이디" : userbox.identifier,
                "박스 구성" : userbox_content if userbox is not None else "",
                "구독 주기": order.sub.get_shipping_range_display(),
                "구독 요일" : order.sub.get_weekday_display(),
                "정기 배송 예정일" : order.estimate_date,
                "상품코드" : userbox.box.identifier,
                "새벽 배송 여부" : "예" if order.is_dawn else "아니오",
                "산지 배송 여부" : "아니오"
            }
            return order_data

    @swagger_auto_schema(query_serializer=OrderWmsGetAPISerializer(),)
    def get(self, request, *args, **kwargs):
        status = request.GET.get('status', '0')
        num_pages = request.GET.get('num_pages', 20)   # 한 페이지에 데이터 몇개 보여질지
        page = request.GET.get('page', 1)  # 현재 페이지
        order_by = request.GET.get('order_by', 'id')
        decending = request.GET.get('decending', True)
        identifier = request.GET.get('identifier')
        if decending:
            order_by = f"-{order_by}"

        if identifier:        
            orders = Order.objects.filter(identifier=identifier)
        else:
            orders = Order.objects.filter(status=status).order_by(order_by)


        paginator = Paginator(orders, num_pages)
        data = []
        #for order in orders:
        for order in paginator.get_page(page):
            # 구독 여부...
            if order.sub:
                # 구독 주문의 경우
                order_data = self.update_order(order)
            else:
                # 단품 주문의 경우
                order_data = {
                    "주문번호" : order.identifier,
                    "주문상태" : order.status,
                    "송장번호" : order.invoice_number if order.invoice_number else "",
                    "송장업체" : order.invoice_company if order.invoice_company else "",
                    "채널" : "궁합과일",
                    "회원 아이디" : order.user_id,
                    "상품명" : order.product.name if order.product else "",
                    "상품수량" : order.amount,
                    "판매가" : order.product.price if order.product else "",
                    "총 결제 금액" : order.final_price,
                    "총 품목 금액" : order.price,
                    "총 배송 금액" : order.shipping_fee,
                    "사용된 총 예치금" : order.deposit,
                    "사용된 총 마일리지" : order.mileage,
                    "주문일자" : order.created_at.strftime("%Y-%m-%d"),
                    "수취인 이름" : order.recipient_name,
                    "수취인 핸드폰 번호" : order.recipient_phone,
                    "수취인 우편번호(5자리)" : order.post_number,
                    "수취인 주소" : order.address,
                    "수취인 나머지 주소" : order.address_detail,
                    "주문시 남기는 글" : order.request,
                    "현관 비밀번호" : order.entrance_password,
                    "구독 아이디" : "",
                    "유저박스 아이디" : "",
                    "박스 구성" : "",
                    "구독 주기": "",
                    "구독 요일" : "",
                    "정기 배송 예정일" : "",
                    "상품코드" : order.product.identifier,
                    "새벽 배송 여부" : "예" if order.is_dawn else "아니오",
                    "산지 배송 여부" : "예" if order.product.is_direct else "아니오"
                }
            data.append(order_data)
        return JsonResponse({"data" : data, "total_order":len(orders)}, status=200)


# wms 와 관련된 API
class OrderWmsUpdateView(APIView):
    permission_classes = [permissions.AllowAny,]

    def post(self, request, identifier, **kwargs):
        order = get_object_or_404(Order, identifier=identifier)

        if request.POST.get('invoice_company'):
            invoice_company = request.POST.get('invoice_company')
            order.invoice_company = invoice_company
            order.save()
            
        if request.POST.get('invoice_number'):
            invoice_number = request.POST.get('invoice_number')
            order.invoice_number = invoice_number
            order.status = "2"
            
            order.save()
            return JsonResponse({f"{identifier}" : "update success"}, status=200)


        if request.POST.get('status'):
            status = request.POST.get('status')
            status_arr = ["0","1","2","3","4","5","6","7","8","20"]
            if status not in status_arr:
                return JsonResponse({f"{identifier}" : "유효하지 않은 상태값입니다."}, status=400)    
            if status == "8":
                order.dtime = datetime.datetime.now()
            order.status = status

            order.save()
            return JsonResponse({f"{identifier}" : "update success"}, status=200)
        
        if not request.POST.get('invoice_number') and request.POST.get('status'):
            return JsonResponse({f"{identifier}" : "params error"}, status=400)


class ShippingAPIView(APIView):
    permission_classes = [permissions.AllowAny,]
    @swagger_auto_schema(query_serializer=ShippingGetAPISerializer(),)
    def get(self, request, *args, **kwargs):
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
					url = "/shipping",
					method = "get",
					request_code = request.GET,
					response_code = "401",
					message = "token, refresh_token expire",
					user_id = "unknown"
				)
                return JsonResponse({"status":"expire", "msg":"token, refresh_token expire"}, status=401)

        user_id = get_username_from_uat(request)
        username = user_id[0]['username']

        if request.GET.get('order_id') == "주문전":
            return JsonResponse({"data" : "유효하지 않은 송장번호.", "token":context['token']}, status=200)

        order_id = request.GET.get('order_id')
        order = Order.objects.get(id=order_id)
        is_dawn = order.is_dawn
        invoice_number = order.invoice_number
        dawn_status = {"정상배송":0,  "배송시작":1, "대응배송":1, "미배송":1, "미회수":1, "정상회수":1, "오배송":1, "오회수":1, "배차완료":1, "미출고":2, "미입고":2, "접수완료":2, "주문취소":0}
        normal_status = {"delivered":0,"out_for_delivery":1,"in_transit":1,"at_pickup":2}

        result = {}

        if invoice_number is None:
            return JsonResponse({"data" : "유효하지 않은 송장번호.", "token":context['token']}, status=200)
        
        if '-' in invoice_number:    #새벽배송
            invoice_date_str = invoice_number.split('-')[0]
            invoice_date = datetime.datetime.strptime(invoice_date_str,"%Y%m%d")
            invoice_date = invoice_date.strftime("%Y-%m-%d")
            # data = {"orderDate":"2021-03-10","imageYn":"0","orderType":"2","customerOrderNum":"20210308-0001306"}
            header = {'apiaccesskey': 'o0g+Auaw8Zx+1b/DD1bWJRvRl+DYR3S3ssknK52M86tJYhypZIG9qWfS73XdHzyV+GQhJ/eZLP8Dg+1jIYbUzw==', 'Content-type': 'application/json'}
            data = {"orderDate":invoice_date,"imageYn":"0","orderType":"1","timfOrderNum":invoice_number}
            res = requests.request("POST", "https://tmsapi.teamfresh.co.kr/api/delivery/orderDeliveryInfo", headers=header,data=json.dumps(data))
            progresses = json.loads(res.text)

            if progresses['resultCode'] == '0002':
                return JsonResponse({"data" : {}, "message":progresses['resultMsg'], "token":context['token']}, status=502)

            result['now_status'] = dawn_status[progresses['result']['deliveryInfo']['tfsCategory']]
            
        else:    #일반배송
            #택배사에 정보 요청
            url = f'https://apis.tracker.delivery/carriers/kr.lotte/tracks/{invoice_number}'
            response = requests.request("GET",url)

            #택배 위치 조회
            progresses = json.loads(response.text)['progresses']

            #택배 상태
            state = progresses[0]['status']['id']
            result['now_status'] = normal_status[state]

            traker_arr = []
            for each in progresses:
                location = each['location']['name'].split('\t')[1].split('\n')[0]
                data = {"name":location,"time":each['time']}

                traker_arr.append(data)

            result['delivery_tracking'] = traker_arr

        return JsonResponse({"data" : result, "token":context['token']}, status=200)


class OrderIdentifierView(APIView):
    permission_classes = [permissions.AllowAny,]

    #주문 조회
    @swagger_auto_schema(query_serializer=OrderGetAPISerializer(),)
    def get(self, request, *args, **kwargs):
        refresh_token = request.META.get('HTTP_REFRESHTOKEN', b'')
        token = request.META.get('HTTP_TOKEN', b'')
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
					url = "/order/identifier",
					method = "GET",
					request_code = request.GET,
					response_code = "401",
					message = "token, refresh_token expire",
					user_id = "unknown"
				)
                return JsonResponse({"status":"expire", "msg":"token, refresh_token expire"}, status=401)

        new_identifier = create_order_identifier()
        return JsonResponse({"data": {"identifier": new_identifier}, "token":context['token']}, status=200)


# class OrderWmsView(APIView):
#     permission_classes = [permissions.AllowAny,]
#     @swagger_auto_schema(query_serializer=OrderWmsGetAPISerializer(),)
#     def get(self, request, *args, **kwargs):

#         refresh_token = request.META.get('HTTP_REFRESHTOKEN', b'')
#         token = request.META.get('HTTP_TOKEN', b'')
#         context = {}
#         context['token'] = token

#         #token을 디코딩 -> exp 확인 날자가 지나면 tokken을 재발급(refresh 토큰을 이용해서)

#         payload = get_payload_from_token(request)
#         exp = datetime.datetime.fromtimestamp(int(payload['exp']))

#         is_refresh = False
#         if datetime.datetime.now() > exp:
#             tokens, status = get_uat_from_refresh_token(refresh_token)
#             if status == 200:
#                 context['refresh_token'] = tokens['refresh_token']
#                 context['token'] = tokens['access_token']
#                 is_refresh = True
#             else:
#                 Log.objects.create(
# 					url = "/order",
# 					method = "GET",
# 					request_code = request.GET,
# 					response_code = "401",
# 					message = "token, refresh_token expire",
# 					user_id = "unknown"
# 				)
#                 return JsonResponse({"status":"expire", "msg":"token, refresh_token expire"}, status=401)

#         username = get_username_from_uat(request)[0]['username']

        
#         return JsonResponse({"data" : data}, status=200)


### 진맛과 정산을 위한 API

class FruitsOrderSerializer(serializers.ModelSerializer):
    product_id = serializers.SerializerMethodField()
    class Meta:
        model = Order
        fields = (
            "id",
            "identifier",
            "user_id",
            "orderer_phone",
            "status",
            "price",
            "amount",
            "product_id",
            "created_at",
        )
    def get_product_id(self, obj):
        return obj.product.id if obj.product else None


class FruitsProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "id",
            "identifier",
            "name",
            "price",
        )


class FruitsPaymentLogSerializer(serializers.ModelSerializer):
    order_id = serializers.SerializerMethodField()
    class Meta:
        model = PaymentLog
        fields = (
        "receipt_id",
        "item_name",
        "pg_order_id",
        "payment_name",
        "method",
        "method_name",
        "requested_at",
        "purchased_at",
        "price",
        "order_id",
        "user_id",
        )
    def get_order_id(self, obj):
        return obj.order.id if obj.order else None


class FruitsOrderListView(APIView):
    permission_classes = [permissions.AllowAny,]

    #주문 조회
    def get(self, request, *args, **kwargs):
        filter_type = request.GET.get("type")
        today = datetime.datetime.today()
        post_month = datetime.datetime(today.year, today.month, 1) - relativedelta(months=1)
        if filter_type == "daily":
            orders = Order.objects.exclude(product=None).filter(created_at__year=today.year, created_at__month=today.month, created_at__day=today.day)
        elif filter_type == "monthly":
            orders = Order.objects.exclude(product=None).filter(created_at__year=post_month.year, created_at__month=post_month.month)
        datas = FruitsOrderSerializer(orders, many=True).data
        return JsonResponse({"data": datas}, status=200)


class FruitsProductListView(APIView):
    permission_classes = [permissions.AllowAny,]

    #주문 조회
    def get(self, request, *args, **kwargs):
        products = Product.objects.all()
        datas = FruitsProductSerializer(products, many=True).data
        return JsonResponse({"data": datas}, status=200)


class FruitsPaymentLogListView(APIView):
    permission_classes = [permissions.AllowAny,]

    #주문 조회
    def get(self, request, *args, **kwargs):
        filter_type = request.GET.get("type")
        today = datetime.datetime.today()
        post_month = datetime.datetime(today.year, today.month, 1) - relativedelta(months=1)
        if filter_type == "daily":
            logs = PaymentLog.objects.exclude(receipt_id=None).filter(created_at__year=today.year, created_at__month=today.month, created_at__day=today.day)
        if filter_type == "monthly":
            logs = PaymentLog.objects.exclude(receipt_id=None).filter(created_at__year=post_month.year, created_at__month=post_month.month)
        datas = FruitsPaymentLogSerializer(logs, many=True).data
        return JsonResponse({"data": datas}, status=200)


class OrderViewForGeneticTest(APIView):
    permission_classes = (HasAPIKey,)

    def put(self, request, *args, **kwargs):
        username = request.POST.get('username')
        status = request.POST.get('status')

        order = Order.objects.filter(user_id=username).filter(product__identifier="P00000ZN").filter(final_price=0).exclude(status="8").last()
        if order == None:
            return JsonResponse({"message":"Order not found."}, status=403)

        order.status = status
        order.save()

        return JsonResponse({"message":"처리되었습니다.."},status=200)

    def delete(self, request, *args, **kwargs):

        username = request.GET.get('username')

        order = Order.objects.filter(user_id=username).filter(product__identifier="P00000ZN").filter(final_price=0).exclude(status="8").last()
        if order == None:
            return JsonResponse({"message":"Order not found."}, status=403)

        if order.final_price == 0:  #0원 결제
            order.status = "8"
            order.cancel_reason = "유전자 검사 취소"
            if order.mileage:
                order.mileage_status = '3'
            else:
                order.mileage_status = '2'
            order.save()
            return JsonResponse({"message":"처리되었습니다."},status=200)
        else:
            card_info = json.loads(order.card)

            #인증키 발급
            headers = {"Content-Type": "application/json"}
            data = '{"application_id": "5ffd22185b294800202a17fc", "private_key": "XNUYmHvVSUhY6nxtbqoLsOQL11ZuLm9cKOEXJZCR1Xc="}'
            response = requests.post("https://api.bootpay.co.kr/request/token", headers=headers, data=data)
            response = json.loads(response.text)

            #구독시 주문 취소가 안되는 상황 확인하기

            #취소 요청
            receipt_id=request.POST.get("receipt_id")
            headers = {"Authorization": response['data']['token']}
            body = {"receipt_id": card_info['receipt_id'], "price": card_info['price'], "name": order.recipient_name, "reason": reason}
            response = requests.request("POST", "https://api.bootpay.co.kr/cancel", headers=headers, data=body)
            response_data = json.loads(response.text)
            if response.status_code == 500:
                return JsonResponse({"message":response_data['message'], "reason":response_data, "token":context['token']},status=500)
            else:
                response_data = response_data["data"]

            if response.status_code == 200:
                order.status = "8"
                order.cancel_reason = "유전자 검사 취소"
                if order.mileage:
                    order.mileage_status = '3'
                else:
                    order.mileage_status = '2'
                order.save()


                payment_log = PaymentLog.objects.create(
                    receipt_id=response_data["receipt_id"],
                    price=response_data['request_cancel_price'],
                    item_name = order.product.name if order.product else order.sub.box.name,
                    payment_name = "결제 취소",
                    pg_order_id = response_data['tid'],
                    purchased_at = response_data['revoked_at'],
                    order = order,
                    user_id=username
                    )
                return JsonResponse({"message":"처리되었습니다.", "data":response_data},status=200)
            else:
                return JsonResponse({"message":"처리중 오류가 발생했습니다."},status=500)

        return JsonResponse({"message":"처리중 오류가 발생했습니다."},status=501)