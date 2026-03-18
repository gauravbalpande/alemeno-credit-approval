from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from customers.serializers import CustomerSerializer, RegisterCustomerSerializer


class RegisterCustomerView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = RegisterCustomerSerializer(data=request.data)
        if serializer.is_valid():
            customer = serializer.save()
            output = CustomerSerializer(customer).data
            return Response(output, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

