from flask import Flask, render_template, request, jsonify, redirect, abort
import pandas as pd
import regex as re
from datetime import date, timedelta
import math
from werkzeug.exceptions import default_exceptions, HTTPException

from helpers import whatsapp_parser, get_messages_df, get_timespan, get_totals, get_emoji_list, get_most_active_day, allowed_file

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyse", methods=["GET", "POST"])
def analyse():
    if request.method == "POST":
        
        
        # check if the post request has the file part
        if 'textFile' not in request.files:
            print('No file part')
            return abort(400, description="No file part")
        
        text_file = request.files['textFile']
        
        # if user does not select file, browser also
        # submit an empty part without filename
        if text_file.filename == '':
            print('No selected file')
            return abort(400, description="No selected file")

        # If text_file exists and if file is a .txt
        if text_file and allowed_file(text_file.filename):
            
            messages = whatsapp_parser(text_file)

            if not messages:
                print("Invalid file")
                return abort(400, description="Invalid file format")

            df = get_messages_df(messages)

            authors = df["author"].unique().tolist()

            # Get the color scheme for each author
            default_colors_list = ["rgba(70, 35, 122, 0.5)", "rgba(61, 220, 151, 0.5)", 
                                "rbga(255, 73, 92, 0,5)", "rgba(242, 208, 169,0.5)", 
                                "rgba(153, 193, 185, 0.5)"]
            author_colors = {}
            n = 0
            for author in authors:
                author_colors[author] = default_colors_list[n]
                n += 1

            # Get the total days of chat, total messages, total words, total letters
            totals = get_totals(df)

            # Start and end date of chat
            timespan = get_timespan(df)
            
            # Get the timespan labels for the timeline chart
            timespan_labels = [(timespan["startDate"] + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((totals["totalDays"] + 1))]
            
            # format the datetime object of the timespan data into strings
            timespan["startDate"] = timespan["startDate"].strftime("%Y-%m-%d")
            timespan["endDate"] = timespan["endDate"].strftime("%Y-%m-%d")

            # Get the averages 
            averages = {"wordsPerMessage": round(sum(totals["totalWords"].values()) / sum(totals["totalMessages"].values()), 2),
                        "lettersPerWord": round(sum(totals["totalLetters"].values()) / sum(totals["totalWords"].values()), 2),
                        "messagesPerDay": round(sum(totals["totalMessages"].values()) / totals["totalDays"], 2)}

            # Create dataframes grouped by different time periods
            groupby_date_df = df.groupby(["author", df["datetime"].dt.date])["message_count"].count().unstack().transpose().fillna(0).reset_index()
            groupby_dof_df = df.groupby(["author", df["datetime"].dt.day_name()])["message_count"].count().unstack().transpose().fillna(0).reset_index()
            groupby_hour_df = df.groupby(["author", df["datetime"].dt.hour])["message_count"].count().unstack().transpose().fillna(0)

            # Sort the days of week groupby dataframe by the correct order of days of week
            dof = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            groupby_dof_df["datetime"] = pd.Categorical(groupby_dof_df["datetime"], categories=dof, ordered=True)
            groupby_dof_df = groupby_dof_df.sort_values("datetime")

            # Remove the column names after transposing the dataframes 
            groupby_date_df.columns.name = groupby_dof_df.columns.name =  groupby_hour_df.columns.name = None


            # List of words to be ignored in the final charts
            ignored_words = [""]

            # Split the data into individual words
            word_df = df.loc[:, ["author", "body"]]
            word_tokenized = word_df["body"].str.lower().str.split().apply(lambda x: [re.sub("[^a-zA-Z]", "", i) for i in x])
            word_df["body"] = word_tokenized
            word_df = word_df.explode("body")

            # Get the count for each word
            word_freq_df = word_df.groupby(["author"])["body"].value_counts().unstack().transpose()
            word_freq_df.columns.name = word_freq_df.index.name = None

            # Get the variables for IDF
            total_word_count = word_freq_df.sum()
            number_of_users = len(word_freq_df.columns)

            # Calculate TF_IDF for most relevant words
            term_freq_df = word_freq_df.apply(lambda term_raw_count: term_raw_count / total_word_count[term_raw_count.name])
            inverse_document_freq_df = word_freq_df.apply(lambda x: x.notna()).sum(axis=1).apply(lambda x: math.log(number_of_users/x))
            tfidf_df = term_freq_df.mul(inverse_document_freq_df, axis=0)
            most_relevant_words = {}


            # Get the top 50 words excluding the ignored words    
            # top_words_df = word_freq_df.drop(index=ignored_words)
            top_words_df = word_freq_df.fillna(0)
            top_words_df["total"] = word_freq_df.sum(axis=1)
            top_words_df = top_words_df.sort_values(by=["total"], ascending=False).iloc[:50, :-1]

            # Split the data into individual emojis 
            top_emojis_df = df.loc[:, ["author", "body"]]
            top_emojis_df["body"] = top_emojis_df["body"].apply(lambda x: get_emoji_list(x))
            top_emojis_df = top_emojis_df.explode("body")

            # Get the count for each emoji
            top_emojis_df = top_emojis_df.groupby(["author"])["body"].value_counts().unstack().transpose().fillna(0)
            top_emojis_df.columns.name = top_emojis_df.index.name = None

            # See if the chat has emojis or no
            no_emojis = top_emojis_df.empty 

            # If it has, continue with the calculation
            if no_emojis != True:
                # Get the top 15 emojis
                top_emojis_df["total"] = top_emojis_df.sum(axis=1)
                top_emojis_df = top_emojis_df.sort_values(by=["total"], ascending=False).iloc[:15, :-1]



            # Datasets for the charts
            timeline_datasets = []
            week_activity_datasets = []
            day_activity_datasets = []
            top_words_datasets = []
            top_emojis_datasets = []

            for author in authors:
                # Get the timeline data for each author for the timeline dataset
                timeline_df = groupby_date_df.loc[:, ["datetime", author]]
                timeline_df.columns = ["t", "y"]
                timeline_df["t"] = timeline_df["t"].apply(lambda x: x.strftime("%Y-%m-%d"))
                timeline_data = timeline_df.to_dict(orient="records")
                timeline_datasets.append({"label": author, "data": timeline_data, "backgroundColor": author_colors[author]})

                # Get the weekly activity data for each author for the weekly acivity dataset
                week_activity_data = groupby_dof_df[author].tolist()
                week_activity_datasets.append({"label": author, "data": week_activity_data, "backgroundColor": author_colors[author]})

                # Get the hourly activity data for each author for the hourly acivity dataset
                day_activity_data = groupby_hour_df[author].tolist()
                day_activity_datasets.append({"label": author, "data": day_activity_data, "backgroundColor": author_colors[author]})

                # Get the top 50 words data for each author for the top words dataset
                top_words_data = top_words_df[author].tolist()
                top_words_datasets.append({"label": author, "data": top_words_data, "backgroundColor": author_colors[author]})
                
                if no_emojis != True:
                    # Get the top 50 words data for each author for the top words dataset
                    top_emojis_data = top_emojis_df[author].tolist()
                    top_emojis_datasets.append({"label": author, "data": top_emojis_data, "backgroundColor": author_colors[author], "showLine": False, "radius": 8, "hoverRadius": 9})

                # Get the most 5 relevant words for each author
                most_relevant_words[author] = tfidf_df.sort_values(by=author, ascending=False).iloc[:8].index.values.tolist()

            if no_emojis == True:
                top_emojis_datasets = None

            # Return all the data in a JSON format
            return jsonify({
                "authors": authors,
                "timespan": timespan,
                "totals" : totals,
                "averages": averages,
                "timelineChartData": {
                    "labels": timespan_labels,
                    "datasets": timeline_datasets
                },
                "messagesComparisonChartData": {
                    "datasets": [{"data": list(totals["totalMessages"].values()), "backgroundColor": list(author_colors.values())}], 
                    "labels": list(totals["totalMessages"].keys())
                },
                "wordsComparisonChartData": {
                    "datasets": [{"data": list(totals["totalWords"].values()), "backgroundColor": list(author_colors.values())}], 
                    "labels": list(totals["totalWords"].keys())
                },
                "weekActivityChartData": {
                    "labels": ["M", "T", "W", "T", "F", "S", "S"],
                    "datasets": week_activity_datasets
                },
                "dayActivityChartData": {
                    "labels": list(range(24)),
                    "datasets": day_activity_datasets
                },
                "topWordsChartData": {
                    "labels": top_words_df.index.values.tolist(),
                    "datasets": top_words_datasets
                },
                "topEmojisChartData": {
                    "labels": top_emojis_df.index.values.tolist(),
                    "datasets": top_emojis_datasets
                },
                "mostRelevantWords": most_relevant_words,
                "mostActiveDay": get_most_active_day(df)
            })
        return redirect("/")

    return redirect("/")

# Handles errors
@app.errorhandler(HTTPException)
def errorhandler(e):
    return jsonify(error=str(e.description)), 400

# https://github.com/pallets/flask/pull/2314
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)