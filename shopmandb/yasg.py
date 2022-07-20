from django.conf.urls import url
from django.urls import path, include
from drf_yasg.views import get_schema_view
from rest_framework.permissions import AllowAny, IsAuthenticated, BasePermission
from drf_yasg import openapi

schema_url_patterns = [
	path('/', include('shopmandb.urls')),
] 

schema_view = get_schema_view(
    openapi.Info(
        title='과일궁합 Shopman API',
        default_version='v1.0',
        description=
        '''
        과일궁합 Shopman API 문서 페이지입니다.
        API 통신을 하기 위해서는 SSO에서 발급되는
        token, refreshtoken을 Authosize에 등록 후 사용해야 합니다.
        일부 api는 유동적인 데이터가 많아 파라미터를 등록하지 않았습니다.
        ''',
        terms_of_service="https://d-if.kr/"
    ),
    validators=['flex'],
    public=True,
    permission_classes=(AllowAny,),
    patterns=schema_url_patterns,
)