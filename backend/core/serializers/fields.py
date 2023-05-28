from rest_framework import serializers


class IdRelatedField(serializers.SlugRelatedField):
    def to_internal_value(self, data):
        return data

    # TBA validate that the ID exists


class TextEnumField(serializers.ChoiceField):
    def to_representation(self, obj):
        if obj == "" and self.allow_blank:
            return obj
        return self._choices[obj].lower()

    def to_internal_value(self, data):
        # To support inserts with the value
        if data == "" and self.allow_blank:
            return ""

        for key, val in self._choices.items():
            if val.lower() == data:
                return key
        self.fail("invalid_choice", input=data)
