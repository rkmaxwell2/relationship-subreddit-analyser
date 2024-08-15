from praw import Reddit
from praw.models import Submission, Comment
from client.get_reddit_client import client
from model import Case, SampleRow, CommentRow, Reply, CommentMetric, FinalDisplay
from datetime import datetime, timezone
import pandas as pd
import json
from typing import List
from generate_sample import count_replies_by_user
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SAMPLE_FILE = "data/samples/sample_20240614_155000.json"

def get_comment_forest(submission: Submission) -> Comment:
    """
    Retrieve the comment forest (all comments) for a given submission.

    Args:
        submission (Submission): The submission from which to fetch comments.

    Returns:
        CommentForest: The fully expanded comment forest for the submission.
    """
    logger.info(f"Fetching comment forest for submission: {submission.id}")
    original_comment_forest = submission.comments 
    original_comment_forest.replace_more(limit=None)
    return original_comment_forest

def get_comments(submission: Submission) -> list[Comment]:
    """
    Get a list of comments from a submission, sorted by score in descending order.

    Args:
        submission (Submission): The submission from which to fetch and sort comments.

    Returns:
        list[Comment]: The sorted list of comments.
    """
    logger.info(f"Fetching and sorting comments by score for submission: {submission.id}")
    comment_forest = get_comment_forest(submission)
    comments = sorted(
        comment_forest,
        key=lambda comment: comment.score,
        reverse=True
    )
    return comments

def response_ratio(total_replies: int, total_replies_by_op: int) -> float:
    """
    Calculate the ratio of replies by the original poster (OP) to the total replies.

    Args:
        total_replies (int): The total number of replies.
        total_replies_by_op (int): The number of replies by the OP.

    Returns:
        float: The calculated response ratio.
    """
    try:
        return round(total_replies_by_op / total_replies, 3)
    except ZeroDivisionError:
        return 0.0

def get_comment_metrics(comments: list[Comment], op: str) -> list[CommentMetric]:
    """
    Generate a list of metrics for each comment, including the OP response ratio.

    Args:
        comments (list[Comment]): The list of comments to analyze.
        op (str): The username of the original poster.

    Returns:
        list[CommentMetric]: A list of CommentMetric objects sorted by response ratio.
    """
    logger.info(f"Generating comment metrics for OP: {op}")
    metrics = []
    for comment in comments:
        total_replies, total_replies_by_op = count_replies_by_user(comment.replies, op)
        metrics.append(
            CommentMetric(
                OP=op,
                comment=comment,
                OP_response_ratio=response_ratio(total_replies, total_replies_by_op)
            )
        )
    return sorted(
        [comment for comment in metrics if comment.comment.body != "[deleted]"],
        key=lambda x: x.OP_response_ratio,
        reverse=True
    )

