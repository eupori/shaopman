from django.contrib import admin
from shopmandb.models import Order, Product, Subscription, UserBox, Box
import json
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

class EventAdminSite(admin.AdminSite):
    site_header = "과일궁합 WMS 관리사이트"
    site_title = "과일궁합 WMS 관리사이트"
    index_title = "과일궁합을 통한 주문내역을 조회하고, 관리합니다."

wms_site = EventAdminSite(name='event_admin')

class CouponIsUsedFilter(admin.SimpleListFilter):
    title = '쿠폰 사용 여부'
    parameter_name = 'coupon'
    
    def lookups(self, request, model_admin):
        return (
            ('used', _("쿠폰 사용")),
            ('un_used', _("쿠폰 미사용")),
            )

    def queryset(self, request, queryset):
        if self.value() == "used":
            return queryset.filter(product__identifier="P00000ZN").filter(final_price=0)
        elif self.value() == "un_used":
            return queryset.exclude(product__identifier="P00000ZN").exclude(final_price=0)

class TesterFilter(admin.SimpleListFilter):
    title = '테스터 필터'
    parameter_name = 'test'
    
    def lookups(self, request, model_admin):
        return (
            ('tester', _("테스터")),
            ('user', _("사용자")),
            )

    def queryset(self, request, queryset):
        if self.value() == "tester":
            return queryset.filter(user_id__icontains="test")
        elif self.value() == "user":
            return queryset.exclude(user_id__icontains="test")

@admin.register(Order, site=wms_site)
class OrderAdmin(admin.ModelAdmin):
    model = Order
    fields = [
        'identifier', 'status', 'invoice_number', 'invoice_company','channel',
        'user_id', 'get_product_name', 'amount',
        'get_product_price', 'get_order_price', 'get_final_price',
        'get_shipping_fee','get_deposit','get_mileage','get_created_at',
        'get_orderer_name', 'get_recipient_name','get_recipient_phone','get_post_number',
        'get_address','get_address_detail','get_request',
        'get_entrance_password','get_sub_identifier','get_user_box_id',
        'get_user_box','get_sub_shipping_range','get_sub_weekday',
        'get_estimate_date','get_user_box_identifier','get_dawn','get_is_test', 'comment',
    ]
    list_display = [
        'identifier', 'user_id', 'get_orderer_name', 'get_coupon', 'get_recipient_name', 'status',  
        'price', 'amount', 'product', 'get_dawn','get_is_test',
        'created_at', 'updated_at', 
    ]
    list_filter = ('status', 'payment_type', CouponIsUsedFilter, TesterFilter,)
    search_fields = ('identifier', 'recipient_name', 'address',)
    readonly_fields = (
        'identifier', 'channel',
        'user_id', 'get_product_name', 'amount', 
        'get_product_price', 'get_order_price', 'get_final_price',
        'get_shipping_fee','get_deposit','get_mileage','get_created_at',
        'get_orderer_name', 'get_recipient_name','get_recipient_phone','get_post_number',
        'get_address','get_address_detail','get_request',
        'get_entrance_password','get_sub_identifier','get_user_box_id',
        'get_user_box','get_sub_shipping_range','get_sub_weekday',
        'get_estimate_date','get_user_box_identifier','get_dawn','get_is_test',
    )
    def get_coupon(self, obj):
        if obj.product:
            if obj.product.identifier == "P00000ZN" and obj.final_price == 0:
                return True
        
        return False
    get_coupon.boolean = True    
    get_coupon.short_description = '쿠폰 사용 여부'

    def get_product_name(self, obj):
        return obj.product.name
    get_product_name.short_description = '제품명'

    def get_product_price(self, obj):
        return obj.product.price
    get_product_price.short_description = '판매가'

    def get_order_price(self, obj):
        return obj.price
    get_order_price.short_description = '총 품목 금액'

    def get_final_price(self, obj):
        return obj.final_price
    get_final_price.short_description = '총 결제 금액'

    def get_shipping_fee(self, obj):
        return obj.shipping_fee
    get_shipping_fee.short_description = '총 배송 금액'

    def get_deposit(self, obj):
        return obj.deposit
    get_deposit.short_description = '사용된 총 예치금'

    def get_mileage(self, obj):
        return obj.mileage
    get_mileage.short_description = '사용된 총 마일리지'

    def get_created_at(self, obj):
        return obj.order.created_at.strftime("%Y-%m-%d")
    get_created_at.short_description = '주문 일자'

    def get_orderer_name(self, obj):
        return obj.orderer_name
    get_orderer_name.short_description = '주문자 이름'

    def get_recipient_name(self, obj):
        return obj.recipient_name
    get_recipient_name.short_description = '수취인 이름'

    def get_recipient_phone(self, obj):
        return obj.recipient_phone
    get_recipient_phone.short_description = '수취인 핸드폰 번호'

    def get_post_number(self, obj):
        return obj.post_number
    get_post_number.short_description = '수취인 우편번호(5자리)'

    def get_address(self, obj):
        return obj.address
    get_address.short_description = '수취인 주소'

    def get_address_detail(self, obj):
        return obj.address_detail
    get_address_detail.short_description = '수취인 나머지 주소'

    def get_request(self, obj):
        return obj.request
    get_request.short_description = '주문시 남기는 글'

    def get_is_test(self, obj):
        return obj.is_test
    get_is_test.short_description = '체험분 여부'

    def get_comment(self, obj):
        return obj.comment
    get_comment.short_description = '직원 코멘트'

    def get_entrance_password(self, obj):
        return obj.entrance_password
    get_entrance_password.short_description = '현관 비밀번호'

    def get_sub_identifier(self, obj):
        return obj.sub.identifier if obj.sub else obj.sub.identifier
    get_sub_identifier.short_description = '구독 아이디'

    def get_user_box_id(self, obj):
        userbox = obj.userbox_order.last()
        return userbox.identifier
    get_user_box_id.short_description = '유저박스 아이디'

    def get_user_box(self, obj):
        if obj.sub:
            user_box = UserBox.objects.filter(
                    subscription=obj.sub, is_selected=True, order=obj)[0]
            contents = []
            for value in json.loads(user_box.value):
                contents.append(
                        f"{value['name']} {int(value['amount'])}g")
            return ' | '.join(contents)
        else:
            return '-'
    get_user_box.short_description = '박스 구성'
            
    def get_sub_shipping_range(self, obj):
        return obj.sub.get_shipping_range_display()
    get_sub_shipping_range.short_description = '구독 주기'

    def get_sub_weekday(self, obj):
        return obj.sub.get_weekday_display()
    get_sub_weekday.short_description = '구독 요일'

    def get_estimate_date(self, obj):
        return obj.estimate_date
    get_estimate_date.short_description = '정기 배송 예정일'

    def get_user_box_identifier(self, obj):
        userbox = obj.userbox_order.last()
        return userbox.box.identifier
    get_user_box_identifier.short_description = '상품코드'

    def get_dawn(self, obj):
        return "새벽배송" if obj.is_dawn else "일반배송"
    get_dawn.short_description = '새벽 배송 여부'