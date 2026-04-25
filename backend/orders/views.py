from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Order
from .serializers import OrderSerializer, OrderStatusSerializer
from users.models import User


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "update_status":
            return OrderStatusSerializer
        return OrderSerializer

    # ---------- VIEW ORDER DETAILS ----------
    @action(detail=True, methods=['get'])
    def details(self, request, pk=None):
        order = self.get_object()
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    # ---------- UPDATE STATUS ----------
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        user = request.user

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data["status"]

        allowed_transitions = {
            "pending": ["accepted", "cancelled", "rejected"],
            "accepted": ["preparing", "cancelled"],
            "preparing": ["out_for_delivery", "cancelled"],
            "out_for_delivery": ["delivered"],
        }

        # ---------- VALIDATE TRANSITION ----------
        if new_status not in allowed_transitions.get(order.status, []):
            return Response(
                {"error": f"Cannot change from {order.status} to {new_status}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ---------- ROLE-BASED PERMISSIONS ----------

        # OWNER
        if user.role == "owner":
            if order.restaurant.owner != user:
                return Response({"error": "Not your restaurant"}, status=403)

            if new_status not in ["accepted", "rejected", "preparing", "out_for_delivery"]:
                return Response({"error": "Owner cannot perform this action"}, status=403)

            # Assign rider automatically when out for delivery
            if new_status == "out_for_delivery":
                rider = User.objects.filter(role="rider").first()
                if not rider:
                    return Response({"error": "No rider available"}, status=400)
                order.rider = rider

        # RIDER
        elif user.role == "rider":
            if order.rider != user:
                return Response({"error": "Not your delivery"}, status=403)

            if new_status != "delivered":
                return Response({"error": "Rider can only mark delivered"}, status=403)

        # CUSTOMER
        elif user.role == "customer":
            if order.user != user:
                return Response({"error": "Not your order"}, status=403)

            if new_status != "cancelled":
                return Response({"error": "Customer can only cancel"}, status=403)

        else:
            return Response({"error": "Invalid role"}, status=403)

        # ---------- UPDATE ----------
        old_status = order.status
        order.status = new_status
        order.save()

        return Response({
            "message": "Status updated successfully",
            "order_id": order.id,
            "old_status": old_status,
            "new_status": order.status
        })