import regex as re
import pandas as pd
from datetime import date
import dateutil
import string
import emoji
import math

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == "txt"

def whatsapp_parser(textfile):
    """ Returns a list of Message objects """

    # Create empty list of messages
    messages = []

    # Regex pattern to get whatsapp event where each event is starts with a date and ends before the next date
    # or until end of file
    pat = re.compile(r'^(\d+[\/.-]\d+[\/.-]\d+.*?)(?=^\d+[\/.-]\d+[\/.-]\d+|\Z)', re.S | re.M)

    # Regex pattern to get the details of a whatsapp message
    msg_regex = r"^(?P<date>\d+[\/.-]\d+[\/.-]\d+), (?P<time>\d+:\d+(:\d+)?( (AM|PM))?) - (?P<author>.*?)(?=:): (?P<body>.*?)(?=\d+[\/.-]\d+[\/.-]\d+|\Z)"

    isFileObject = False

    try:
        rf = open(textfile)
    except TypeError:
        try:
            read_object = textfile.stream.read().decode("utf-8")
            isFileObject = True
        except Exception as e:
            print(e)
            return None
    except FileNotFoundError as e:
        print(e)
        return None
    else:
        read_object = rf.read()

    # Get an interable object of events
    events = pat.finditer(read_object)

    if not events:
        return None
    
    for event in events:
        # Delete any newline and replace with space
        row = event.group(0).strip().replace('\n', ' ')
        
        # Get the match of a message
        match = re.match(msg_regex, row)

        # If it's not an event that is not asscociated with a sender:
        if match:
            # combine date and time
            datetime = match.group('date') + " " + match.group('time')
            message = {"datetime": datetime, "author": match.group('author'), "body": match.group('body').replace('\n', ' ')}
            messages.append(message)
    
    if isFileObject:
        textfile.close()
    else: 
        rf.close()

    return messages

def get_messages_df(messages):
    # Get the pandas dataframe from the whatsapp_messages object list
    df = pd.DataFrame(messages)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df["body"] = df["body"].astype("string")

    # Get the letter count of each message (note that the lambda function return the number of letters and not characters)
    df["letter_count"] = df["body"].apply(lambda s: sum(l.isalpha() for l in s))

    #Get the number of words in a message 
    df["word_count"] = df["body"].str.split().str.len()

    # Put in a count row to make calculations easier
    df["message_count"] = 1

    return df

def get_timespan(df):
    """ Returns the start and end date of the chat """
    return {"startDate": df["datetime"].min().date(), "endDate": df["datetime"].max().date()}

def get_totals(df):
    """ Returns the totals of the following """
    total_days = (df["datetime"].max() - df["datetime"].min()).days
    if total_days == 0:
        total_days = 1
    total_messages = df["author"].value_counts().to_dict()
    total_words = df.groupby(["author"])["word_count"].sum().to_dict()
    total_letters = df.groupby(["author"])["letter_count"].sum().to_dict()

    return {"totalDays": total_days, "totalMessages": total_messages, "totalWords": total_words, "totalLetters": total_letters}
    
def get_most_active_day(df):
    """ Get the date, total messages and total words of the most active day """
    # Get the most active date (the most amount of messages in a day)
    max_date = df["datetime"].dt.date.value_counts().idxmax()
    
    # Group the counts by dates and find the counts of the most active date
    groupbyobj = df.groupby(["author", df["datetime"].dt.date])
    groupbyobj = groupbyobj.agg({"word_count": "sum", "message_count": "count"})
    groupbyobj = groupbyobj.loc[pd.IndexSlice[:, max_date], :].reset_index(level="datetime", drop=True)
    
    # Rename columns for easier access later on in JS and convert to dict    
    groupbyobj.rename(columns = {"word_count": "wordCount", "message_count": "messageCount"}, inplace = True)
    counts = groupbyobj.to_dict()
    most_active_day = {"date": max_date.strftime("%Y-%m-%d"), "messages": sum(counts["messageCount"].values()), 
    "words": sum(counts["wordCount"].values())}

    return most_active_day


def get_emoji_list(text):
    """ Returns a list of emojis from a given text """
    emoji_list = []
    
    # this regex gets all the unicode characters
    data = re.findall(r'\X', text)
    
    # if the unicode character is an emoji, then append
    for grapheme in data:
        if any(char in emoji.UNICODE_EMOJI for char in grapheme):
            emoji_list.append(grapheme)
    
    return emoji_list