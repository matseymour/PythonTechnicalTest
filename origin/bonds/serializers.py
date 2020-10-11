from rest_framework import serializers

from bonds.lib import GleifClient
from bonds.models import Bond


class BondSerializer(serializers.ModelSerializer):

    class Meta:
        model = Bond
        fields = ('isin', 'size', 'currency', 'maturity', 'lei', 'legal_name',)
        read_only_fields = ('legal_name',)

    def create(self, validated_data):
        legal_name = GleifClient().getLegalName(validated_data['lei'])
        return Bond.objects.create(
            owner=self.context["request"].user, legal_name=legal_name, **validated_data
        )
