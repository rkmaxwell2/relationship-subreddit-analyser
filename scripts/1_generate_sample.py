from praw import Reddit
from praw.models import Subreddit, Submission, Comment
from datetime import datetime
from client.get_reddit_client import client
from model import SampleRow
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TITLE_CLEANUP_TERMS = ["[update]", "(update)", "update", ":"]

def get_most_commented_update_submissions(subreddit: Subreddit) -> list[Submission]:
    """
    Get the top submissions from a subreddit for the past month sorted by the number of comments,
    and filter out posts that are not updates or have no author.

    Args:
        subreddit (Subreddit): The subreddit from which to fetch submissions.

    Returns:
        list[Submission]: A list of filtered submissions sorted by comment count.
    """
    logger.info("Fetching top submissions from the past month...")
    sorted_submissions: list[Submission] = sorted(
        subreddit.top(time_filter="month"),
        key=lambda submission: submission.num_comments,
        reverse=True
    )
    filtered_submissions = [
        submission for submission in sorted_submissions
        if "update" in submission.title.lower()
        and submission.author is not None
    ]
    logger.info(f"Found {len(filtered_submissions)} submissions after filtering for updates.")
    return filtered_submissions

def get_original_title_from_update(update: Submission) -> str:
    """
    Extract the original title from an update submission by removing common update keywords.

    Args:
        update (Submission): The update submission to process.

    Returns:
        str: The cleaned original title.
    """
    original_title = update.title.lower()
    for word in TITLE_CLEANUP_TERMS:
        original_title = original_title.replace(word, "")
    original_title = ' '.join(original_title.strip().split())
    logger.info(f"Extracted original title: '{original_title}'")
    return original_title

def get_submission_from_title(subreddit: Subreddit, title: str) -> Submission:
    """
    Search for a submission in a subreddit by title.

    Args:
        subreddit (Subreddit): The subreddit in which to search.
        title (str): The title to search for.

    Returns:
        Submission: The earliest submission matching the title.
    """
    logger.info(f"Searching for submission with title: '{title}'")
    submissions = subreddit.search(title, limit=2)
    return min(submissions, key=lambda submission: submission.created_utc)

def count_replies_by_user(comments: list[Comment], username: str | None) -> tuple[int, int]:
    """
    Recursively count the total number of replies and the number of replies by a specific user.

    Args:
        comments (list[Comment]): The list of comments to process.
        username (str | None): The username to count replies for.

    Returns:
        tuple[int, int]: A tuple containing total replies and user-specific replies.
    """
    total_count = 0
    user_count = 0
    for comment in comments:
        total_count += 1
        if comment.author and comment.author.name == username:
            user_count += 1
        total_replies, user_replies = count_replies_by_user(comment.replies, username)
        total_count += total_replies
        user_count += user_replies
    return total_count, user_count

def author_response_ratio(submission: Submission) -> float:
    """
    Calculate the response ratio of the author in a submission.

    Args:
        submission (Submission): The submission to process.

    Returns:
        float: The ratio of author's comments to total comments and replies.
    """
    logger.info(f"Calculating author response ratio for submission: {submission.title}")
    submission.comments.replace_more(limit=None)
    total_comments_and_replies, author_comments_and_replies = count_replies_by_user(submission.comments.list(), submission.author.name)
    ratio = round(author_comments_and_replies / total_comments_and_replies, 3)
    logger.info(f"Author response ratio: {ratio}")
    return ratio

def main():
    """
    Main function to generate a sample dataset of original and update submissions.
    """
    logger.info("Generating sample...")
    reddit: Reddit = client()
    subreddit: Subreddit = reddit.subreddit("relationships")
    updates: list[Submission] = get_most_commented_update_submissions(subreddit)
    
    sample = []
    for id, update_submission in enumerate(updates):
        logger.info(f"\nProcessing submission {id + 1}/{len(updates)}")
        logger.info(f"Update title: {update_submission.title}")
        
        original_title = get_original_title_from_update(update_submission)
        original_submission = get_submission_from_title(subreddit, original_title)
        logger.info(f"Original title: {original_submission.title}")
        
        if original_submission is not None:
            row = SampleRow(
                case_id=id + 1,
                original_id=original_submission.id,
                update_id=update_submission.id,
                original_title=original_title,
                update_title=update_submission.title,
                author_username=update_submission.author.name,
                original_text=original_submission.selftext,
                update_text=update_submission.selftext,
                original_num_comments=original_submission.num_comments,
                update_num_comments=update_submission.num_comments,
                original_votes=original_submission.score,
                update_votes=update_submission.score,
                original_upvote_ratio=original_submission.upvote_ratio,
                update_upvote_ratio=update_submission.upvote_ratio,
                orignal_author_response_ratio=author_response_ratio(original_submission),
                update_author_response_ratio=author_response_ratio(update_submission),
                original_url=original_submission.url,
                update_url=update_submission.url
            )
            sample.append(row)
    
    data = [row.dict() for row in sample]
    df = pd.DataFrame(data)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sample/sample_{timestamp}.json"
    df.to_json(filename, orient='records')
    logger.info("Sample dataset generated and saved as 'sample.json'.")

if __name__ == "__main__":
    main()
