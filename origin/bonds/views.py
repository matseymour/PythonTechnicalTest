from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from bonds.models import Bond
from bonds.serializers import BondSerializer


class HelloWorld(APIView):
    def get(self, request):
        return Response("Hello World!")


class BondViewSet(mixins.CreateModelMixin,
                  mixins.ListModelMixin,
                  viewsets.GenericViewSet):

    queryset = Bond.objects.all()
    serializer_class = BondSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):

        queryset = super(BondViewSet, self).get_queryset().filter(owner=self.request.user)
        filters = {
            key_: value for key_, value in self.request.query_params.items()
            if key_ in ['isin', 'size', 'currency', 'maturity', 'lei', 'legal_name']
        }
        return queryset.filter(**filters)
