from shopmandb.models import Shipping
from rest_framework.views import APIView
from rest_framework import permissions
from .payment import get_payload_from_token, get_uat_from_refresh_token, get_username_from_uat
from django.http import JsonResponse
from rest_framework import serializers
from shopmandb.models import *
import datetime
import pandas as pd
import json

class ShippingFeeAPIView(APIView):
    permission_classes = [permissions.AllowAny,]
    def get(self,request, *args, **kwargs):
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
                return JsonResponse({"status":"expire", "msg":"token, refresh_token expire"}, status=401)

        user_id = get_username_from_uat(request)
        try:
            post_number = request.GET.get('post_number')
            
			
            fee_object=Shipping.objects.filter(new_post=post_number).last()
            print(fee_object)
            if fee_object:
                fee = int(fee_object.airport_fee) + int(fee_object.ship_fee)
            else:
                fee = 0

            return JsonResponse({"data" : {'fee':fee}, "token":context['token']}, status=200)
        except Exception as e:
            print("except", e)
            return JsonResponse({"data" : fee, "token":context['token']}, status=200)

class StatisticsView(APIView):
    permission_classes = [permissions.AllowAny,]
    def get(self,request, *args, **kwargs):
        today = datetime.datetime.now().date()

        user_total = {}
        date_total = {}
        total = {}
        range_total = {}

        #날짜별 통계
        for i in range(1,29):
            before_days = (datetime.datetime.now() - datetime.timedelta(days=29-i)).date()
            date_total[str(before_days)] = 0

        before_28_days = before_days = (datetime.datetime.now() - datetime.timedelta(days=28)).date()
        order_list = Order.objects.filter(created_at__date__gte=before_28_days).exclude(created_at__date=today).exclude(status__in=['4','5','8'])
        values_list = order_list.values_list('price','created_at__date')
        for each in values_list:
            date_total[str(each[1])] += each[0]

        #사용자별 통계
        order_list = Order.objects.all().exclude(status__in=['4','5','8'])
        user_list = order_list.values_list('user_id','price')
        
        for each in user_list:
            if each[0] not in user_total:
                user_total[each[0]] = each[1]
            else:
                user_total[each[0]] += each[1]
        
        #총 통계
        total_list = sum(list(order_list.values_list('price',flat=True)))

        product_order_list = Order.objects.all().exclude(product=None).exclude(status__in=['4','5','8'])
        subscription_order_list = Order.objects.all().exclude(sub=None).exclude(status__in=['4','5','8'])

        product_list = list(product_order_list.values_list('product__name',flat=True))
        product_dict = {}
        for each in set(product_list):
            product_dict[each] = product_list.count(each)

        subscription_list = list(subscription_order_list.values_list('sub__box__name',flat=True))
        for each in set(subscription_list):
            product_dict[each] = subscription_list.count(each)


        if request.GET.get('first_date'):
            first_date = request.GET.get('first_date')
            last_date = request.GET.get('last_date')
            date_range = pd.period_range(first_date, last_date, freq='d')
            for i in date_range:
                range_total[str(i)] = 0

            order_list = Order.objects.filter(created_at__date__gte=first_date).filter(created_at__date__lte=last_date).exclude(created_at__date=today).exclude(status__in=['4','5','8'])
            values_list = order_list.values_list('price','created_at__date')
            for each in values_list:
                range_total[str(each[1])] += each[0]
            return JsonResponse({"range_total":range_total, "date_total":date_total, "user_total":user_total, "total_list":total_list, "product":product_dict},status=200)

        
        return JsonResponse({"date_total":date_total, "user_total":user_total, "total_list":total_list, "product":product_dict},status=200)