from shopmandb.models import *
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.parsers import FormParser
from rest_framework_api_key.permissions import HasAPIKey
from drf_yasg.utils import swagger_auto_schema
from .payment import get_payload_from_token, get_uat_from_refresh_token, get_username_from_uat
from django.http import JsonResponse
from rest_framework import serializers
from shopmandb.views import order
from django.core.paginator import Paginator
import datetime
import json

class SubscriptionInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = (
            "id",
            "shipping_range",
            "weekday",
            "recipient_name",
            "recipient_phone",
            "shipping_name",
            "post_number",
            "address",
            "address_detail",
            "entrance_password",
            "request"
        )


class SubscriptionSerializer(serializers.ModelSerializer):
    box = serializers.SerializerMethodField()
    card = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = (
            "id",
            "shipping_range",
            "weekday",
            "user_id",
            "box",
            "card",
            "recipient_name",
            "recipient_phone",
            "shipping_name",
            "post_number",
            "address",
            "address_detail",
            "entrance_password",
            "request"
        )

    def get_box(self, obj):
        return obj.box.name
    def get_card(self, obj):
        return json.loads(obj.card)


class PlanPostAPISerializer(serializers.Serializer):
    subscription_id = serializers.CharField(max_length=50, required=False)
    box_id = serializers.CharField(max_length=50, required=False)

class SubscriptionPostAPISerializer(serializers.Serializer):
    id = serializers.CharField(max_length=50)
    userbox_id = serializers.CharField(max_length=50)


class SubscriptionInfoGetAPISerializer(serializers.Serializer):
    subscription_id = serializers.CharField(max_length=50)


class SubscriptionInfoPatchAPISerializer(serializers.Serializer):
    id = serializers.CharField(max_length=50)
    shipping_range = serializers.CharField(max_length=50, required=False)
    weekday = serializers.CharField(max_length=50, required=False)
    recipient_name = serializers.CharField(max_length=50, required=False)
    recipient_phone = serializers.CharField(max_length=50, required=False)
    shipping_name = serializers.CharField(max_length=50, required=False)
    post_number = serializers.CharField(max_length=50, required=False)
    address = serializers.CharField(max_length=50, required=False)
    address_detail = serializers.CharField(max_length=50, required=False)
    entrance_password = serializers.CharField(max_length=50, required=False)
    expected_day = serializers.CharField(max_length=50, required=False)
    requset = serializers.CharField(max_length=50, required=False)


# class SubscriptionGetWmsAPISerializer(serializers.Serializer):
#     if_id = serializers.CharField(max_length=50, required=False)

#     def get_data_or_errors(self):
#         if self.is_valid():
#             return True, self.data
#         else:
#             return False, self.errors


class SubscriptionWmsInfoSerializer(serializers.ModelSerializer):
    box = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    shipping_range = serializers.SerializerMethodField()
    weekday = serializers.SerializerMethodField()
    wakeYn = serializers.SerializerMethodField()
    class Meta:
        model = Subscription
        fields = (
            "identifier",
            "user_id",
            "recipient_name",
            "box",
            "shipping_range",
            "weekday",
            "created_at",
            "is_active",
            "wakeYn"
        )
        extra_kwargs = {'is_active': {'write_only': True}}
    def get_wakeYn(self, obj):
        return obj.is_active
    def get_box(self, obj):
        return str(obj.box.name) + " - " + str(obj.box.price)
    def get_created_at(self, obj):
        return str(obj.created_at.date())
    def get_shipping_range(self, obj):
        return obj.get_shipping_range_display()
    def get_weekday(self, obj):
        return obj.get_weekday_display()

# def eidt_expected_day(expected_day, old_range, old_day, new_range, new_day):
#     if new_day == old_day:
#         if new_range == old_range:
#             return expected_day
#     return expected_day + datetime.timedelta(days=new_day - old_day + ((new_range - old_range) * 7), )

def get_user_id(request):
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
            return JsonResponse({"status":"expire", "msg":"token, refresh_token expire"}, status=401)

    user_id = get_username_from_uat(request)
    return user_id, context

# def make_order(real_result):
#     box = Box.objects.get(identifier=real_result["box_id"])

#     final_price = box.price - int(real_result["mileage"]) - int(real_result["deposit"])
#     userbox_id = real_result["user_box_id"]
#     userbox = UserBox.objects.get(identifier=userbox_id)
#     value = userbox.value

#     amount = 1

