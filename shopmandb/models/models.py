from django.db import models
from django.utils.translation import gettext_lazy as _
from .core import *
import datetime

# Create your models here.

class Box(TimeStampedModel):
    identifier = models.CharField(_("박스 ID"), max_length=100, unique=True)
    name = models.CharField(_("박스명"), max_length=100)
    image = models.FileField(_("이미지"), null=True, blank=True, upload_to="box")
    price = models.PositiveIntegerField(_("가격"), default=0)
    description = models.CharField(_("설명"), max_length=1000, null=True, blank=True)
    content = models.CharField(_("내용"), max_length=10000, null=True, blank=True)
    tooltip = models.CharField(_("툴팁"), max_length=1000, null=True, blank=True)

    def __str__(self):
        return f"{self.name}-{self.price}"


class Subscription(TimeStampedModel):
    RANGE_CHOICES = (
        ("0", _("1주에 1번")), 
        ("1", _("2주에 1번")), 
        ("2", _("3주에 1번")), 
        ("3", _("4주에 1번")), 
    )

    DAY_CHOICES = (
        ("0", _("화")), 
        ("1", _("수")), 
        ("2", _("목")), 
        ("3", _("금")), 
        ("4", _("토")), 
    )
    ACTIVE_CHOICES = (
        ("0", _("정상결제중")), 
        ("1", _("잠시 멈춤")), 
        ("2", _("해지")), 
    )
    
    identifier = models.CharField(_("구독 ID"), max_length=100, unique=True, blank=True)
    shipping_range = models.CharField(_("배송 주기"), choices=RANGE_CHOICES, max_length=100)
    weekday = models.CharField(_("요일"), choices=DAY_CHOICES, max_length=100)
    expected_day = models.DateField(_("결제 예정일"), null=True, blank=True)
    user_id = models.CharField(_("사용자 id"), max_length=1000, null=True)
    box = models.ForeignKey(Box, on_delete=models.SET_NULL, verbose_name="box id", null=True)
    card = models.TextField(_("결제 정보"), null=True)
    recipient_name = models.CharField(_("수령인"), max_length=100, blank=True)
    recipient_phone = models.CharField(_("수령인 전화번호"), max_length=100, blank=True)
    shipping_name = models.CharField(_("배송지명"), max_length=100, null=True, blank=True)
    post_number = models.CharField(_("우편 번호"), max_length=100, blank=True)
    address = models.CharField(_("주소"), max_length=100, blank=True)
    address_detail = models.CharField(_("상세주소"), max_length=100, blank=True)
    entrance_password = models.CharField(_("현관비밀번호"), max_length=1000, null=True, blank=True)
    survey_id = models.CharField(_("설문조사 id"), max_length=100, blank=True)
    request = models.CharField(_("요청사항"), max_length=1000, null=True, blank=True)
    is_active = models.CharField(_("구독 활성화 여부"), choices=ACTIVE_CHOICES, max_length=100)

    def __str__(self):
        return f"{self.identifier}-{self.box.price}"


class Product(TimeStampedModel):
    identifier = models.CharField(_("상품번호"), max_length=100, unique=True, blank=True)
    name = models.CharField(_("상품명"), max_length=10000)
    if_id = models.CharField(_("과일 코드"), max_length=100)
    image_storage = models.CharField(_("이미지 위치"), max_length=10000, null=True, blank=True)
    image_path = models.CharField(_("이미지 경로"), max_length=10000, null=True, blank=True)
    price = models.PositiveIntegerField(_("가격"), default=0)
    weight = models.CharField(_("중량"), max_length=100, default=0)
    description = models.CharField(_("설명"), max_length=1000, null=True, blank=True)
    content = models.TextField(_("상세정보"))
    maker = models.CharField(_("제조사"), max_length=100, null=True, blank=True)
    origin = models.CharField(_("원산지"), max_length=100)
    min_order_count = models.PositiveIntegerField(_("최소 주문 수량"), default=0)
    max_order_count = models.PositiveIntegerField(_("최대 주문 수량"), default=100)
    is_discount = models.BooleanField(_("할인 여부"), default=False)
    is_direct = models.BooleanField(_("직송 여부"), default=False)
    discount_fee = models.PositiveIntegerField(_("할인 가격"), default=0)
    discount_fee_condition = models.CharField(_("할인 기준"), max_length=100, null=True, blank=True)
    order_amount = models.PositiveIntegerField(_("판매량"), default=0, null=True, blank=True)
    hit_count = models.PositiveIntegerField(_("조회수"), default=0, null=True, blank=True)
    option = models.TextField(_("옵션"), null=True, blank=True)
    is_active = models.BooleanField(_("사용 여부"), default=True)
    is_tax_free = models.BooleanField(_("비과세 여부"), default=False)

    def __str__(self):
        return f"{self.identifier}-{self.name}"
    

