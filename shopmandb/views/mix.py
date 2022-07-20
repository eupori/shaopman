from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.parsers import FormParser
from drf_yasg.utils import swagger_auto_schema
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from shopmandb.models import *
from django.forms.models import model_to_dict
from rest_framework import serializers
from .payment import *

import shopmandb.models as models
import requests
import datetime
import json
import base64
import pandas as pd
import numpy as np
from django.http import JsonResponse
from django.http import Http404
import itertools
import random
import time
import copy

def create_box_identifier():
    if UserBox.objects.all().count() != 0:
        new_id = UserBox.objects.last().id + 1
    else:
        new_id = 1
    identifier = "Box" + str(new_id).zfill(4)
    return identifier

def get_payload_from_token(request):  # 헤더에서 토큰만 반환
    auth = request.META.get('HTTP_TOKEN', b'').split(".")[1]
    auth += "=" * ((4 - len(auth) % 4) % 4)
    return json.loads(base64.b64decode(auth).decode("utf-8"))

def get_uat_from_refresh_token(refresh_token): # 토큰이 만료되었을 경우 refresh token을 이용하여 재발급
    payload=f'client_id={settings.OIDC_RP_CLIENT_SECRET}&client_secret={settings.OIDC_RP_CLIENT_SECRET}&grant_type=refresh_token&refresh_token={refresh_token}'
    headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
    }
    sat_response = requests.request("POST", settings.OIDC_OP_TOKEN_ENDPOINT, headers=headers, data=payload)
    return json.loads(sat_response.text), sat_response.status_code

class MixPostAPISerializer(serializers.Serializer):
    data = serializers.CharField(max_length=500)
    box = serializers.CharField(max_length=50)

    
class BoxSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    class Meta:
        model = models.Box
        fields = (
            "identifier",
            "name",
            "image",
            "price",
            "description",
            "content",
            "tooltip"
        )
        examples = {
            "identifier":"30050",
            "name":"[S] 정기배송 A박스",
            "image":"https://www.soyutne.co.kr/data/goods/1/2019/06/149_tmp_9b5aa8917a08076db6c5a079961dae403908view.jpg",
            "price":50000,
            "description":"첫 구매 시 50% 할인",
            "content":"https://www.soyutne.co.kr/data/goods/1/2019/06/149_tmp_9b5aa8917a08076db6c5a079961dae403908view.jpg",
            "tooltip":"같은 가격, 20% 많은 과일 배송 무료 새벽배송",
        }

    def get_image(self, obj):
        return f"{self.context['request'].scheme}://{self.context['request'].get_host()}/media/"+str(obj.image)
    def get_content(self, obj):
        data = []
        data.append(obj.content)
        return data


# Create your views here.
class Test(APIView):
    permission_classes = [permissions.AllowAny,]
    
    def get(self, request, *args, **kwargs):
        return JsonResponse({"data":"datata"})
        
    def post(self, request, *args, **kwargs):
        if(request.POST.get('why1') is None):
            return JsonResponse({"success":False}, status=400)
        return JsonResponse({"success":True})


class BoxView(APIView): # 상품 리스트에 들어갈 박스 리스트를 반환
    permission_classes = [permissions.AllowAny,]
    
    parser_classes = (FormParser,)
    @swagger_auto_schema()
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
                    url = "/mix",
                    method = "GET",
                    request_code = request.GET,
                    response_code = "401",
                    message = "token, refresh_token expire",
                    user_id = "unknown"
                )
                return JsonResponse({"status":"expire", "msg":"token, refresh_token expire"}, status=401)

        username = get_username_from_uat(request)[0]['username']

        box = Box.objects.all().order_by('price')

        Log.objects.create(
            url = "/box",
            method = "GET",
            request_code = request.GET,
            response_code = "200",
            message = "success",
            user_id = username
        )

        return JsonResponse({"data":BoxSerializer(box, context={"request":request}, many=True).data})

