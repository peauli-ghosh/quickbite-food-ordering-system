from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from .models import Restaurant, Category, MenuItem
from .serializers import RestaurantSerializer, CategorySerializer, MenuItemSerializer


class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer