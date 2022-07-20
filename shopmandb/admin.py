from django.contrib import admin
from shopmandb.models import *
from django.utils.translation import gettext_lazy as _

from rangefilter.filters import DateRangeFilter, DateTimeRangeFilter
import pandas as pd
import json
# Register your models here.
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

class PaymentLogAdmin(admin.ModelAdmin):
	model = PaymentLog
	list_display = [
		"item_name",
		"purchased_at",
        "user_id",
        "method",
        "order"
	]


class AgentLogAdmin(admin.ModelAdmin):
    change_list_template='change_list_form.html'
    model = AgentLog


class MileageLogAdmin(admin.ModelAdmin):
	model = MileageLog
	list_display = [
		"user_id", "mileage", "status", "message",
	]


class OrderAdmin(admin.ModelAdmin):
    model = Order
    list_display = [
        'identifier', 'user_id', 'status',  'price', 
        'final_price', 'get_coupon', 
        'amount', 'product', 'sub', 
        'is_test', 'created_at', 'updated_at', 
    ]
    list_filter = (
                'status',
                'payment_type',
                CouponIsUsedFilter,
                TesterFilter,
                ('created_at', DateRangeFilter), ('updated_at', DateTimeRangeFilter),
            )
    search_fields = ('identifier', 'recipient_name', 'address',)

    def get_coupon(self, obj):
        if obj.product:
            if obj.product.identifier == "P00000ZN" and obj.final_price == 0:
                return True
        
        return False
    get_coupon.boolean = True    
    get_coupon.short_description = '쿠폰 사용 여부'


class BoxAdmin(admin.ModelAdmin):
    model = Box
    list_display = [
        'identifier', 'name', 'price',  'tooltip', 'created_at', 
    ]
    list_filter = ('price',)
    search_fields = ('identifier', 'name', 'price',)


class SubscriptionAdmin(admin.ModelAdmin):
    model = Subscription
    list_display = [
        'identifier', 'user_id', 'recipient_name', 'box', 
        'is_active', 'request', 'expected_day', 'created_at', 
    ]
    list_filter = ('is_active', 'box',)
    search_fields = ('identifier', 'user_id', 'is_active', 'expected_day', 'box',)


class ProductAdmin(admin.ModelAdmin):
    model = Product
    list_display = [
        'identifier', 'name', 'if_id', 'price', 
        'weight', 'origin', 'is_discount', 'order_amount', 'created_at', 'is_active'
    ]
    list_filter = ('if_id','is_active',)
    search_fields = ('identifier', 'name', 'if_id', 'price', 'is_discount', 'created_at', 'is_active',)


class UserBoxAdmin(admin.ModelAdmin):
    model = UserBox
    list_display = [
        'identifier', 'subscription', 'order', 'box', 
        'user_id', 'is_selected', 'target', 'created_at'
    ]
    list_filter = ('is_selected', 'target', 'created_at',)
    search_fields = ('identifier', 'user_id', 'is_selected', 'target', 'created_at',)

class LogAdmin(admin.ModelAdmin):
    model = Log
    list_display = [
        'id', 'url', 'method', 'user_id', 'response_code', 'created_at'
    ]
    list_filter = ('response_code', 'url', 'method')
    search_fields = ('response_code', 'id', 'url', 'method', 'user_id', 'created_at',)


class SettingAdmin(admin.ModelAdmin):
    model = Setting
    # list_display = (
    #     "title",
    #     "view_type",
    #     "is_active",
    # )
    readonly_fields = ["original_product"]

    def save_model(self, request, obj, form, change):
        df = pd.read_excel(obj.excel_file, engine='openpyxl')
        print(df.columns)
        # hp = pd.read_csv(obj.hp, index_col=0)
        # print(fm.index)
        # print(fm.shape, mt.shape, hp.shape)
        res_df = {}
        for ind, row in df.iterrows():
            tmp = {
                "name": row['name'],
                'if_id':row['if_id'],
                "price":row['price'],
                "unit":1,
                "step":row['step'],
                "min_unit":row['min_weight'],
                "per_price":row['price']/row['step'],
                "item_code": row['item_code'] if 'item_code' in row else "tmp"
            }
            if row['if_id'] not in res_df:
                res_df[row['if_id']] = [tmp]
            else:
                res_df[row['if_id']].append(tmp)
        obj.original_product = json.dumps(res_df)
        super().save_model(request, obj, form, change)



admin.site.register(Box,BoxAdmin)
admin.site.register(Subscription,SubscriptionAdmin)
admin.site.register(Product,ProductAdmin)
admin.site.register(Order,OrderAdmin)
admin.site.register(UserBox,UserBoxAdmin)
admin.site.register(Payment)
admin.site.register(PaymentLog,PaymentLogAdmin)
admin.site.register(Log,LogAdmin)
admin.site.register(AgentLog,AgentLogAdmin)
admin.site.register(Setting, SettingAdmin)
admin.site.register(OrderEmailLog)
admin.site.register(MileageLog, MileageLogAdmin)
