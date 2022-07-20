from django.core.management.base import BaseCommand, CommandError
from shopmandb.models import *
from shopmandb.views import *
from django.conf import settings

import xmltodict
import requests
import datetime
import json

def jmf_user_deposit_edit(id, val, reason_code):
    url = "http://bestfruit.godomall.com/api/ig_member_info.php"
    data={'ig_key': JMF_API_KEY,
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

def update_mileage(order):
    # 마일리지 업데이트
    paid_price = order.price - order.mileage - order.deposit - order.shipping_fee
    val = paid_price * 0.01
    print("paid price: ", paid_price, "val : ", val)
    response = jmf_user_mileage_edit(order.user_id, -val,'01005002') # 마일리지 충전
    if response['result'] == '200':
        print('마일리지 적립 성공')
        order.mileage_status = '1'
        order.save()

        MileageLog.objects.create(
            user_id = order.user_id,
            mileage = val,
            status = response['result'],
            message = "마일리지 적립 성공"
        )
    else:
        print('마일리지 적립 실패')
        print(response)

        MileageLog.objects.create(
            user_id = order.user_id,
            mileage = val,
            status = response['result'],
            message = response
        )

def refund_mileage(order):
    val = order.mileage
    response = jmf_user_mileage_edit(order.user_id, -val,'01005003') # 마일리지 환급
    order.mileage_status = '4'
    order.save()

    if response['result'] == '200':
        print('마일리지 적립 성공')
        order.mileage_status = '1'
        order.save()

        MileageLog.objects.create(
            user_id = order.user_id,
            mileage = val,
            status = response['result'],
            message = "주문 취소에 의한 마일리지 환급"
        )
    else:
        print('마일리지 적립 실패')
        print(response)

        MileageLog.objects.create(
            user_id = order.user_id,
            mileage = val,
            status = response['result'],
            message = response
        )

def refund_deposit(order):
    val = order.deposit
    jmf_user_deposit_edit(order.user_id, val)


class Command(BaseCommand):
    help = 'Automatic agent for mileage'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        today = datetime.datetime.now()
        after_three_days = (today - datetime.timedelta(days=3))
        date = datetime.datetime.now().date() - datetime.timedelta(days=3)
        print("update mileage handle")
        
        # 취소된 주문건들
        for order in Order.objects.filter(status="8", created_at__lte=date, sub__isnull=True):
            if order.deposit:
                refund_deposit(order)
            if order.mileage_status == '3':
                refund_mileage(order)


        # 마일리지 적립, 주문 취소 건은 mileage_status = "3" or "2"
        for order in Order.objects.filter(mileage_status='0', created_at__lte=date, sub__isnull=True):
            update_mileage(order)