#     sub = Subscription.objects.create(
#         identifier=create_sub_identifier(),
#         shipping_range=real_result["range"],
#         weekday=real_result["weekday"],
#         expected_day= real_result['estimate_date'],
#         user_id=real_result['user_id'],
#         box= box,
#         card = real_result['card'],
#         survey_id = real_result['survey_ids'],
# 		recipient_name=real_result["recipient_name"],
#         recipient_phone=real_result["recipient_phone"],
#         shipping_name=real_result["shipping_name"],
#         post_number=real_result["post_number"],
#         address=real_result["address"],
#         address_detail=real_result["detail_address"],
# 		entrance_password=real_result["entrance_password"],
# 		request=real_result["request"]
#     )

#     order = Order.objects.create(
#         identifier=create_order_identifier(),
#         user_id=real_result['user_id'],
#         recipient_name=real_result["recipient_name"],
#         recipient_phone=real_result["recipient_phone"],
#         shipping_name=real_result["shipping_name"],
#         post_number=real_result["post_number"],
#         address=real_result["address"],
#         address_detail=real_result["detail_address"],
#         shipping_fee=3000,
#         price=box.price,
#         amount=amount,
#         mileage=real_result["mileage"],
#         deposit=real_result["deposit"],
#         payment_type= real_result["payment_type"],
#         final_price=final_price,
#         is_paid=True,
#         status="0",
#         card=str(real_result["card"]),
#         is_dawn=real_result["is_dawn"],
#         request=real_result["request"],
#         estimate_date=real_result["estimate_date"],
#         entrance_password=real_result["entrance_password"],
#         mileage_status="2",
#         sub=sub
#     )

#     userbox.subscription = sub
#     userbox.order = order
#     userbox.is_seleted = True
#     userbox.save()

#     target_id = userbox.target
#     order_userbox = UserBox.objects.filter(target = target_id)
#     order_userbox.update(subscription=sub)

#     return True

# ㅅㅏ용자의 구독 리스트
# 구독한 박스, 구독 주기
class SubscriptionListView(APIView):
    permission_classes = [permissions.AllowAny,]
    def get(self,request, *args, **kwargs):
        user_id, context = get_user_id(request)
        username = user_id[0]['username']
        sub_list = []
        
        try:
            subs = Subscription.objects.filter(user_id=username, is_active="0").order_by('-id')
            for sub in subs:
                user_box = UserBox.objects.filter(subscription=sub, is_selected=True).last()
                new = user_box.created_at
                now = datetime.datetime.now()
                day = now - new
                if day.days >= 1:
                    new = False
                else:
                    new = True
                image = f"{request.scheme}://{request.get_host()}/media/{str(sub.box.image)}"
                user_sub = {
                    "id" : sub.id,
                    "box_price" : sub.box.price,
                    "box_name" : sub.box.name,
                    "shipping_range" : sub.shipping_range,
                    "weekday" : sub.weekday,
                    "image" : image,
                    "is_new" : new,
                }
                sub_list.append(user_sub)

                Log.objects.create(
                    url = "/profile/sub/",
                    method = "GET",
                    request_code = request.GET,
                    response_code = "200",
                    message = sub_list,
                    user_id = username
                )
            return JsonResponse({"data" : sub_list, "token":context['token']}, status=200)
        except Exception as e:
            print("except", e)
            Log.objects.create(
                    url = "/profile/sub/",
                    method = "GET",
                    request_code = request.GET,
                    response_code = "500",
                    message = e,
                    user_id = username
                )
            return JsonResponse({"data" : sub_list, "message":str(e), "token":context['token']}, status=500)


