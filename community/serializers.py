from rest_framework import serializers

from community.models import ForumPost



class ForumPostSerializer(serializers.ModelSerializer):
    """
    Serializer for the ForumPost model representing a forum discussion post.
    """
    class Meta:
        model = ForumPost
        fields = ('id', 'user', 'title', 'content', 'created_at', 'updated_at', 'is_active')
        read_only_fields = ('id', 'created_at', 'updated_at', 'user')

    def validate_title(self, value):
        """
        Validate that the title is not blank or composed solely of whitespace.
        """
        if not value.strip():
            raise serializers.ValidationError("Title cannot be blank.")
        return value

    def create(self, validated_data):
        """
        Create a new ForumPost instance.
        
        If a request is provided in the context and the user is not already set,
        automatically assigns the request.user to the post.
        """
        request = self.context.get('request')
        if request and not validated_data.get('user'):
            validated_data['user'] = request.user
        return super().create(validated_data)
