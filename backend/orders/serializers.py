from rest_framework import serializers
from .models import Order, OrderItem
from restaurants.models import MenuItem


class OrderItemSerializer(serializers.ModelSerializer):
    menu_item_detail = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['menu_item', 'menu_item_detail', 'quantity']

    def get_menu_item_detail(self, obj):
        return {
            "id": obj.menu_item.id,
            "name": obj.menu_item.name,
            "price": obj.menu_item.price
        }
    
class OrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[
        "accepted",
        "preparing",
        "out_for_delivery",
        "delivered",
        "cancelled",
        "rejected",
    ])


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, write_only=True)
    order_items = OrderItemSerializer(source='items', many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'restaurant', 'items', 'order_items', 'total_price', 'status']
        read_only_fields = ['total_price', 'status']

    def validate(self, data):
        restaurant = data['restaurant']
        items = data['items']

        for item in items:
            if item['menu_item'].restaurant != restaurant:
                raise serializers.ValidationError(
                    "All items must belong to the selected restaurant"
                )

        if not restaurant.is_open:
            raise serializers.ValidationError(
                "Cannot order from a closed restaurant"
            )

        return data

    def create(self, validated_data):
        items_data = validated_data.pop('items')

        order = Order.objects.create(**validated_data)

        total_price = 0

        for item_data in items_data:
            menu_item = item_data['menu_item']
            quantity = item_data['quantity']

            if quantity <= 0:
                raise serializers.ValidationError(
                    "Quantity must be greater than 0"
                )

            price = menu_item.price

            OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                quantity=quantity,
                price=price
            )

            total_price += price * quantity

        order.total_price = total_price
        order.save()

        return order