from django.urls import path

from ambience.views import OrderAmbienceView

urlpatterns = [
    path("orders/<int:order_id>/ambience/", OrderAmbienceView.as_view(), name="order-ambience")
]