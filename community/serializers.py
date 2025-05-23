from core.models import CustomUser as User

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from rest_framework.fields import HiddenField, CurrentUserDefault

from community.models import ForumPost, Comment, Challenge, Leaderboard, UserProfile



class ForumPostSerializer(serializers.ModelSerializer):
    """
    Serializer for the ForumPost model representing a forum discussion post.
    """
    title = serializers.CharField(allow_blank=True, trim_whitespace=False)

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



class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Comment model representing a comment on a forum post.
    """
    content = serializers.CharField(allow_blank=True, trim_whitespace=False)
    
    class Meta:
        model = Comment
        fields = ('id', 'user', 'post', 'content', 'created_at', 'is_active')
        read_only_fields = ('id', 'created_at', 'user')
    
    def validate_content(self, value):
        """
        Ensure the comment's content is not empty or composed solely of whitespace.
        """
        if not value.strip():
            raise serializers.ValidationError("Comment content cannot be empty.")
        return value

    def create(self, validated_data):
        """
        Create and return a new Comment instance.
        
        If the serializer context contains a 'request' object and the user is not provided,
        automatically assign the current user to the comment.
        """
        request = self.context.get('request')
        if request and not validated_data.get('user'):
            validated_data['user'] = request.user
        return super().create(validated_data)



class ChallengeSerializer(serializers.ModelSerializer):
    """
    Serializer for the Challenge model where users can compete with each other.
    """
    # Allow participants to be provided as a list of primary keys, but make it optional.
    participants = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        required=False
    )
    
    class Meta:
        model = Challenge
        fields = (
            'id', 'name', 'description', 'start_date', 'end_date',
            'participants', 'created_at', 'is_active'
        )
        read_only_fields = ('id', 'created_at',)
    
    def validate(self, data):
        """
        Ensure that the end_date is after the start_date.
        """
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError("End date cannot be earlier than start date.")
        return data

    def create(self, validated_data):
        """
        Create a new Challenge instance and set the many-to-many participants if provided.
        """
        participants = validated_data.pop('participants', [])
        challenge = Challenge.objects.create(**validated_data)
        if participants:
            challenge.participants.set(participants)
        return challenge

    def update(self, instance, validated_data):
        """
        Update an existing Challenge instance. Handles updating of the many-to-many field separately.
        """
        participants = validated_data.pop('participants', None)
        
        # Update simple fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update the participants if provided
        if participants is not None:
            instance.participants.set(participants)
        return instance



class LeaderboardSerializer(serializers.ModelSerializer):
    """
    Serializer for the Leaderboard model, which stores scores associated with a user's participation
    in a challenge.
    """
    user = HiddenField(default=CurrentUserDefault())

    class Meta:
        model = Leaderboard
        fields = ('id', 'challenge', 'user', 'score')
        read_only_fields = ('id',)
        validators = [
            UniqueTogetherValidator(
                queryset=Leaderboard.objects.all(),
                fields=['challenge', 'user'],
                message="Each user can have only one leaderboard entry per challenge."
            )
        ]

    def validate_score(self, value):
        """
        Validate that the score is a positive integer.
        """
        if value <= 0:
            raise serializers.ValidationError("Score must be a positive integer.")
        return value

    def create(self, validated_data):
        """
        Create a new Leaderboard entry.

        If the serializer context contains a request and the user is not provided in the input,
        automatically assign the request.user to the leaderboard entry.
        """
        request = self.context.get('request')
        
        # Ensure the user is assigned if not provided
        if 'user' not in validated_data:
            if request and request.user:
                validated_data['user'] = request.user
            else:
                raise serializers.ValidationError({'user': 'User is required but was not provided.'})

        return super().create(validated_data)
    
    def to_representation(self, instance):
        """
        Add 'user' to the serialized output even though it's read-only.
        """
        representation = super().to_representation(instance)
        representation['user'] = instance.user.username  # Add user field to the output
        return representation



class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the UserProfile model that stores additional information about a user.
    """
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False)

    class Meta:
        model = UserProfile
        fields = ('id', 'user', 'bio', 'profile_picture', 'social_links', 'created_at')
        read_only_fields = ('id', 'user', 'created_at')

    def create(self, validated_data):
        """
        Create a new UserProfile instance.
        
        If a request is provided in the serializer context and the user is not explicitly provided,
        automatically assign the request's user to the profile.
        """
        request = self.context.get('request')
        if request and not validated_data.get('user'):
            validated_data['user'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Update an existing UserProfile instance.
        
        Allows updating bio, profile_picture, and social_links.
        """
        instance.bio = validated_data.get('bio', instance.bio)
        instance.profile_picture = validated_data.get('profile_picture', instance.profile_picture)
        instance.social_links = validated_data.get('social_links', instance.social_links)
        instance.save()
        return instance

    # Custom validation for social_links field
    def validate_social_links(self, value):
        """
        Ensure that the social_links field is a dictionary.
        """
        if not isinstance(value, dict):
            raise serializers.ValidationError("Social links must be a dictionary.")
        return value
