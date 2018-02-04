# When user write email commands,
# Interpret/parse it then send request to IMAP

class Interpreter():
    # command in a raw form 
    raw_command = ""

    def __init__(self, inText):
        raw_command = inText

        