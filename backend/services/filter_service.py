import openai
import os
from typing import Tuple
from dotenv import load_dotenv

load_dotenv()


class ContentFilter:
    """
    Content filter using OpenAI's Moderation API to detect inappropriate content.
    """

    def __init__(self):
        # Set up OpenAI API key
        openai.api_key = os.getenv('OPENAI_API_KEY')

        if not openai.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        # Polite responses for filtered content
        self.polite_responses = [
            "I'm here to help you find great books! Please keep our conversation friendly and respectful. What kind of book are you looking for?",
            "Let's keep our chat positive! I'd love to recommend some amazing books. What genres or themes interest you?",
            "I'm designed to help with book recommendations in a friendly environment. What type of story are you in the mood for?",
            "I prefer to keep our conversation respectful. How about we talk about books instead? What's your favorite genre?",
            "Let's focus on finding you some great reading material! What kind of books do you usually enjoy?"
        ]

    def contains_inappropriate_content(self, text: str) -> bool:
        """
        Check if text contains inappropriate content using OpenAI's Moderation API.

        Args:
            text (str): Text to check

        Returns:
            bool: True if inappropriate content is found
        """
        try:
            # Call OpenAI Moderation API
            response = openai.moderations.create(input=text)

            # Check if content was flagged
            moderation_result = response.results[0]

            # Return True if any category is flagged
            return moderation_result.flagged

        except Exception as e:
            print(f"Error checking content moderation: {e}")
            # Fail safely - don't block content if API fails
            return False

    def get_detailed_moderation_info(self, text: str) -> dict:
        """
        Get detailed moderation information (optional, for debugging/logging).

        Args:
            text (str): Text to check

        Returns:
            dict: Detailed moderation results
        """
        try:
            response = openai.moderations.create(input=text)
            result = response.results[0]

            return {
                'flagged': result.flagged,
                'categories': result.categories.model_dump(),
                'category_scores': result.category_scores.model_dump()
            }
        except Exception as e:
            print(f"Error getting moderation details: {e}")
            return {'flagged': False, 'categories': {}, 'category_scores': {}}

    def get_polite_response(self) -> str:
        """
        Get a random polite response for inappropriate content.

        Returns:
            str: Polite response message
        """
        import random
        return random.choice(self.polite_responses)

    def filter_message(self, message: str) -> Tuple[bool, str]:
        """
        Filter a message and return whether it's appropriate and a response.

        Args:
            message (str): User message to filter

        Returns:
            Tuple[bool, str]: (is_appropriate, response_if_inappropriate)
        """
        if self.contains_inappropriate_content(message):
            return False, self.get_polite_response()
        return True, ""


# Create a global instance
content_filter = ContentFilter()