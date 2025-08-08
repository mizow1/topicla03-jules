def safe_print(message):
    """
    A wrapper around the print() function that handles UnicodeEncodeError
    by replacing problematic characters. This is useful for logging in
    environments with restrictive default encodings (like Windows cp932).
    """
    try:
        print(message)
    except UnicodeEncodeError:
        # Encode to UTF-8 and decode back to the default encoding, replacing errors
        safe_message = message.encode('utf-8', 'replace').decode('utf-8', 'replace')
        print(safe_message)
