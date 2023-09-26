import re

term_pattern = r'202\d{3}'
assignment_pattern = r'[A-Z]{4}\d+(?:\.\d+)*'
course_pattern = r'[A-Z]{4}(?:[1-9][0-9]{2}|100)'
weight_pattern = r'\(\d{1,3}%\)'


def find_first_match(pattern, text):
    """
    Finds the first occurrence of a pattern in a given text.

    Args:
        pattern (str): The regular expression pattern to search for.
        text (str): The input text.

    Returns:
        str or None: The first match found in the text, or None if no match is found.
    """
    match = re.search(pattern, text)
    if match:
        return match.group()
    else:
        return None
    
    
    