def create_userbox(context, input_data, box, username, check_api, subscription=None):
    original_product = None
    setting = Setting.load()
    if setting.is_excel == True:
        original_product = json.loads(setting.original_product)
    else:
        original_product = get_original_product()
    fruit_ids = []
    descriptions = input_data['descriptions']
    for item in input_data['fruits']:
        fruit_ids.append(item['if_id'])
    selected_list = list(set(fruit_ids) & set(original_product.keys()))
    detail_dict = {}
    for item in input_data['fruits']:
        detail_dict[item['if_id']] = item

    
    sorted_fruit_list = list(
            filter(lambda x: x in list(selected_list), fruit_ids)
        )
    original_products = list(set(original_product.keys()))
    random.seed(10)
    random.shuffle(original_products)
    random.seed(int(1000 * time.time()) % 2**32)
    for item in original_products:
        if item not in sorted_fruit_list:
            sorted_fruit_list.append(item)

    if len(sorted_fruit_list) < 3:
        if check_api == True:
            return False, JsonResponse({"data":[], "token":context['token'],}, status=200)
        else:
            return False, []

    origin_price = int(box.price/100*65) 
    min_price =  int(box.price/100*60) 
    res_list = []
    target_id = -1
    print("start")
    for items in itertools.combinations(sorted_fruit_list, 3):
        print(items)
        cnt_list = []
        buy_check = False
        for ind, fruit in enumerate(items):
            cnt_list.append([x for x in range(len(original_product[fruit]))])
        copy_cnt_list = copy.deepcopy(cnt_list)
        print(copy_cnt_list)
        while copy_cnt_list[0]:
            print("while1")
            cnt0 = random.choice(copy_cnt_list[0])
            copy_cnt_list[0].remove(cnt0)
            copy_cnt_list[1] = copy.deepcopy(cnt_list[1])
            while copy_cnt_list[1]:
                print("while2")
                cnt1 = random.choice(copy_cnt_list[1])
                copy_cnt_list[1].remove(cnt1)
                copy_cnt_list[2] = copy.deepcopy(cnt_list[2])
                while copy_cnt_list[2]:
                    print("while3")
                    cnt2 = random.choice(copy_cnt_list[2])
                    copy_cnt_list[2].remove(cnt2)
                    
                    p_list = []
                    p_list.append(original_product[items[0]][cnt0])
                    p_list.append(original_product[items[1]][cnt1])
                    p_list.append(original_product[items[2]][cnt2])
                    p_price = [p['per_price'] for p in p_list]
                    p_unit = [p['min_unit'] for p in p_list]
                    # p_step_type = [p['unit'] for p in p_list]
                    p_step = [p['step'] for p in p_list]
                    # for step in p_step_type:
                    # 	if step in ["KG", "kg"]:
                    # 		p_step.append(0.1)
                    # 	elif step == "과":
                    # 		p_step.append(1)
                    # 	elif step in ["팩", "박스", "송이", "개"]:
                    # 		p_step.append(0.5)
                    total_price = sum([int(p_price[i])*float(p_unit[i]) for i in range(len(p_list))])
                    if total_price >= min_price and total_price <= origin_price:
                        tmp_list = []

                        for k in range(len(p_list)): 
                            tmp_list.append(
                                {	"id":"???", 
                                    "name": p_list[k]['name'],
                                    "fruit_name": descriptions[p_list[k]['if_id']]["name"],
                                    "price": int(p_price[k]*p_unit[k]), 
                                    "if_id": p_list[k]['if_id'], 
                                    "unit": p_list[k]['unit'],
                                    "amount":p_unit[k],
                                    "image":descriptions[p_list[k]['if_id']]["image"],
                                    "min_unit":p_list[k]['min_unit'],
                                    "detail":detail_dict[p_list[k]['if_id']] if p_list[k]['if_id'] in detail_dict else None,
                                    "nutrition":descriptions[p_list[k]['if_id']]["nutrition"],
                                    "storage_method":descriptions[p_list[k]['if_id']]["storage_method"],
                                    "selection_method":descriptions[p_list[k]['if_id']]["selection_method"],
                                    "item_code":p_list[k]['item_code']
                                }
                            )
                        #userbox 생성
                        id = create_box_identifier()
                        user_box = UserBox.objects.create(
                            identifier = id,
                            box = box,
                            user_id = username,
                            value = json.dumps(tmp_list),
                            target = id if target_id == -1 else target_id,
                            is_selected = True if target_id == -1 else False,
                            subscription = subscription,
                            survey_names = json.dumps(input_data['survey_names']) if 'survey_names' in input_data else json.dumps([])
                        )

                        if target_id == -1:
                            target_id = id
                        series = {"user_box_id":id,"box":tmp_list}

                        res_list.append(series)
                        buy_check = True
                        break
                    elif total_price < min_price:
                        min_step_prices = origin_price - total_price
                        
                        # for i in range(len(p_list)):
                        # 	if min_step_prices > p_price[i] * p_step[i]:
                        # 		target = i
                        target = -1
                        target_list = []
                        for i in range(len(p_list)):
                            if min_step_prices > p_price[i] * p_step[i]:
                                target_list.append((i, p_price[i] * p_unit[i]))
                        
                        if len(target_list) == 1:
                            target = target_list[0][0]
                        elif len(target_list) != 0:
                            target = min(target_list, key=lambda x:x[1])[0]
                            pass
                        if target == -1:
                            break
                        while origin_price - total_price > 0:
                            remain_price = origin_price - total_price
                            p_unit[target] += p_step[target] * 1
                            # int(remain_price / p_price[target])
                            total_price = sum([float(p_price[i])*int(p_unit[i]) for i in range(len(p_list))])
                            
                            if total_price >= min_price and origin_price >= total_price:
                                tmp_list = []
                                for k in range(len(p_list)): 
                                    tmp_list.append(
                                        {	"id":"???", 
                                            "name": p_list[k]['name'],
                                            "fruit_name": descriptions[p_list[k]['if_id']]["name"],
                                            "price": int(p_price[k]*p_unit[k]), 
                                            "if_id": p_list[k]['if_id'], 
                                            "unit": p_list[k]['unit'],
                                            "amount":p_unit[k],
                                            "image":descriptions[p_list[k]['if_id']]["image"],
                                            "min_unit":p_list[k]['min_unit'],
                                            "detail":detail_dict[p_list[k]['if_id']] if p_list[k]['if_id'] in detail_dict else None,
                                            "nutrition":descriptions[p_list[k]['if_id']]["nutrition"],
                                            "storage_method":descriptions[p_list[k]['if_id']]["storage_method"],
                                            "selection_method":descriptions[p_list[k]['if_id']]["selection_method"],
                                            "item_code":p_list[k]['item_code']
                                        }
                                    )
                                    
                                #userbox 생성
                                id = create_box_identifier()
                                user_box = UserBox.objects.create(
                                    identifier = id,
                                    box = box,
                                    user_id = username,
                                    value = json.dumps(tmp_list),
                                    target = id if target_id == -1 else target_id,
                                    is_selected = True if target_id == -1 else False,
                                    subscription = subscription,
                                    survey_names = json.dumps(input_data['survey_names']) if 'survey_names' in input_data else json.dumps([])
                                )

                                if target_id == -1:
                                    target_id = id
                                series = {"user_box_id":id,"box":tmp_list}
                                    
                                res_list.append(series)
                                buy_check = True
                                break
                        if buy_check == True:
                            break


                if buy_check == True:
                    break
            if buy_check == True:
                break	
        if len(res_list) == 3:
            break
    return True, res_list	

