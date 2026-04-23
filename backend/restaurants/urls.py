from rest_framework.routers import DefaultRouter
from .views import RestaurantViewSet, CategoryViewSet, MenuItemViewSet

router = DefaultRouter()
router.register('restaurants', RestaurantViewSet)
router.register('categories', CategoryViewSet)
router.register('menu-items', MenuItemViewSet)

urlpatterns = router.urls