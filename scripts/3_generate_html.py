from model import CommentRow, Reply, FinalDisplay
from datetime import datetime
import pandas as pd
import json
from typing import List
from jinja2 import Template
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

sample_name = "sample_20240614_155000"

def load_template(template_file: str) -> str:
    """
    Load the template file into a string.

    Args:
        template_file (str): The path to the template file.

    Returns:
        str: The content of the template file.
    """
    logging.info(f"Loading template from file: {template_file}")
    with open(template_file, 'r') as file:
        return file.read()

def save_html(output: str, output_file: str) -> None:
    """
    Save the HTML output to a file.

    Args:
        output (str): The HTML content to save.
        output_file (str): The path to the file where HTML content will be saved.
    """
    logging.info(f"Saving HTML output to file: {output_file}")
    with open(output_file, 'w') as file:
        file.write(output)

def render_comment(comment: CommentRow) -> str:
    """
    Render a comment into HTML using a Jinja2 template.

    Args:
        comment (CommentRow): The comment object to render.

    Returns:
        str: The rendered HTML string for the comment.
    """
    comment_template = """
    <div class="comment">
        <p class="author">{{ comment.comment_author }}</p>
        <p class="posted">{{ comment.posted }}</p>
        <p><pre>{{ comment.text }}</pre></p>
        <p>Upvotes: {{ comment.votes }} | Replies: {{ comment.num_replies }} | Author Response Ratio: {{ comment.OP_response_ratio }}</p>
        {% for reply in comment.replies %}
            {{ render_reply(reply) }}
        {% endfor %}
    </div>
    """
    template = Template(comment_template)
    template.globals['render_reply'] = render_reply
    return template.render(comment=comment)

def render_reply(reply: Reply) -> str:
    """
    Render a reply into HTML using a Jinja2 template.

    Args:
        reply (Reply): The reply object to render.

    Returns:
        str: The rendered HTML string for the reply.
    """
    reply_template = """
    <div class="reply">
        <p class="author">{{ reply.reply_username }}</p>
        <p class="posted">{{ reply.posted }}</p>
        <p><pre>{{ reply.text }}</pre></p>
        {% for reply in reply.replies %}
            {{ render_reply(reply) }}
        {% endfor %}
    </div>
    """
    template = Template(reply_template)
    template.globals['render_reply'] = render_reply
    return template.render(reply=reply)

def sort_comments_by_posted_time(comments: List[CommentRow]) -> List[CommentRow]:
    """
    Sort a list of comments by their posted time.

    Args:
        comments (List[CommentRow]): The list of comments to sort.

    Returns:
        List[CommentRow]: The sorted list of comments.
    """
    logging.info("Sorting comments by posted time")
    sorted_comments = sorted(comments, key=lambda x: datetime.strptime(x.posted, "%Y-%m-%d %H:%M:%S UTC"))
    return sorted_comments

def anonimise_reply(reply: Reply, commenters: dict, counter: int):
    """
    Anonymise a reply and its nested replies.

    Args:
        reply (Reply): The reply to anonymise.
        commenters (dict): Dictionary mapping original usernames to anonymised usernames.
        counter (int): Counter for generating anonymised usernames.

    Returns:
        (Reply, dict, int): The anonymised reply, updated commenters dictionary, and updated counter.
    """
    logging.debug(f"Anonimising reply from username: {reply.reply_username}")
    if reply.reply_username in commenters:
        reply.reply_username = commenters[reply.reply_username]
    else:
        commenters[reply.reply_username] = f"commenter_{counter}"
        reply.reply_username = f"commenter_{counter}"
        counter += 1
    
    for reply in reply.replies:
        reply, commenters, counter = anonimise_reply(reply, commenters, counter)
    
    return reply, commenters, counter

def anonimise_comment(comment: CommentRow, commenters: dict, counter: int):
    """
    Anonymise a comment and its nested replies.

    Args:
        comment (CommentRow): The comment to anonymise.
        commenters (dict): Dictionary mapping original usernames to anonymised usernames.
        counter (int): Counter for generating anonymised usernames.

    Returns:
        (CommentRow, dict, int): The anonymised comment, updated commenters dictionary, and updated counter.
    """
    logging.debug(f"Anonimising comment from author: {comment.comment_author}")
    if comment.comment_author in commenters:
        comment.comment_author = commenters[comment.comment_author]
    else:
        commenters[comment.comment_author] = f"commenter_{counter}"
        comment.comment_author = f"commenter_{counter}"
        counter += 1
    
    for reply in comment.replies:
        reply, commenters, counter = anonimise_reply(reply, commenters, counter)

    return comment, commenters, counter

