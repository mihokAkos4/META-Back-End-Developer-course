from rest_framework import generics
from django.shortcuts import get_object_or_404
from django.http import HttpResponseBadRequest, JsonResponse
from .models import MenuItem, Cart, Order, OrderItem, Category
from .serializers import  MenuItemSerializer, ManagerListSerializer, CartSerializer, OrderSerializer, CartAddSerializer, CartRemoveSerializer, SingleOrderSerializer, OrderPutSerializer, CategorySerializer
from .paginations import MenuItemListPagination
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth.models import User, Group
from .permissions import IsManager, IsDeliveryCrew
from datetime import date

# View for listing and creating menu items
class MenuItemListView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]  # Rate limiting for users
    queryset = MenuItem.objects.all()  # Fetch all menu items
    serializer_class = MenuItemSerializer  # Serializer for MenuItem model
    search_fields = ['title', 'category__title']  # Fields to allow search
    ordering_fields = ['price', 'category']  # Fields to allow ordering
    pagination_class = MenuItemListPagination  # Pagination for menu items

    def get_permissions(self):
        # Define permissions based on request method
        if self.request.method == 'GET':
            permission_classes = []  # No authentication required for GET
        else:
            permission_classes = [IsAuthenticated, IsAdminUser]  # Auth required for other methods
        return [permission() for permission in permission_classes]

# View for managing categories
class CategoryView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = CategorySerializer
    queryset = Category.objects.all()  # Fetch all categories
    permission_classes = [IsAdminUser]  # Only admins can access

