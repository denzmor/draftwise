import os

USER_DATA_DIR = "./data/users"

def get_user_file_path(username, file_name):
    """
    Generate a file path for the given user's file.
    :param username: The logged-in username
    :param file_name: "exclusion.txt" or "must_include.txt"
    :return: Full file path as a string
    """
    user_dir = os.path.join(USER_DATA_DIR, username)
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, file_name)

