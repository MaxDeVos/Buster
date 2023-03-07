from src.DatabaseCog.DatabaseCog import sanitize_input


def generate_invite_queue_db(invite_message_id, real_name="", username="", description="", inviter_user_id="",
                             timestamp="", votes_yes=None,
                             votes_no=None, votes_abstain=None):
    args = [invite_message_id, real_name, username, description, inviter_user_id, timestamp,
            votes_yes, votes_no, votes_abstain]

    sanitized_list = []
    for item in args:
        if type(item) is str:
            sanitized_list.append(sanitize_input(item))
        else:
            sanitized_list.append(item)

    return sanitized_list