# View for retrieving, updating, or deleting a specific menu item
class MenuItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_permissions(self):
        # Define permissions based on request method
        permission_classes = [IsAuthenticated]
        if self.request.method == 'PATCH':
            permission_classes = [IsAuthenticated, IsManager | IsAdminUser]
        if self.request.method == "DELETE":
            permission_classes = [IsAuthenticated, IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def patch(self, request, *args, **kwargs):
        # Toggle 'featured' status for a menu item
        menuitem = MenuItem.objects.get(pk=self.kwargs['pk'])
        menuitem.featured = not menuitem.featured
        menuitem.save()
        return JsonResponse(status=200, data={'message': f'Featured status of {menuitem.title} changed to {menuitem.featured}'})

# View for listing and adding managers
class ManagersListView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = User.objects.filter(groups__name='Managers')  # Users in 'Managers' group
    serializer_class = ManagerListSerializer
    permission_classes = [IsAuthenticated, IsManager | IsAdminUser]

    def post(self, request, *args, **kwargs):
        # Add user to 'Managers' group
        username = request.data['username']
        if username:
            user = get_object_or_404(User, username=username)
            managers = Group.objects.get(name='Managers')
            managers.user_set.add(user)
            return JsonResponse(status=201, data={'message': 'User added to Managers group'})

# View for removing managers
class ManagersRemoveView(generics.DestroyAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = ManagerListSerializer
    permission_classes = [IsAuthenticated, IsManager | IsAdminUser]
    queryset = User.objects.filter(groups__name='Managers')

    def delete(self, request, *args, **kwargs):
        # Remove user from 'Managers' group
        pk = self.kwargs['pk']
        user = get_object_or_404(User, pk=pk)
        managers = Group.objects.get(name='Managers')
        managers.user_set.remove(user)
        return JsonResponse(status=200, data={'message': 'User removed from Managers group'})

# View for managing the Delivery Crew group
class DeliveryCrewListView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    queryset = User.objects.filter(groups__name='Delivery crew')  # Users in 'Delivery crew' group
    serializer_class = ManagerListSerializer
    permission_classes = [IsAuthenticated, IsManager | IsAdminUser]

    def post(self, request, *args, **kwargs):
        # Add user to 'Delivery Crew' group
        username = request.data['username']
        if username:
            user = get_object_or_404(User, username=username)
            crew = Group.objects.get(name='Delivery crew')
            crew.user_set.add(user)
            return JsonResponse(status=201, data={'message': 'User added to Delivery Crew group'})

class DeliveryCrewRemoveView(generics.DestroyAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = ManagerListSerializer
    permission_classes = [IsAuthenticated, IsManager | IsAdminUser]
    queryset = User.objects.filter(groups__name='Delivery crew')

    def delete(self, request, *args, **kwargs):
        # Remove user from 'Delivery Crew' group
        pk = self.kwargs['pk']
        user = get_object_or_404(User, pk=pk)
        managers = Group.objects.get(name='Delivery crew')
        managers.user_set.remove(user)
        return JsonResponse(status=201, data={'message': 'User removed from the Delivery crew group'})

# View for handling cart operations
class CartOperationsView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self, *args, **kwargs):
        # Fetch the user's cart items
        return Cart.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        # Add item to cart
        serialized_item = CartAddSerializer(data=request.data)
        serialized_item.is_valid(raise_exception=True)
        id = request.data['menuitem']
        quantity = request.data['quantity']
        item = get_object_or_404(MenuItem, id=id)
        price = int(quantity) * item.price
        try:
            Cart.objects.create(user=request.user, quantity=quantity, unit_price=item.price, price=price, menuitem_id=id)
        except:
            return JsonResponse(status=409, data={'message': 'Item already in cart'})
        return JsonResponse(status=201, data={'message': 'Item added to cart!'})

    def delete(self, request, *args, **kwargs):
        # Remove item(s) from cart
        if request.data['menuitem']:
            serialized_item = CartRemoveSerializer(data=request.data)
            serialized_item.is_valid(raise_exception=True)
            menuitem = request.data['menuitem']
            cart = get_object_or_404(Cart, user=request.user, menuitem=menuitem)
            cart.delete()
            return JsonResponse(status=200, data={'message': 'Item removed from cart'})
        else:
            Cart.objects.filter(user=request.user).delete()
            return JsonResponse(status=201, data={'message': 'All items removed from cart'})

# View for handling order operations
class OrderOperationsView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = OrderSerializer

    def get_queryset(self, *args, **kwargs):
        # Fetch orders based on user roles
        if self.request.user.groups.filter(name='Managers').exists() or self.request.user.is_superuser:
            return Order.objects.all()
        elif self.request.user.groups.filter(name='Delivery crew').exists():
            return Order.objects.filter(delivery_crew=self.request.user)
        else:
            return Order.objects.filter(user=self.request.user)

    def get_permissions(self):
        # Permissions for GET and POST requests
        permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def post(self, request, *args, **kwargs):
        # Place an order from the cart
        cart = Cart.objects.filter(user=request.user)
        x = cart.values_list()
        if not x:
            return HttpResponseBadRequest()
        total = sum([float(item[-1]) for item in x])
        order = Order.objects.create(user=request.user, status=False, total=total, date=date.today())
        for item in cart.values():
            menuitem = get_object_or_404(MenuItem, id=item['menuitem_id'])
            OrderItem.objects.create(order=order, menuitem=menuitem, quantity=item['quantity'])
        cart.delete()
        return JsonResponse(status=201, data={'message': f'Your order has been placed! Your order number is {order.id}'})

# View for handling individual order operations
class SingleOrderView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    serializer_class = SingleOrderSerializer

    def get_permissions(self):
        # Permissions for individual order actions
        order = Order.objects.get(pk=self.kwargs['pk'])
        if self.request.user == order.user and self.request.method == 'GET':
            permission_classes = [IsAuthenticated]
        elif self.request.method in ['PUT', 'DELETE']:
            permission_classes = [IsAuthenticated, IsManager | IsAdminUser]
        else:
            permission_classes = [IsAuthenticated, IsDeliveryCrew | IsManager | IsAdminUser]
        return [permission() for permission in permission_classes]

    def get_queryset(self, *args, **kwargs):
        # Fetch order items for a specific order
        return OrderItem.objects.filter(order_id=self.kwargs['pk'])

    def patch(self, request, *args, **kwargs):
        # Toggle order status
        order = Order.objects.get(pk=self.kwargs['pk'])
        order.status = not order.status
        order.save()
        return JsonResponse(status=200, data={'message': f'Status of order #{order.id} changed to {order.status}'})

    def put(self, request, *args, **kwargs):
        # Assign a delivery crew to the order
        serialized_item = OrderPutSerializer(data=request.data)
        serialized_item.is_valid(raise_exception=True)
        order_pk = self.kwargs['pk']
        crew_pk = request.data['delivery_crew']
        order = get_object_or_404(Order, pk=order_pk)
        crew = get_object_or_404(User, pk=crew_pk)
        order.delivery_crew = crew
        order.save()
        return JsonResponse(status=201, data={'message': f'{crew.username} was assigned to order #{order.id}'})

    def delete(self, request, *args, **kwargs):
        # Delete an order
        order = Order.objects.get(pk=self.kwargs['pk'])
        order_number = order.id
        order.delete()
        return JsonResponse(status=200, data={'message': f'Order #{order_number} was deleted'})
