from client.client_config import client_id, client_secret, user_agent
import praw
from praw import Reddit

def client() -> Reddit:
    """
    Create and return an authenticated Reddit client instance.

    This function initializes a `praw.Reddit` object using the provided
    `client_id`, `client_secret`, and `user_agent`. These credentials
    are required to interact with the Reddit API.

    Returns:
        Reddit: An instance of the `praw.Reddit` class, configured with
        the specified client ID, client secret, and user agent.
    """
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )
    return reddit
