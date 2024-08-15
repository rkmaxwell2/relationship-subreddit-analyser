from pydantic import BaseModel
from typing import List, Optional
from praw.models import Submission, Redditor, Comment
from datetime import datetime


class Case(BaseModel):
    id: Optional[int] = None
    original_title: str
    author: Redditor
    original_submission: Optional[Submission] = None
    update_submission: Optional[Submission] = None

    class Config:
        arbitrary_types_allowed = True

class SampleRow(BaseModel):
    case_id: int
    original_id: str
    update_id: str
    original_title: str
    update_title: str
    author_username: str
    original_text: str
    update_text: str
    original_num_comments: int
    update_num_comments: int
    original_votes: int
    update_votes: int
    original_upvote_ratio: float
    update_upvote_ratio: float
    orignal_author_response_ratio: float
    update_author_response_ratio: float
    original_url: str
    update_url: str

    class Config:
        arbitrary_types_allowed = True

class CommentMetric(BaseModel):
    OP: str
    comment: Comment
    OP_response_ratio: float

    class Config:
        arbitrary_types_allowed = True

class Reply(BaseModel):
    id: str
    reply_username: str | None
    posted: str
    text: str
    replies: list['Reply']

    class Config:
        arbitrary_types_allowed = True

class CommentRow(BaseModel):
    id: str
    comment_author: str | None
    num_replies: int
    votes: int
    OP_response_ratio: float
    posted: str
    text: str
    replies: List[Reply]
    

    class Config:
        arbitrary_types_allowed = True


class FinalDisplay(BaseModel):
    case_id: int
    submission_title: str
    submission_author: str
    original_url: str
    original_posted: str
    original_num_comments: int
    original_votes: int
    original_upvote_ratio: float
    orignal_author_response_ratio: float
    original_text: str
    original_comments_most_engaged: List[CommentRow]
    original_comments_highest_voted: List[CommentRow]
    update_title: str
    update_url: str
    update_posted: str
    update_num_comments: int
    update_votes: int
    update_upvote_ratio: float
    update_author_response_ratio: float
    update_text: str
    update_comments_most_engaged: List[CommentRow]
    update_comments_highest_voted: List[CommentRow]

    class Config:
        arbitrary_types_allowed = True

