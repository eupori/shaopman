from shopmandb.models import *
import datetime

def get_default_context(request):
    context={}
    today = datetime.datetime.today()
    subs = Subscription.objects.filter(expected_day=today.date(), is_active="0")
    sub_count = subs.count()

    orders = Order.objects.exclude(sub=None).filter(created_at__date=today.date(), is_test=False)
    order_count = orders.count()

    context["sub_count"] = sub_count
    context["order_count"] = order_count
    context["orders"] = orders
    context["subs"] = subs
    return context