def parse_replies(comment: Comment) -> list[Reply]:
    """
    Recursively parse replies to a comment, converting them to Reply objects.

    Args:
        comment (Comment): The comment whose replies are to be parsed.

    Returns:
        list[Reply]: A list of Reply objects representing the replies.
    """
    logger.info(f"Parsing replies for comment: {comment.id}")
    replies = comment.replies
    replies.replace_more(limit=None)
    return [
        Reply(
            id=reply.id,
            reply_username=reply.author.name if reply.author is not None else None,
            posted=datetime.fromtimestamp(reply.created_utc, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z'),
            text=reply.body,
            replies=parse_replies(reply),
        )
        for reply in replies
    ]

def get_comment_rows(case: Case, submission: Submission) -> list[CommentRow]:
    """
    Extract and categorize comments into 'most engaged' and 'highest voted' categories.

    Args:
        case (Case): The Case object containing case-related data.
        submission (Submission): The submission from which to extract comments.

    Returns:
        tuple[list[CommentRow], list[CommentRow]]: Two lists of CommentRow objects for the most engaged and highest voted comments.
    """
    logger.info(f"Extracting comments for case {case.case_id} from submission: {submission.id}")
    engaged_comments = []
    top_comments = []

    comments_with_metrics: list[CommentMetric] = get_comment_metrics(get_comments(submission), case.author_username)

    comments_with_top_score = sorted(
        [comment for comment in comments_with_metrics if comment.OP_response_ratio == 0.0], 
        key=lambda x: x.comment.score,
        reverse=True
    )[:5]  # Keep 5 highest scoring comment trees that OP hasn't interacted with

    comments_with_top_response_ratio = sorted(
        [comment for comment in comments_with_metrics if comment.OP_response_ratio != 0.0], 
        key=lambda x: x.OP_response_ratio,
        reverse=True
    )  # Keep all comment trees that OP has intereacted with
    
    for comment_metric in comments_with_top_response_ratio:
        comment = CommentRow(
            id=comment_metric.comment.id,
            comment_author=comment_metric.comment.author.name if comment_metric.comment.author is not None else None,
            num_replies=len(comment_metric.comment.replies),
            votes=comment_metric.comment.score,
            OP_response_ratio=comment_metric.OP_response_ratio,
            posted=datetime.fromtimestamp(comment_metric.comment.created_utc, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z'),
            text=comment_metric.comment.body,
            replies=parse_replies(comment_metric.comment)
        )
        engaged_comments.append(comment)

    for comment_metric in comments_with_top_score:
        comment = CommentRow(
            id=comment_metric.comment.id,
            comment_author=comment_metric.comment.author.name if comment_metric.comment.author is not None else None,
            num_replies=len(comment_metric.comment.replies),
            votes=comment_metric.comment.score,
            OP_response_ratio=comment_metric.OP_response_ratio,
            posted=datetime.fromtimestamp(comment_metric.comment.created_utc, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z'),
            text=comment_metric.comment.body,
            replies=parse_replies(comment_metric.comment)
        )
        top_comments.append(comment)
    
    return engaged_comments, top_comments

def main():
    """
    Main function to process cases and generate datasets for each case based on comments and metrics.
    """
    logger.info(f"Starting comment selection for sample file: {SAMPLE_FILE}")
    with open(SAMPLE_FILE) as f:
        data = json.load(f)
    sample: List[SampleRow] = [SampleRow(**item) for item in data]
    
    reddit: Reddit = client()
    for case in sample:
        logger.info(f"Processing Case {case.case_id}...")
        original_submission = reddit.submission(id=case.original_id)
        update_submission = reddit.submission(id=case.update_id)

        logger.info(f"Finding and categorizing comments for Case {case.case_id}...")
        original_comments_most_engaged, original_comments_highest_voted = get_comment_rows(case, original_submission)
        update_comments_most_engaged, update_comments_highest_voted = get_comment_rows(case, update_submission)

        final = [FinalDisplay(
            case_id=case.case_id,
            submission_title=case.original_title,
            submission_author=case.author_username,
            original_url=case.original_url,
            original_posted=datetime.fromtimestamp(original_submission.created_utc, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z'),
            original_num_comments=case.original_num_comments,
            original_votes=case.original_votes,
            original_upvote_ratio=case.original_upvote_ratio,
            orignal_author_response_ratio=case.orignal_author_response_ratio,
            original_text=case.original_text,
            original_comments_most_engaged=original_comments_most_engaged,
            original_comments_highest_voted=original_comments_highest_voted,
            update_title=case.update_title,
            update_url=case.update_url,
            update_posted=datetime.fromtimestamp(update_submission.created_utc, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z'),
            update_num_comments=case.update_num_comments,
            update_votes=case.update_votes,
            update_upvote_ratio=case.update_upvote_ratio,
            update_author_response_ratio=case.update_author_response_ratio,
            update_text=case.update_text,        
            update_comments_most_engaged=update_comments_most_engaged,
            update_comments_highest_voted=update_comments_highest_voted
        )]
        data = [row.dict() for row in final]
        df = pd.DataFrame(data)
        save_folder = SAMPLE_FILE.rstrip(".json")
        output_file = f'data/comment_trees/{save_folder}/case_{case.case_id}.json'
        df.to_json(output_file, orient='records')
        logger.info(f"Data saved to {output_file} for Case {case.case_id}")

if __name__ == "__main__":
    main()
