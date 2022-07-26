# Generated by Django 3.1.1 on 2021-01-28 17:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Box',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('identifier', models.CharField(max_length=20, unique=True, verbose_name='박스 ID')),
                ('name', models.CharField(max_length=20, verbose_name='박스명')),
                ('image', models.CharField(blank=True, max_length=20, null=True, verbose_name='이미지')),
                ('price', models.PositiveIntegerField(default=0, verbose_name='가격')),
                ('description', models.CharField(blank=True, max_length=100, null=True, verbose_name='설명')),
                ('content', models.CharField(blank=True, max_length=20, null=True, verbose_name='내용')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Log',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('request_code', models.CharField(blank=True, max_length=20, null=True, verbose_name='호출 코드')),
                ('response_code', models.CharField(blank=True, max_length=20, null=True, verbose_name='응답 코드')),
                ('user_id', models.CharField(max_length=20, verbose_name='사용자 ID')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Option',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('index', models.PositiveIntegerField(default=0)),
                ('add_price', models.PositiveIntegerField(default=0)),
                ('is_selected', models.BooleanField(default=False, verbose_name='선택 여부')),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('identifier', models.CharField(max_length=20, unique=True, verbose_name='결제 ID')),
                ('price', models.PositiveIntegerField(default=0, verbose_name='금액')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('identifier', models.CharField(max_length=20, unique=True, verbose_name='구독 ID')),
                ('shipping', models.CharField(blank=True, max_length=20, null=True, verbose_name='배송지')),
                ('shipping_range', models.CharField(choices=[('one_week', '1주에 1번'), ('two_week', '2주에 1번'), ('three_week', '3주에 1번'), ('four_week', '4주에 1번')], max_length=50, verbose_name='배송 주기')),
                ('weekday', models.CharField(choices=[('tue', '화'), ('wed', '수'), ('thur', '목'), ('fri', '금'), ('sat', '토')], max_length=10, verbose_name='요일')),
                ('box', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shopmandb.box', verbose_name='box_id')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='UserBox',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('identifier', models.CharField(max_length=20, unique=True, verbose_name='사용자 박스 ID')),
                ('user_id', models.CharField(max_length=20, verbose_name='사용자 ID')),
                ('is_selected', models.BooleanField(default=False, verbose_name='선택 여부')),
                ('box', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shopmandb.box', verbose_name='box_id')),
                ('subscription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shopmandb.subscription', verbose_name='sub_id')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('identifier', models.CharField(max_length=20, unique=True, verbose_name='상품번호')),
                ('name', models.CharField(max_length=20, verbose_name='상품명')),
                ('if_id', models.CharField(max_length=10, verbose_name='과일 코드')),
                ('image_storage', models.CharField(blank=True, max_length=20, null=True, verbose_name='이미지 위치')),
                ('image_path', models.CharField(blank=True, max_length=20, null=True, verbose_name='이미지 경로')),
                ('price', models.PositiveIntegerField(default=0, verbose_name='가격')),
                ('weight', models.CharField(default=0, max_length=20, verbose_name='중량')),
                ('description', models.CharField(blank=True, max_length=100, null=True, verbose_name='설명')),
                ('content', models.CharField(max_length=20, verbose_name='상세정보')),
                ('maker', models.CharField(blank=True, max_length=20, null=True, verbose_name='제조사')),
                ('origin', models.CharField(max_length=20, verbose_name='원산지')),
                ('min_order_count', models.PositiveIntegerField(default=0, verbose_name='최소 주문 수량')),
                ('max_order_count', models.PositiveIntegerField(default=100, verbose_name='최대 주문 수량')),
                ('is_discount', models.BooleanField(default=False, verbose_name='할인 여부')),
                ('discount_fee', models.PositiveIntegerField(default=0, verbose_name='할인 가격')),
                ('discout_fee_contition', models.CharField(blank=True, max_length=20, null=True, verbose_name='할인 기준')),
                ('use_option', models.BooleanField(default=False, verbose_name='옵션 사용 여부')),
                ('order_amount', models.PositiveIntegerField(blank=True, default=0, null=True, verbose_name='판매량')),
                ('hit_count', models.PositiveIntegerField(blank=True, default=0, null=True, verbose_name='조회수')),
                ('option', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shopmandb.option', verbose_name='option_id')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('identifier', models.CharField(max_length=20, unique=True, verbose_name='주문번호')),
                ('user_id', models.CharField(max_length=10, verbose_name='사용자 id')),
                ('recipient_name', models.CharField(blank=True, max_length=50, verbose_name='수령인')),
                ('recipient_phone', models.CharField(max_length=50, verbose_name='수령인 전화번호')),
                ('shipping_name', models.CharField(blank=True, max_length=50, null=True, verbose_name='배송지명')),
                ('post_number', models.CharField(max_length=10, verbose_name='우편번호')),
                ('address', models.CharField(max_length=50, verbose_name='주소')),
                ('address_detail', models.CharField(max_length=50, verbose_name='상세주소')),
                ('shipping_fee', models.PositiveIntegerField(default=3000, verbose_name='배송비')),
                ('option1', models.CharField(blank=True, max_length=20, null=True, verbose_name='옵션1')),
                ('option2', models.CharField(blank=True, max_length=20, null=True, verbose_name='옵션2')),
                ('option3', models.CharField(blank=True, max_length=20, null=True, verbose_name='옵션3')),
                ('option4', models.CharField(blank=True, max_length=20, null=True, verbose_name='옵션4')),
                ('price', models.PositiveIntegerField(default=0, verbose_name='가격')),
                ('amount', models.PositiveIntegerField(default=1, verbose_name='수량')),
                ('coupon', models.CharField(blank=True, max_length=20, null=True, verbose_name='쿠폰')),
                ('point', models.PositiveIntegerField(default=0, verbose_name='포인트')),
                ('deposit', models.PositiveIntegerField(default=0, verbose_name='예치금')),
                ('payment_type', models.CharField(choices=[('credit_card', '신용카드'), ('toss', '토스'), ('kakao', '카카오페이')], max_length=50, verbose_name='결제 방법')),
                ('final_price', models.PositiveIntegerField(default=0, verbose_name='최종금액')),
                ('is_paid', models.BooleanField(default=False, verbose_name='결제여부')),
                ('status', models.CharField(choices=[('ordered', '주문완료'), ('shipping', '배송중'), ('shipping_complete', '배송완료'), ('refund_receipt', '환불접수'), ('refund_complete', '환불완료'), ('exchange_receipt', '교환접수'), ('exchange_complete', '교환완료')], max_length=50, verbose_name='상태')),
                ('is_down', models.BooleanField(default=False, verbose_name='새벽 배송 여부')),
                ('dtime', models.DateField(blank=True, null=True, verbose_name='삭제 일자')),
                ('request', models.CharField(blank=True, max_length=100, null=True, verbose_name='요청사항')),
                ('shipping_place', models.CharField(blank=True, max_length=30, null=True, verbose_name='배송 업체명')),
                ('invoice_number', models.CharField(blank=True, max_length=30, null=True, verbose_name='송장번호')),
                ('estimate_date', models.DateField(blank=True, null=True, verbose_name='배송 예정일')),
                ('complete_date', models.DateField(blank=True, null=True, verbose_name='배송 완료일')),
                ('product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='shopmandb.product', verbose_name='product_id')),
                ('subscription', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='shopmandb.subscription', verbose_name='subscription_id')),
                ('user_box', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='shopmandb.userbox', verbose_name='user_box_id')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AgentLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(blank=True, max_length=20, null=True, verbose_name='상태')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shopmandb.userbox', verbose_name='order_id')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
