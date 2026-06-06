from django.urls import re_path
from apps.leilao import consumers

websocket_urlpatterns = [
    re_path(r"ws/leilao/(?P<evento_id>[^/]+)/$", consumers.LeilaoConsumer.as_asgi()),
    re_path(r"ws/telao/(?P<evento_id>[^/]+)/$", consumers.TelaoConsumer.as_asgi()),
]