class SubscriptionDetailView(APIView):
    permission_classes = [permissions.AllowAny,]
    def get(self, request, pk, **kwargs):
        user_id, context = get_user_id(request)
        try:
            sub = Subscription.objects.get(pk=pk)
            user_boxes = UserBox.objects.filter(subscription=sub, is_selected=True).order_by('-id')
            survey_names = json.loads(user_boxes.last().survey_names)
            username = []
            for name in survey_names:
                username.append(name)
            image = f"{request.scheme}://{request.get_host()}/media/{str(sub.box.image)}"
            sub_data = {
                "username" : username,
                "price" : sub.box.price,
                "image" : image,
                "next" : sub.expected_day
            }
            box_data = []
            userbox_data = []

            # user_boxes = 구독에 들어있는 주문에 대한 박스
            for user_box in user_boxes:
                fruits = []
                for value in json.loads(user_box.value):
                    data = {
                        "pk" : user_box.pk,
                        "name" : value['name'],
                        "if_id" : value['if_id'],
                        "image" : value['image'],
                        "trait_metabolites" : [] if value['detail'] is None else value['detail']['trait_metabolites'],
                        "nutrition": value['nutrition'],
                        "storage_method" : value['storage_method'],
                        "selection_method" : value['selection_method'],
                    }
                    fruits.append(data)
                userbox_data.append(fruits)
                # if user_box.order.status == "0":
                #     user_box_list = UserBox.objects.filter(target=user_box.target, is_selected=False)
                #     for userbox in user_box_list:
                #         fruits = []
                #         for v_data in json.loads(userbox.value):
                #             data = {
                #                 "pk" : userbox.pk,
                #                 "name" : v_data['name'],
                #                 "if_id" : v_data['if_id'],
                #                 "image" : v_data['image'],
                #                 "trait_metabolites" : v_data['detail']['trait_metabolites'],
                #                 "nutrition": v_data['nutrition'],
                #                 "storage_method" : v_data['storage_method'],
                #                 "selection_method" : v_data['selection_method'],
                #             }
                #             fruits.append(data)
                #         userbox_data.append(fruits)
                box = {
                    "status" : user_box.order.status if user_box.order else "1",
                    "date" : user_box.subscription.expected_day - datetime.timedelta(days=7),
                    "weekday" : user_box.subscription.weekday,
                    "is_dawn" : user_box.order.is_dawn if user_box.order else False,
                    "order_id" : user_box.order.id if user_box.order else "주문전",
                    "userbox" : userbox_data,
                    "recipient_name": user_box.subscription.recipient_name,
                    "recipient_phone": user_box.subscription.recipient_phone,
                    "shipping_name": user_box.subscription.shipping_name,
                    "post_number": user_box.subscription.post_number,
                    "address": user_box.subscription.address,
                    "address_detail": user_box.subscription.address_detail,
                    "entrance_password": user_box.subscription.entrance_password,
                }
                box["status"] = "0" if box["status"]=="20" else box["status"]
                box_data.append(box)
            
            Log.objects.create(
                url = "/profile/sub/"+str(pk),
                method = "GET",
                request_code = request.GET,
                response_code = "200",
                message = {"data" : sub_data, "box_data" :box_data},
                user_id = get_username_from_uat(request)[0]['username']
            )

            return JsonResponse({"data" : sub_data, "box_data" :box_data, "token":context['token']}, status=200)
        except Exception as e:
            print(e)
            Log.objects.create(
                url = "/profile/sub/"+str(pk),
                method = "GET",
                request_code = request.GET,
                response_code = "500",
                message = e,
                user_id = get_username_from_uat(request)[0]['username']
            )
            return JsonResponse({"data" : "no data", "token":context['token'], "msg" : str(e)}, status=500)

    # 배송지 수정(order_id(pk) 필요) / 유저박스 변경(order_id(pk), userbox_id 필요)
    @swagger_auto_schema(request_body=SubscriptionPostAPISerializer(),)
    def post(self, request, pk):
        user_id, context = get_user_id(request)
        order_id = request.POST.get('id', '')
        userbox_id = request.POST.get('userbox_id', '')
        
        # 조합박스 변경
        try:
            order = Order.objects.get(id=order_id)
            prev_userbox = order.userbox_order.last()
            prev_userbox.is_selected = False
            prev_userbox.save()
            new_userbox = UserBox.objects.get(id=userbox_id) # 새로운 userbox
            new_userbox.is_selected = True
            new_userbox.save()

            Log.objects.create(
                url = "/profile/sub/"+str(pk),
                method = "POST",
                request_code = request.POST,
                response_code = "200",
                message = new_userbox,
                user_id = user_id
            )
            return JsonResponse({"data" : "success", "token":context['token']}, status=200)
        except Exception as e:
            print(e)
            Log.objects.create(
                url = "/profile/sub/"+str(pk),
                method = "POST",
                request_code = request.POST,
                response_code = "500",
                message = e,
                user_id = "unknown"
            )
            return JsonResponse({"data" : "fail", "token":context['token']}, status=500)    


    def delete(self, request, pk):
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
                return JsonResponse({"status":"expire", "msg":"token, refresh_token expire"}, status=401)

        user_id = get_username_from_uat(request)
        username = get_username_from_uat(request)[0]['username']

        try:
            sub = Subscription.objects.get(pk=pk)
            sub.is_active = "2"
            sub.save()

            Log.objects.create(
                url = "/profile/sub/"+str(pk),
                method = "DELETE",
                request_code = "",
                response_code = "200",
                message = sub,
                user_id = username
            )
            return JsonResponse({"data":"success", "token":context['token']}, status=200)
        except Exception as e:
            print(e)
            Log.objects.create(
                url = "/profile/sub/"+str(pk),
                method = "DELETE",
                request_code = "",
                response_code = "500",
                message = e,
                user_id = username
            )
            return JsonResponse({"data" : "fail", "token":context['token']}, status=200)


