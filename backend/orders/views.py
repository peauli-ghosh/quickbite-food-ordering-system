from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Order
from .serializers import OrderSerializer, OrderStatusSerializer


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

        # ---------- PERMISSIONS ----------

        # Restaurant owner actions
        if new_status in ["accepted", "rejected", "preparing"]:
            if order.restaurant.owner != user:
                return Response(
                    {"error": "Only restaurant owner can perform this action"},
                    status=status.HTTP_403_FORBIDDEN
                )

        # Delivered (future: rider)
        if new_status == "delivered":
            if order.restaurant.owner != user:  # replace later with rider check
                return Response(
                    {"error": "Only delivery agent can mark delivered"},
                    status=status.HTTP_403_FORBIDDEN
                )

        # Cancel
        if new_status == "cancelled":
            if user != order.user and user != order.restaurant.owner:
                return Response(
                    {"error": "Not allowed to cancel"},
                    status=status.HTTP_403_FORBIDDEN
                )

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