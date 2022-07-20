from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import permissions
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.contrib.staticfiles import finders
from shopmandb.models import *

import requests
import datetime
import json
import base64
import pandas as pd
import numpy as np
from email.mime.image import MIMEImage

from django.http import JsonResponse
from django.http import Http404

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.contrib.staticfiles import finders

def get_payload_from_token(request):  # 헤더에서 토큰만 반환
    auth = request.META.get('HTTP_TOKEN', b'').split(".")[1]
    auth += "=" * ((4 - len(auth) % 4) % 4)
    return json.loads(base64.b64decode(auth).decode("utf-8"))

def get_uat_from_refresh_token(refresh_token):
    payload=f'client_id={settings.OIDC_RP_CLIENT_SECRET}&client_secret={settings.OIDC_RP_CLIENT_SECRET}&grant_type=refresh_token&refresh_token={refresh_token}'
    headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
    }
    sat_response = requests.request("POST", settings.OIDC_OP_TOKEN_ENDPOINT, headers=headers, data=payload)
    return json.loads(sat_response.text), sat_response.status_code

# 타이틀
# [과일궁합 주문] 새 주문이 접수되었습니다 - 210505O-0098


# 상품
# [부여] 허니스윗 방울토마토 500g
#  or
# 정기배송 A박스
# 델라웨어 포도 1000g | 대저짭짤이토마토 500g | 함안 흑수박 5000g

# 링크
# https://shopman.d-if.kr/wms/shopmandb/order/98/change/

# 주문 번호
# 210505O-0098

# 구매시간


# 가격
# 50,000원

# 새벽배송여부
# 새벽배송으로 발송
#  or
# 일반배송으로 발송
# request_url : {request.scheme}://{request.get_host()} 필요
def send_order_email(order, request_url="https://shopman.d-if.kr"):
    try:
        email_title= f"[과일궁합 주문] 새 주문이 접수되었습니다 - {order.identifier}"
        is_single = order.sub is None
        if is_single:
            product = order.product.name
        else:
            user_box = UserBox.objects.get(order=order, is_selected=True)
            contents = []
            for value in json.loads(user_box.value):
                contents.append(
                    f"{value['name']} {int(value['amount'])}g")

            product = order.sub.box.name+" " + "맛보기" if order.is_test == True else "정기구독"
            product_sub = ' | '.join(contents)

        email_body = {
            "identifier": order.identifier,
            "product": product,
            "product_sub": None if is_single else product_sub,
            "link": f"{request_url}/wms/shopmandb/order/{order.pk}/change/",
            "purchase_time": order.created_at,
            "dawn_content": "새벽배송으로 발송" if order.is_dawn else "일반배송으로 발송",
            "price": order.final_price,
        }
        # email_title= f"[과일궁합 주문] 새 주문이 접수되었습니다 - 210505O-0098"
        # product = "[부산] 대저 짭짤이 토마토 500g"

        # email_body = {
        #     "identifier": "210505O-0098",
        #     "product": product,
        #     "product_sub": None,
        #     "link": "https://shopman.d-if.kr/wms/shopmandb/order/98/change/",
        #     "purchase_time": "2021-03-04 10:07:25.126732",
        #     "dawn_content": "새벽배송으로 발송",
        #     "price": f'{15000:,}',
        # }
        html_body = render_to_string('email_form.html', email_body)
        email = EmailMultiAlternatives(
            subject=email_title,
            body="",
            from_email='과일궁합 지원팀 <fm.order@d-if.kr>',
            # from_email='wm@d-if.kr',
            to=[settings.ORDER_EMAIL]
        )

        email.attach_alternative(html_body, "text/html")
        email.mixed_subtype = 'related'

        image_names = ['cs-banner']
        for image_name in image_names:
            with open(finders.find(f'images/{image_name}.png'), 'rb') as f:
                image_data = f.read()
                image = MIMEImage(image_data)
                image.add_header('Content-ID', f'<{image_name}>')
                # image.add_header('Content-Disposition', 'inline', filename="image_name")
                email.attach(image)

        res = email.send(fail_silently=False)
        if res in [1, '1']:
            OrderEmailLog.objects.create(
                order=order,
                status="success",
                message="1"
            )
        else:
            OrderEmailLog.objects.create(
                order=order,
                status=f"fail",
                message=res
            )
    except Exception as e:
        OrderEmailLog.objects.create(
            order=order,
            status=f"Exception fail",
            message=str(e)
        )