from django.contrib import admin
from django.urls import path, include
from main.views import (StatesView, FactoriesView, AqiPrognosticationView, AqiPrognosticationByCordsView,
                        FactoriesByCordsView)

urlpatterns = [
    path("states/", StatesView.as_view(), name="states"),
    path("factories/", FactoriesView.as_view(), name="factories"),
    path("aqi/", AqiPrognosticationView.as_view(), name="aqi"),
    path("aqi-by-cords/", AqiPrognosticationByCordsView.as_view(), name="aqi-by-coords"),
    path("factories-by-cords/", FactoriesByCordsView.as_view(), name="factories-by-coords"),
]