class PlanView(APIView):
    permission_classes = [permissions.AllowAny,]
    @swagger_auto_schema(request_body=PlanPostAPISerializer(),)
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
                return JsonResponse({"status":"expire", "msg":"token, refresh_token expire"}, status=401)
                

        subscription_id = request.POST.get('subscription_id')
        box_id = request.POST.get('box_id')

        user_id = get_username_from_uat(request)
        username = user_id[0]['username']
        sub_list = []

        try:
            sub = Subscription.objects.get(id=subscription_id)
            sub.box = Box.objects.get(identifier=box_id)
            sub.save()
            subs = Subscription.objects.filter(user_id=username, is_active="0")

            for sub in subs:
                user_box = UserBox.objects.filter(subscription=sub, is_selected=True).last()
                new = user_box.created_at
                now = datetime.datetime.now()
                day = now - new
                if day.days >= 1:
                    new = False
                else:
                    new = True
                image = f"{request.scheme}://{request.get_host()}/media/{str(sub.box.image)}"
                user_sub = {
                    "id" : sub.id,
                    "box_price" : sub.box.price,
                    "shipping_range" : sub.shipping_range,
                    "weekday" : sub.weekday,
                    "image" : image,
                    "is_new" : new,
                }
                sub_list.append(user_sub)
                
            return JsonResponse({"data":sub_list, "token":context['token']}, status=200)
        except Exception as e:
            print(e)
            Log.objects.create(
                url = "/plan",
                method = "POST",
                request_code = request.POST,
                response_code = "500",
                message = e,
                user_id = "unknown"
            )
            return JsonResponse({"data" : "fail", "token":context['token']}, status=200)


class SubscriptionInfoView(APIView):
    permission_classes = [permissions.AllowAny,]
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
                return JsonResponse({"status":"expire", "msg":"token, refresh_token expire"}, status=401)
                
        username = get_username_from_uat(request)[0]['username']

        try:
            subscription_id = request.GET.get('subscription_id')
            subscription = Subscription.objects.get(id=subscription_id)
            sub_data = SubscriptionSerializer(subscription).data
            sub_data["next"] = subscription.expected_day
            sub_data['phone'] = subscription.recipient_phone

            Log.objects.create(
                url = "/subscription-info",
                method = "GET",
                request_code = request.GET,
                response_code = "200",
                message = sub_data,
                user_id = username
            )

            return JsonResponse({"data":sub_data, "token":context['token']}, status=200)
        except Exception as e:
            print(e)
            return JsonResponse({"data" : "fail", "token":context['token']}, status=200)

    

    def patch(self, request, *args, **kwargs):
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
                return JsonResponse({"status":"expire", "msg":"token, refresh_token expire"}, status=401)

        username = get_username_from_uat(request)[0]['username']
        request_json = request.POST
        print(request_json)
        tmp_dict = {}
        for key in request_json.keys():
            if key != "receipt_id" and key != "billing_key" and key != "card_no" and key != "card_name" and key != "requset":
                if request_json[key] != 'null':
                    tmp_dict[key] = request_json[key]
            if key == 'requset':
                target = Subscription.objects.get(id=request.POST.get('id'))
                target.request = request_json['requset']
                target.save()
        subscriptions = Subscription.objects.filter(id=request.POST.get('id'))

        # old_range = subscriptions.last().shipping_range
        # old_weekday = subscriptions.last().weekday
        subscriptions.update(**tmp_dict)

        subscription = subscriptions.last()
        if subscription.card is not None:
            card = json.loads(subscription.card)

        # 구독 날짜 변경 시 발생되는 이슈 때문에 일단 클라이언트에서 보내주는 날짜 사용
        # if request_json.get('weekday') and request_json.get('weekday') != 'null': 
        #     if request_json.get('shipping_range') and request_json.get('shipping_range') != 'null': 
        #         new_day = eidt_expected_day(subscription.expected_day, int(old_range), int(old_weekday), int(request_json.get('shipping_range')), int(request_json.get('weekday')))
                
        #         subscription.expected_day = new_day

        if request_json.get('receipt_id') and request_json.get('receipt_id') != 'null': 
            card['receipt_id'] = request_json['receipt_id']
            tmp_dict['receipt_id'] = request_json['receipt_id']
        if request_json.get('billing_key') and request_json.get('billing_key') != 'null':
            card['billing_key'] = request_json['billing_key']
            tmp_dict['billing_key'] = request_json['billing_key']
        if request_json.get('card_no') and request_json.get('card_no') != 'null':
            card['card_no'] = request_json['card_no']
            tmp_dict['card_no'] = request_json['card_no']
        if request_json.get('card_name') and request_json.get('card_name') != 'null':
            card['card_name'] = request_json['card_name']
            tmp_dict['card_name'] = request_json['card_name']

        subscription.card = json.dumps(card)
        subscription.save()

        try:
            # subscription_id = request.GET.get('id')
            # subscription = Subscription.objects.get(id=request_json['id'])
            card = json.loads(subscription.card)

            sub_data = SubscriptionInfoSerializer(subscription).data
            sub_data['receipt_id'] = card['receipt_id']
            sub_data['billing_key'] = card['billing_key']
            sub_data['card_no'] = card['card_no']
            sub_data['card_name'] = card['card_name']
            sub_data['next'] = subscription.expected_day
            sub_data['phone'] = subscription.recipient_phone

            Log.objects.create(
                url = "/subscription-info",
                method = "PATCH",
                request_code = request.POST,
                response_code = "200",
                message = sub_data,
                user_id = username
            )

            return JsonResponse({"data":sub_data, "token":context['token']}, status=200)
        except Exception as e:
            print(e)
            return JsonResponse({"data" : "fail", "token":context['token']}, status=200)