def parse_comments(comments_raw: List[dict]) -> List[CommentRow]:
    """
    Convert a list of raw comment dictionaries into a list of CommentRow objects.

    Args:
        comments_raw (List[dict]): The raw comment data.

    Returns:
        List[CommentRow]: The list of CommentRow objects.
    """
    logging.info("Parsing raw comments")
    comments = []
    for cmt in comments_raw:
        comment = CommentRow(**cmt)
        comments.append(comment)
    return comments

def anonimise_comments(comments: List[CommentRow], counter: int, commenters: dict):
    """
    Anonymise a list of comments.

    Args:
        comments (List[CommentRow]): The list of comments to anonymise.
        counter (int): Counter for generating anonymised usernames.
        commenters (dict): Dictionary mapping original usernames to anonymised usernames.

    Returns:
        (List[CommentRow], int, dict): The anonymised list of comments, updated counter, and updated commenters dictionary.
    """
    logging.info("Anonimising comments")
    anon_comments = []
    for cmt in comments:
        anonimised_comment, commenters, counter = anonimise_comment(cmt, commenters, counter)
        anon_comments.append(anonimised_comment)

    return anon_comments, counter, commenters

def parse_case(sample_name: str, comment_file: str) -> None:
    """
    Parse a case from a JSON file, anonymise comments, and generate HTML output.

    Args:
        sample_name (str): The name of the sample.
        comment_file (str): The path to the JSON file containing case data.
    """
    logging.info(f"Parsing case from file: {comment_file}")
    with open(comment_file) as f:
        data = json.load(f)
    sample: List[FinalDisplay] = [FinalDisplay(**item) for item in data]
    case = pd.DataFrame([row.dict() for row in sample]).iloc[0]

    author = case["submission_author"]
    anonimised_author = f"author_{case['case_id']}"
    case["submission_author"] = anonimised_author

    commenters = {author: anonimised_author}
    counter = 1

    original_comments_engaged = parse_comments(case["original_comments_most_engaged"])
    original_comments_highest_voted = parse_comments(case["original_comments_highest_voted"])
    update_comments_engaged = parse_comments(case["update_comments_most_engaged"])
    update_comments_highest_voted = parse_comments(case["update_comments_highest_voted"])

    anon_original_comments_engaged, counter, commenters = anonimise_comments(sort_comments_by_posted_time(original_comments_engaged), counter, commenters)
    anon_original_comments_highest_voted, counter, commenters = anonimise_comments(sort_comments_by_posted_time(original_comments_highest_voted), counter, commenters)
    anon_update_comments_engaged, counter, commenters = anonimise_comments(sort_comments_by_posted_time(update_comments_engaged), counter, commenters)
    anon_update_comments_highest_voted, counter, commenters = anonimise_comments(sort_comments_by_posted_time(update_comments_highest_voted), counter, commenters)

    template = Template(load_template("reddit_api/template.html"))
    template.globals['render_comment'] = render_comment
    template.globals['render_reply'] = render_reply

    html_output = template.render(
        case_id=case["case_id"],
        submission_title=case["submission_title"],
        submission_author=case["submission_author"],
        original_posted=case["original_posted"],
        original_votes=case["original_votes"],
        original_upvote_ratio=case["original_upvote_ratio"],
        original_num_comments=case["original_num_comments"],
        orignal_author_response_ratio=case["orignal_author_response_ratio"],
        original_text=case["original_text"],
        original_comments_engaged=anon_original_comments_engaged,
        original_comments_top=anon_original_comments_highest_voted,
        update_posted=case["update_posted"],
        update_votes=case["update_votes"],
        update_upvote_ratio=case["update_upvote_ratio"],
        update_num_comments=case["update_num_comments"],
        update_author_response_ratio=case["update_author_response_ratio"],
        update_text=case["update_text"],
        update_comments_engaged=anon_update_comments_engaged,
        update_comments_top=anon_update_comments_highest_voted
    )
    output_file = f"data/html/{sample_name}/case_{case['case_id']}.html"
    save_html(html_output, output_file)

def main() -> None:
    """
    Main function to process all files in the data folder and generate HTML outputs.
    """
    data_folder = f"data/comment_trees/{sample_name}.json"
    logging.info(f"Processing files in folder: {data_folder}")
    for filename in os.listdir(data_folder):
        file_path = os.path.join(data_folder, filename)
        if os.path.isfile(file_path):
            logging.info(f"Generating HTML for file: {filename}")
            parse_case(sample_name, file_path)

if __name__ == "__main__":
    main()