def get_original_product():
    url = "http://bestfdif.heeyam.com/apicall/itemList"
    headers = {}
    payload="{\n    \"header\": {\n        \"RequestId\": \"H2021DIF001\",\n        \"ClientCode\": \"DIF01\"\n    },\n    \"body\": {\n    }\n}"
    response = requests.request("POST", url, headers=headers, data=payload)
    res = json.loads(response.text)
    res_dict = {}
    for item in res['body']['difItemList']:
        if len(item['difItemDetailList']) > 0:
            res_dict[item['org_difItemCode']] = []
            for detail in item['difItemDetailList']:
                res_dict[item['org_difItemCode']].append(
                {'name': detail['DBName'],
                   'if_id': item['org_difItemCode'],
                   'item_code':detail['itemCode'],
                   'price': int(detail['werightPrice']),
                   'unit': 1,
                   'step': int(detail['incrementUnit']),
                   'min_unit': int(detail['minWeight']),
                   'per_price': float(detail['werightPrice'])/float(detail['minWeight'])}
                )
    return res_dict   
class MixView(APIView):
    
    #request : 127.0.0.1:8000/product?fruits=1,2,5&box=30050
    permission_classes = [permissions.AllowAny,]
    # original_product = {
    # 	"IFCP1508":[{"name":"[고령] 킹 명품 설향 딸기", 
    # 					"price":18800, 
    # 					"if_id":"IFCP1508", 
    # 					"unit":"팩", 
    # 					"min_unit":1},
    # 				{"name":"[담양] 죽향딸기", 
    # 					"price":19800, 
    # 					"if_id":"IFCP1508", 
    # 					"unit":"팩", 
    # 					"min_unit":1}],
    # 	"IFCP1640":[{"name":"토종다래", 
    # 					"price":10000, 
    # 					"if_id":"IFCP1640", 
    # 					"unit":"kg", 
    # 					"min_unit":1}],
    # 	"IFCP1633":[{"name":"[성주] 꿀 참외", 
    # 					"price":10800, 
    # 					"if_id":"IFCP1633", 
    # 					"unit":"kg", 
    # 					"min_unit":1}],
    # 	"IFCP1340":[{"name":"대저 짭짤이", 
    # 					"price":21800, 
    # 					"if_id":"IFCP1340", 
    # 					"unit":"kg", 
    # 					"min_unit":1.5}],
    # 	"IFCP1484":[{"name":"[산청] 지리산 촉촉 반건시 곶감", 
    # 					"price":13800, 
    # 					"if_id":"IFCP1340", 
    # 					"unit":"kg", 
    # 					"min_unit":1.5}]
    # }
    # original_product = '{"IFCP1540": [{"name": "\\uc2e0\\uace0\\ubc30", "if_id": "IFCP1540", "price": 12000, "unit": "kg", "min_unit": 1.5}, {"name": "\\ucc3d\\uc870\\ubc30", "if_id": "IFCP1540", "price": 7800, "unit": "\\uacfc", "min_unit": 1.0}], "IFCP1340": [{"name": "[\\ubd80\\uc5ec] \\ud5c8\\ub2c8\\uc2a4\\uc717 \\ud1a0\\ub9c8\\ud1a0", "if_id": "IFCP1340", "price": 13800, "unit": "kg", "min_unit": 1.5}, {"name": "[\\uc9c4\\ucc9c] \\uace8\\ub4e0\\ubca8\\ub300\\ucd94 \\ubc29\\uc6b8\\ud1a0\\ub9c8\\ud1a0", "if_id": "IFCP1340", "price": 21600, "unit": "kg", "min_unit": 1.5}, {"name": "\\ub300\\uc800 \\uc9ed\\uc9e4\\uc774", "if_id": "IFCP1340", "price": 21800, "unit": "KG", "min_unit": 1.5}, {"name": "\\ud5c8\\ub2c8\\uc2a4\\uc717\\ubc29\\uc6b8\\ud1a0\\ub9c8\\ud1a0", "if_id": "IFCP1340", "price": 17800, "unit": "kg", "min_unit": 1.5}], "IFCP1573": [{"name": "[\\ubb38\\uacbd] \\uc288\\ud37c \\ub9ac\\uce58 \\ubd80\\uc0ac", "if_id": "IFCP1573", "price": 4266, "unit": "\\uacfc", "min_unit": 1.0}, {"name": "[\\ubb38\\uacbd] \\uc288\\ud37c \\ub9ac\\uce58 \\ubabb\\ub09c\\uc774 \\ubd80\\uc0ac", "if_id": "IFCP1573", "price": 4266, "unit": "\\uacfc", "min_unit": 1.0}, {"name": "\\ud64d\\ub85c\\uc0ac\\uacfc", "if_id": "IFCP1573", "price": 15000, "unit": "kg", "min_unit": 2.0}, {"name": "\\ud64d\\ub85c\\uc0ac\\uacfc", "if_id": "IFCP1573", "price": 14800, "unit": "kg", "min_unit": 2.0}], "IFCP1484": [{"name": "[\\uc0b0\\uccad] \\uc9c0\\ub9ac\\uc0b0 \\ucd09\\ucd09 \\ubc18\\uac74\\uc2dc \\uacf6\\uac10", "if_id": "IFCP1484", "price": 13800, "unit": "\\ud329", "min_unit": 1.0}, {"name": "[\\uc0b0\\uccad] \\uc9c0\\ub9ac\\uc0b0 \\ud669\\uc81c \\uacf6\\uac10 \\uc911", "if_id": "IFCP1484", "price": 39800, "unit": "\\ubc15\\uc2a4", "min_unit": 1.0}], "IFCP1508": [{"name": "[\\uace0\\ub839] \\ud0b9 \\uba85\\ud488 \\uc124\\ud5a5 \\ub538\\uae30", "if_id": "IFCP1508", "price": 18800, "unit": "\\ud329", "min_unit": 1.0}, {"name": "[\\ub2f4\\uc591] \\uc8fd\\ud5a5\\ub538\\uae30", "if_id": "IFCP1508", "price": 19800, "unit": "\\ud329", "min_unit": 1.0}], "IFCP1640": [{"name": "\\ud1a0\\uc885\\ub2e4\\ub798", "if_id": "IFCP1640", "price": 12800, "unit": "kg", "min_unit": 1.0}], "IFCP1633": [{"name": "[\\uc131\\uc8fc] \\uafc0 \\ucc38\\uc678", "if_id": "IFCP1633", "price": 10800, "unit": "kg", "min_unit": 1.0}], "IFCP1495": [{"name": "\\ub808\\ub4dc\\ud55c\\ub77c\\ubd09", "if_id": "IFCP1495", "price": 12800, "unit": "kg", "min_unit": 1.5}, {"name": "\\ucc9c\\ud61c\\ud5a5", "if_id": "IFCP1495", "price": 12800, "unit": "KG", "min_unit": 1.5}, {"name": "\\uce74\\ub77c\\ud5a5", "if_id": "IFCP1495", "price": 12800, "unit": "kg", "min_unit": 1.5}, {"name": "\\uc218\\ub77c\\ud5a5", "if_id": "IFCP1495", "price": 10800, "unit": "kg", "min_unit": 1.5}, {"name": "\\ud558\\uc6b0\\uc2a4 \\uade4", "if_id": "IFCP1495", "price": 12800, "unit": "KG", "min_unit": 1.5}], "IFCP1531": [{"name": "\\ub178\\uc744\\uba5c\\ub860", "if_id": "IFCP1531", "price": 15800, "unit": "\\uac1c", "min_unit": 1.0}, {"name": "\\ubc31\\uc790\\uba5c\\ub860", "if_id": "IFCP1531", "price": 11800, "unit": "\\uac1c", "min_unit": 1.0}, {"name": "\\uc5bc\\uc2a4\\uba5c\\ub860", "if_id": "IFCP1531", "price": 17800, "unit": "\\uac1c", "min_unit": 1.0}], "IFCP1593": [{"name": "\\uace0\\ucc3d\\uc218\\ubc15", "if_id": "IFCP1593", "price": 24800, "unit": "\\uac1c", "min_unit": 1.0}, {"name": "\\ube14\\ub799\\ub9dd\\uace0\\uc218\\ubc15", "if_id": "IFCP1593", "price": 15800, "unit": "\\uac1c", "min_unit": 1.0}], "IFCP1654": [{"name": "\\ub378\\ub77c\\uc6e8\\uc5b4\\ud3ec\\ub3c4", "if_id": "IFCP1654", "price": 30000, "unit": "kg", "min_unit": 1.0}, {"name": "\\uac70\\ubd09", "if_id": "IFCP1654", "price": 20000, "unit": "kg", "min_unit": 1.0}, {"name": "\\ucea0\\ubca8\\ud3ec\\ub3c4", "if_id": "IFCP1654", "price": 12800, "unit": "kg", "min_unit": 1.0}], "IFCP1557": [{"name": "\\ud669\\ub3c4", "if_id": "IFCP1557", "price": 18000, "unit": "kg", "min_unit": 1.0}, {"name": "\\ucc9c\\ub3c4\\ubcf5\\uc22d\\uc544", "if_id": "IFCP1557", "price": 9800, "unit": "KG", "min_unit": 1.0}], "IFCP1621": [{"name": "\\ub300\\uc11d \\uc790\\ub450", "if_id": "IFCP1621", "price": 15800, "unit": "KG", "min_unit": 1.5}, {"name": "\\uc774\\uafb8\\ubbf8 \\uc790\\ub450", "if_id": "IFCP1621", "price": 18800, "unit": "kg", "min_unit": 1.5}], "IFCP3799": [{"name": "\\uccb4\\ub9ac", "if_id": "IFCP3799", "price": 60000, "unit": "kg", "min_unit": 0.5}], "IFCP1521": [{"name": "\\uc560\\ud50c\\ub9dd\\uace0", "if_id": "IFCP1521", "price": 18000, "unit": "\\uac1c", "min_unit": 1.0}], "IFCP1564": [{"name": "\\ube14\\ub8e8\\ubca0\\ub9ac", "if_id": "IFCP1564", "price": 30000, "unit": "kg", "min_unit": 1.0}]}'
    #6개짜리
    original_product='{"IFCP1495": [{"name": "\\ud55c\\ub77c\\ubd09(\\uc368\\ub2c8\\ud2b8) - \\ub300", "if_id": "IFCP1495", "price": 5000, "unit": 1, "min_unit": 500}, {"name": "\\ud55c\\ub77c\\ubd09(\\uc368\\ub2c8\\ud2b8) - \\uc911 ", "if_id": "IFCP1495", "price": 3300, "unit": 1, "min_unit": 330}], "IFCP1508": [{"name": "\\ub538\\uae30(\\uae08\\uc2e4)", "if_id": "IFCP1508", "price": 20000, "unit": 1, "min_unit": 500}, {"name": "\\ub538\\uae30(\\uc8fd\\ud5a5)", "if_id": "IFCP1508", "price": 12000, "unit": 1, "min_unit": 500}], "IFCP1633": [{"name": "\\ucc38\\uc678 - \\ub300", "if_id": "IFCP1633", "price": 2600, "unit": 1, "min_unit": 330}, {"name": "\\ucc38\\uc678 - \\uc911", "if_id": "IFCP1633", "price": 2000, "unit": 1, "min_unit": 250}, {"name": "\\ucc38\\uc678 - \\uc18c", "if_id": "IFCP1633", "price": 1600, "unit": 1, "min_unit": 200}], "IFCP1340": [{"name": "\\ud5c8\\ub2c8\\uc2a4\\uc717\\ubc29\\uc6b8\\ud1a0\\ub9c8\\ud1a0", "if_id": "IFCP1340", "price": 1100, "unit": 1, "min_unit": 100}, {"name": "\\ud5c8\\ub2c8\\uc2a4\\uc717\\ud1a0\\ub9c8\\ud1a0 (\\uc644\\uc219)", "if_id": "IFCP1340", "price": 1160, "unit": 1, "min_unit": 160}, {"name": "\\ub300\\uc800\\uc9ed\\uc9e4\\uc774\\ud1a0\\ub9c8\\ud1a0", "if_id": "IFCP1340", "price": 1200, "unit": 1, "min_unit": 100}, {"name": "\\ub300\\ucd94\\ubc29\\uc6b8\\ud1a0\\ub9c8\\ud1a0", "if_id": "IFCP1340", "price": 1500, "unit": 1, "min_unit": 100}], "IFCP1531": [{"name": "\\ub178\\uc744 \\uba5c\\ub860 - \\uc911", "if_id": "IFCP1531", "price": 7600, "unit": 1, "min_unit": 1600}, {"name": "\\ub178\\uc744 \\uba5c\\ub860 - \\ub300", "if_id": "IFCP1531", "price": 9500, "unit": 1, "min_unit": 2000}, {"name": "\\uba38\\uc2a4\\ud06c \\uba5c\\ub860 - \\uc911", "if_id": "IFCP1531", "price": 12000, "unit": 1, "min_unit": 1600}, {"name": "\\uba38\\uc2a4\\ud06c \\uba5c\\ub860 - \\ub300", "if_id": "IFCP1531", "price": 13000, "unit": 1, "min_unit": 2000}]}'

    @swagger_auto_schema(request_body=MixPostAPISerializer(),)
    def post(self, request, *args, **kwargs):
        refresh_token = request.META.get('HTTP_REFRESHTOKEN', b'')
        token = request.META.get('HTTP_TOKEN', b'')
        context = {}
        context['token'] = token

        #token을 디코딩 -> exp 확인 날자가 지나면 tokken을 재발급(refresh 토큰을 이용해서)

        payload = get_payload_from_token(request)
        exp = datetime.datetime.fromtimestamp(int(payload['exp']))
        #토큰 내의 날짜를 확인하여 재발급 여부 확인 후 리프레시 토큰 재발급 SSO에 refresh토큰을 bearer를 통해서 url에 post로 요청
        is_refresh = False
        if datetime.datetime.now() > exp:
            tokens, status = get_uat_from_refresh_token(refresh_token)
            if status == 200:
                context['refresh_token'] = tokens['refresh_token']
                context['token'] = tokens['access_token']
                is_refresh = True
            else:
                Log.objects.create(
                    url = "/mix",
                    method = "POST",
                    request_code = request.POST,
                    response_code = "401",
                    message = "token, refresh_token expire",
                    user_id = "unknown"
                )
                return JsonResponse({"status":"expire", "msg":"token, refresh_token expire"}, status=401)

        result = []

        data = request.POST.get("data")
        input_data = json.loads(data)['data']
        box_id = request.POST.get("box")
        box = models.Box.objects.get(identifier=box_id)
        # print(json.loads(data)['fruits'])
        
        status, res_list = create_userbox(context,input_data, box, payload['preferred_username'], True)
        if status == False:
            return res_list
        #result type : 과일 리스트를 가지고 있는 리스트
        #현재 한글 깨짐
        # result = [
        # 	[{	"id":"10000101", 
        # 			"name":"[고령] 킹 명품 설향 딸기", 
        # 			"price":10000, 
        # 			"if_id":"IFCP1508", 
        # 			"unit":"pack",
        # 			"amount":1,
        # 			"image":"http://fruits-test.d-if.kr/media/fruit/IFCP1508.jpg",
        # 			"min_unit":1,},
        # 		{"id":"10000102", 
        # 			"name":"토종다래", 
        # 			"price":10000, 
        # 			"if_id":"IFCP1640", 
        # 			"unit":"kg",
        # 			"amount":3,
        # 			"image":"http://fruits-test.d-if.kr/media/fruit/IFCP1502.jpg",
        # 			"min_unit":1},
        # 		{"id":"10000103", 
        # 			"name":"대저 짭짤이", 
        # 			"price":12000, 
        # 			"if_id":"IFCP1340", 
        # 			"unit":"kg",
        # 			"amount":3,
        # 			"image":"http://fruits-test.d-if.kr/media/fruit/IFCP1340.jpg",
        # 			"min_unit":1.5}],
        # 	[{"id":"10000104", 
        # 			"name":"킹 샤인", 
        # 			"price":32000, 
        # 			"if_id":"IFCP1654", 
        # 			"unit":"ea",
        # 			"amount":1,
        # 			"image":"https://img.khan.co.kr/news/2019/08/23/l_2019082301002623300208011.jpg",
        # 			"min_unit":1},
        # 		{"id":"10000105", 
        # 			"name":"[담양] 죽향딸기", 
        # 			"price":9500, 
        # 			"if_id":"IFCP1508", 
        # 			"unit":"pack",
        # 			"amount":2,
        # 			"image":"https://t1.daumcdn.net/liveboard/realfood/f61e517c8bf9408c8de3e93dd8c236e4.JPG",
        # 			"min_unit":1},
        # 		{"id":"10000106", 
        # 			"name":"[성주] 꿀 참외", 
        # 			"price":4000, 
        # 			"if_id":"IFCP1633", 
        # 			"unit":"kg",
        # 			"amount":2,
        # 			"image":"https://lh3.googleusercontent.com/proxy/jWrHEKgENFDS6oIQsQI2aDAUQbfqRVtuwXS00LMtRxzdRZOpMhCh7sPeaoWXGCjVDrobkBT7o9BL3_nX9rA7dw6N4_oRuj9L0h_EtWj5NMJHKxSNHLE",
        # 			"min_unit":1}],
        # 	[{"id":"10000103", 
        # 			"name":"대저 짭짤이", 
        # 			"price":12000, 
        # 			"if_id":"IFCP1340", 
        # 			"unit":"kg",
        # 			"amount":3,
        # 			"image":"https://funshop.akamaized.net/products/0000056520/vs_image800.jpg",
        # 			"min_unit":1.5},
        # 		{"id":"10000107", 
        # 			"name":"샤인 머스켓", 
        # 			"price":20000, 
        # 			"if_id":"IFCP1654", 
        # 			"unit":"송이",
        # 			"amount":1,
        # 			"image":"https://post-phinf.pstatic.net/MjAxOTA3MzBfMjYx/MDAxNTY0NDcxNDA4OTYx.nP5vsqTr_IWwXB29x765DXN44yrzbOJvw-K_1z9GDUYg.cs1EpkiK2g4qTGH-iU-Zxkw6kvFLzi9STUj86ZZSeXIg.JPEG/shutterstock_1192030990.jpg",
        # 			"min_unit":1},
        # 		{"id":"10000102", 
        # 			"name":"토종다래", 
        # 			"price":10000, 
        # 			"if_id":"IFCP1640", 
        # 			"unit":"kg",
        # 			"amount":3,
        # 			"image":"https://t1.daumcdn.net/cfile/blog/9987E24F5E617B3F1D",
        # 			"min_unit":1}],
        # ]

        # 토종다래%10000%IFCP1640%kg|샤인 머스켓%20000%IFCP1654
        # + 설명, 논문id
        
        return JsonResponse({"data":res_list, "token":context['token']}, status=200)


    # def post(self, request, *args, **kwargs):
    # 	if(request.POST.get('why1') is None):
    # 		return JsonResponse({"success":False}, status=400)
    # 	return JsonResponse({"success":True})



        #[{
        # "userbox_id":1,
        # "box":[{	"id":"10000101", 
        # 			"name":"[고령] 킹 명품 설향 딸기", 
        # 			"price":10000, 
        # 			"if_id":"IFCP1508", 
        # 			"unit":"pack",
        # 			"amount":1,
        # 			"image":"http://fruits-test.d-if.kr/media/fruit/IFCP1508.jpg",
        # 			"min_unit":1,},
        # 		{"id":"10000102", 
        # 			"name":"토종다래", 
        # 			"price":10000, 
        # 			"if_id":"IFCP1640", 
        # 			"unit":"kg",
        # 			"amount":3,
        # 			"image":"http://fruits-test.d-if.kr/media/fruit/IFCP1502.jpg",
        # 			"min_unit":1},
        # 		{"id":"10000103", 
        # 			"name":"대저 짭짤이", 
        # 			"price":12000, 
        # 			"if_id":"IFCP1340", 
        # 			"unit":"kg",
        # 			"amount":3,
        # 			"image":"http://fruits-test.d-if.kr/media/fruit/IFCP1340.jpg",
        # 			"min_unit":1.5}]},
        # 	[{"id":"10000104", 
        # 			"name":"킹 샤인", 
        # 			"price":32000, 
        # 			"if_id":"IFCP1654", 
        # 			"unit":"ea",
        # 			"amount":1,
        # 			"image":"https://img.khan.co.kr/news/2019/08/23/l_2019082301002623300208011.jpg",
        # 			"min_unit":1},
        # 		{"id":"10000105", 
        # 			"name":"[담양] 죽향딸기", 
        # 			"price":9500, 
        # 			"if_id":"IFCP1508", 
        # 			"unit":"pack",
        # 			"amount":2,
        # 			"image":"https://t1.daumcdn.net/liveboard/realfood/f61e517c8bf9408c8de3e93dd8c236e4.JPG",
        # 			"min_unit":1},
        # 		{"id":"10000106", 
        # 			"name":"[성주] 꿀 참외", 
        # 			"price":4000, 
        # 			"if_id":"IFCP1633", 
        # 			"unit":"kg",
        # 			"amount":2,
        # 			"image":"https://lh3.googleusercontent.com/proxy/jWrHEKgENFDS6oIQsQI2aDAUQbfqRVtuwXS00LMtRxzdRZOpMhCh7sPeaoWXGCjVDrobkBT7o9BL3_nX9rA7dw6N4_oRuj9L0h_EtWj5NMJHKxSNHLE",
        # 			"min_unit":1}],
        # 	[{"id":"10000103", 
        # 			"name":"대저 짭짤이", 
        # 			"price":12000, 
        # 			"if_id":"IFCP1340", 
        # 			"unit":"kg",
        # 			"amount":3,
        # 			"image":"https://funshop.akamaized.net/products/0000056520/vs_image800.jpg",
        # 			"min_unit":1.5},
        # 		{"id":"10000107", 
        # 			"name":"샤인 머스켓", 
        # 			"price":20000, 
        # 			"if_id":"IFCP1654", 
        # 			"unit":"송이",
        # 			"amount":1,
        # 			"image":"https://post-phinf.pstatic.net/MjAxOTA3MzBfMjYx/MDAxNTY0NDcxNDA4OTYx.nP5vsqTr_IWwXB29x765DXN44yrzbOJvw-K_1z9GDUYg.cs1EpkiK2g4qTGH-iU-Zxkw6kvFLzi9STUj86ZZSeXIg.JPEG/shutterstock_1192030990.jpg",
        # 			"min_unit":1},
        # 		{"id":"10000102", 
        # 			"name":"토종다래", 
        # 			"price":10000, 
        # 			"if_id":"IFCP1640", 
        # 			"unit":"kg",
        # 			"amount":3,
        # 			"image":"https://t1.daumcdn.net/cfile/blog/9987E24F5E617B3F1D",
        # 			"min_unit":1}],
        # ]