class SubscriptionWmsAPIView(APIView):
    permission_classes = (HasAPIKey, )
    @swagger_auto_schema()
    def get(self, request, *args, **kwargs):
        # refresh_token = request.META.get('HTTP_REFRESHTOKEN', b'')
        # token = request.META.get('HTTP_TOKEN', b'')
		# # data= request.POST.get("data")
        # context = {}
        # context['token'] = token

        # #token을 디코딩 -> exp 확인 날자가 지나면 tokken을 재발급(refresh 토큰을 이용해서)
        # payload = get_payload_from_token(request)
        # exp = datetime.datetime.fromtimestamp(int(payload['exp']))

        # is_refresh = False
        # if datetime.datetime.now() > exp:
        #     tokens, status = get_uat_from_refresh_token(refresh_token)
        #     if status == 200:
        #         context['refresh_token'] = tokens['refresh_token']
        #         context['token'] = tokens['access_token']
        #         is_refresh = True
        #     else:
        #         return JsonResponse({"status":"expire", "msg":"token, refresh_token expire"}, status=401)
                
        # username = get_username_from_uat(request)[0]['username']

        try:
            # sub_data = SubscriptionWmsInfoSerializer(subscription, many=True).data

            num_pages = request.GET.get('num_pages', 20)   # 한 페이지에 데이터 몇개 보여질지
            page = request.GET.get('page', 1)  # 현재 페이지
            order_by = request.GET.get('order_by', 'id')
            decending = request.GET.get('decending', True)
            is_active = request.GET.get('is_active', "0")

            if decending:
                order_by = f"-{order_by}"

            subscriptions = Subscription.objects.filter(is_active=is_active).order_by(order_by)
            total_subscriptions = Subscription.objects.all()

            paginator = Paginator(subscriptions, num_pages)
            data = []
            #for order in orders:
            for subscription in paginator.get_page(page):
                # 구독 여부...
                sub_data = SubscriptionWmsInfoSerializer(subscription).data
                data.append(sub_data)

            Log.objects.create(
                url = "/subscription-wms",
                method = "GET",
                request_code = request.GET,
                response_code = "200",
                message = json.dumps(sub_data),
                user_id = "wms"
            )

            return JsonResponse({"data":data, "search_subscription_count":len(subscriptions), "total_subscription_count":len(total_subscriptions)}, status=200)
        except Exception as e:
            print(e)
            Log.objects.create(
                url = "/subscription-wms",
                method = "GET",
                request_code = request.GET,
                response_code = "500",
                message = e,
                user_id = "wms"
            )
            return JsonResponse({"data" : "fail"}, status=200)