class Order(TimeStampedModel):
    PATMENT_CHOICES = (
        ("0", _("신용카드")), 
        ("1", _("토스")), 
        ("2", _("카카오페이")),
    )
    STATUS_CHOICES = (
        ("0", _("상품준비중")), 
        ("1", _("배송 준비중")), 
        ("2", _("배송중")), 
        ("3", _("배송완료")),
        ("4", _("환불접수")),
        ("5", _("환불완료")),
        ("6", _("교환접수")),
        ("7", _("교환완료")),
        ("8", _("주문취소")),
        ("20", _("주문접수")),
    )

    MILEAGE_STATUS_CHOICES = (
        ('0', _('적립예정')),
        ('1', _('적립완료')),
        ('2', _('미적립')),
        ('3', _('환급예정')),
        ('4', _('환급완료')),
    )

    identifier = models.CharField(_("주문번호"),null=True, blank=True, max_length=100, unique=True)
    user_id = models.CharField(_("사용자 id"), max_length=1000)
    orderer_name = models.CharField(_("주문자"), max_length=200, blank=True)
    orderer_phone = models.CharField(_("주문자 전화번호"), max_length=100, null=True, blank=True)
    recipient_name = models.CharField(_("수령인"), max_length=200, blank=True)
    recipient_phone = models.CharField(_("수령인 전화번호"), max_length=100)
    shipping_name = models.CharField(_("배송지명"), max_length=100, null=True, blank=True)
    post_number = models.CharField(_("우편 번호"), max_length=100)
    address = models.CharField(_("주소"), max_length=200)
    address_detail = models.CharField(_("상세주소"), max_length=200)
    shipping_fee = models.PositiveIntegerField(_("배송비"), default=3000)
    option = models.CharField(_("옵션"), max_length=200, null=True, blank=True)
    option_price = models.PositiveIntegerField(_("옵션 추가비용"), default=0)
    price = models.PositiveIntegerField(_("가격"), default=0)
    amount = models.PositiveIntegerField(_("수량"), default=1)
    mileage = models.PositiveIntegerField(_("마일리지"), default=0)
    deposit = models.PositiveIntegerField(_("예치금"), default=0)
    final_price = models.PositiveIntegerField(_("최종금액"), default=0)
    payment_type = models.CharField(_("결제 방법"), choices=PATMENT_CHOICES, max_length=100)
    is_paid = models.BooleanField(_("결제여부"), default=False)
    status = models.CharField(_("상태"), choices=STATUS_CHOICES, max_length=100)
    cancel_reason = models.CharField(_("취소사유"), max_length=1000, null=True, blank=True)
    is_dawn = models.BooleanField(_("새벽 배송 여부"), default=False)
    dtime = models.DateField(_("삭제 일자"), null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, verbose_name="product id", null=True, blank=True)
    request = models.CharField(_("요청사항"), max_length=1000, null=True, blank=True)
    shipping_place = models.CharField(_("배송 업체명"), max_length=200, null=True, blank=True)
    invoice_number = models.CharField(_("송장번호"), max_length=200, null=True, blank=True)
    invoice_company = models.CharField(_("송장업체"), max_length=200, null=True, blank=True)
    estimate_date = models.DateField(_("배송 예정일"), null=True, blank=True)
    complete_date = models.DateField(_("배송 완료일"), null=True, blank=True)
    entrance_password = models.CharField(_("현관비밀번호"), max_length=1000, null=True, blank=True)
    channel = models.CharField(_("채널"), max_length=100, default="궁합과일")
    card = models.TextField(_("결제 정보"), null=True)
    sub = models.ForeignKey(Subscription, null=True, blank=True, on_delete=models.SET_NULL)
    mileage_status = models.CharField(choices=MILEAGE_STATUS_CHOICES, default="0", max_length=15)
    is_test = models.BooleanField(_('체험분 여부'), default=False)
    comment = models.TextField(_("관리자 코멘트"), null=True, blank=True)

    def __str__(self):
        return f"[Order]:{self.identifier}"

    def get_product_name(self):
        return self.product.name
    get_product_name.short_description = 'product name'


class UserBox(TimeStampedModel):
    identifier = models.CharField(_("사용자 박스 ID"), max_length=100, unique=True, blank=True)
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, verbose_name="subscription id", null=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, verbose_name="order id", null=True, related_name="userbox_order")
    box = models.ForeignKey(Box, on_delete=models.SET_NULL, verbose_name="box id", null=True)
    user_id = models.CharField(_("사용자 ID"), max_length=1000)
    is_selected = models.BooleanField(_("선택 여부"), default=False)
    value = models.TextField(_("추천과일"), blank=True)
    target = models.CharField(_("기준 박스 ID"), max_length=100, blank=True)
    survey_names = models.TextField(_("조합 박스 사람"), default="'[]'")


