from django.contrib import admin
from django.urls import path, include
from .views import (
    CarbonIntensityApiView,
    EnergySourcesApiView,
    CarbonIntensityHistoryApiView,
    EnergySourcesHistoryApiView,
    CarbonIntensityForecastsApiView,
    CarbonIntensityForecastsHistoryApiView,
    EnergySourcesForecastsHistoryApiView,
    SupportedRegionsApiView,
    SignUpAPIView,
    SignInAPIView
)

urlpatterns = [
    path('CarbonIntensity', CarbonIntensityApiView.as_view()),
    path('EnergySources', EnergySourcesApiView.as_view()),
    path('CarbonIntensityHistory', CarbonIntensityHistoryApiView.as_view()),
    path('EnergySourcesHistory', EnergySourcesHistoryApiView.as_view()),
    path('CarbonIntensityForecasts', CarbonIntensityForecastsApiView.as_view()),
    path('CarbonIntensityForecastsHistory', CarbonIntensityForecastsHistoryApiView.as_view()),
    path('EnergySourcesForecastsHistory', EnergySourcesForecastsHistoryApiView.as_view()),   
    path('SupportedRegions', SupportedRegionsApiView.as_view()),
    path('SignUp', SignUpAPIView.as_view()),
    path('SignIn', SignInAPIView.as_view()),
]