class OrderOption(models.Model):
    identifier = models.CharField(_("주문 옵션 id"), max_length=100, unique=True, blank=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, verbose_name="order id", null=True)
    value = models.CharField(_("값"), max_length=1000, blank=True)


class Payment(TimeStampedModel):
    identifier = models.CharField(_("결제 ID"), max_length=100, unique=True, blank=True)
    price = models.PositiveIntegerField(_("금액"), default=0)


class PaymentLog(TimeStampedModel):
    receipt_id = models.CharField(_("결제등록코드"), max_length=1000, null=True, blank=True)
    card_no = models.CharField(_("카드번호"), max_length=1000, null=True, blank=True)
    card_code = models.CharField(_("카드코드"), max_length=1000, null=True, blank=True)
    card_name = models.CharField(_("카드이름"), max_length=1000, null=True, blank=True)
    item_name = models.CharField(_("상품명"), max_length=1000, null=True, blank=True)
    pg_order_id = models.CharField(_("주문번호"), max_length=1000, null=True, blank=True)
    url = models.CharField(_("url"), max_length=1000, null=True, blank=True)
    payment_name = models.CharField(_("결제명"), max_length=1000, null=True, blank=True)
    pg_name = models.CharField(_("pg명"), max_length=1000, null=True, blank=True)
    pg = models.CharField(_("pg사"), max_length=1000, null=True, blank=True)
    method = models.CharField(_("방법"), max_length=1000, null=True, blank=True)
    method_name = models.CharField(_("방법"), max_length=1000, null=True, blank=True)
    requested_at = models.CharField(_("요청시간"), max_length=1000, null=True, blank=True)
    purchased_at = models.CharField(_("결제시간"), max_length=1000, null=True, blank=True)
    price = models.PositiveIntegerField(_("금액"), default=0)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="fruits order id")
    user_id = models.CharField(_("사용자 ID"), max_length=1000, blank=True)


class Log(TimeStampedModel):
    url = models.CharField(_("요청 주소"), max_length=10000, null=True, blank=True)
    method = models.CharField(_("전송 방식"), max_length=100, null=True, blank=True)
    request_code = models.CharField(_("호출 코드"), max_length=100000, null=True, blank=True)
    response_code = models.CharField(_("응답 코드"), max_length=100000, null=True, blank=True)
    message = models.TextField(_("메시지"), blank=True)
    user_id = models.CharField(_("사용자 ID"), max_length=1000)


class AgentLog(TimeStampedModel):
    user_id = models.CharField(_("사용자 ID"), max_length=1000, blank=True)
    subscription = models.ForeignKey(Subscription, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(_("상태"), max_length=100, null=True, blank=True)
    message = models.CharField(_("메시지"), max_length=1000, null=True, blank=True)


class Shipping(TimeStampedModel):
    old_post = models.CharField(_(""), max_length=1000, null=True, blank=True)
    new_post = models.CharField(_(""), max_length=1000, null=True, blank=True)
    si_goon_goo = models.CharField(_(""), max_length=1000, null=True, blank=True)
    dong = models.CharField(_(""), max_length=1000, null=True, blank=True)
    li = models.CharField(_(""), max_length=1000, null=True, blank=True)
    airport_fee = models.PositiveIntegerField(_(""), null=True, blank=True)
    ship_fee = models.PositiveIntegerField(_(""), null=True, blank=True)
    cycle = models.CharField(_(""), max_length=1000, null=True, blank=True)


class Setting(SingletonModel):
    original_product = models.TextField(_("원물"), blank=True)
    excel_file = models.FileField(blank=True)
    version = models.CharField(max_length=100)
    is_excel = models.BooleanField(default=True)

class OrderEmailLog(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, verbose_name="order id", null=True)
    status = models.CharField(_("상태"), max_length=100, null=True, blank=True)
    message = models.TextField(_("메시지"), blank=True)


class ShoppingCart(TimeStampedModel):
    user_id = models.CharField(_("사용자 id"), unique=True, max_length=100)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, verbose_name="product id", null=True, blank=True)
    amount = models.PositiveIntegerField(_("상품 수량"))


class MileageLog(TimeStampedModel):
    user_id = models.CharField(_("사용자 ID"), max_length=1000)
    mileage = models.PositiveIntegerField(_("마일리지"))
    status = models.CharField(_("상태"), max_length=100000, null=True, blank=True)
    message = models.TextField(_("메모"), blank=True)