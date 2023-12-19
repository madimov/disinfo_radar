from drive_functions import *
import numpy as np

df = create_dataframe_from_folder("1XQzVMy7k_mTrVSXduyaoRNmgtdGj3Bmj")
df2=df.copy()


################################counts##########################################################################
def count_rows(df):
    count = len(df)
    return pd.DataFrame({'count': [count]})

stats_folder="1XmS1IlBZ4FXHK81cks2L2J8uS884Twwv"

total = count_rows(df)
total=total.astype("str")
save_dataframe_to_drive(total, "total_twitter.xlsx" ,stats_folder)



def count_tweets_by_day(df, timestamp_col='date'):
    # Convert the timestamp column to datetime format if it's not already
    df[timestamp_col] = pd.to_datetime(df[timestamp_col])

    # Extract the date from the timestamp, format it, and then count the number of tweets per day
    daily_counts = df.groupby(df[timestamp_col].dt.strftime('%b %d')).size().reset_index(name='volume')

    # Rename columns
    daily_counts.columns = ['time', 'volume']

    return daily_counts

stats_folder="1XmS1IlBZ4FXHK81cks2L2J8uS884Twwv"

volume = count_tweets_by_day(df)
volume=volume.astype("str")
save_dataframe_to_drive(volume, "volume.xlsx" ,stats_folder)


#############################top speakers###########################################################################

def weekly_top_five_names_per_title(df):
    # Convert 'date' column to datetime
    df['date'] = pd.to_datetime(df['date'])

    # Set 'date' column as the index
    df.set_index('date', inplace=True)

    google_sheet_id = "1z8z3VOR2iOKtG_Non3TIqMo-CKm_D6EU8JJs7LSrSbI"

    for title in df["title"].unique():
        title_df = df[df["title"] == title]

        # Filter out "Media Institutions"
        title_df = title_df[title_df["title"] != "Media Institutions"]

        # Resample to get weekly counts of names
        weekly_counts = title_df.groupby('name').resample('W').size()

        # Reset index
        weekly_counts = weekly_counts.reset_index()

        # Rename columns
        weekly_counts.columns = ['name', 'week', 'count']

        # Get the top 5 names based on total counts
        top_five_names = weekly_counts.groupby('name')['count'].sum().nlargest(5).index.tolist()

        # Filter dataframe for only top five names
        weekly_counts = weekly_counts[weekly_counts['name'].isin(top_five_names)]

        # Pivot table with names as columns, date as index and counts as values
        pivot_df = weekly_counts.pivot(index='week', columns='name', values='count')

        # Fill NaN values with 0
        pivot_df.fillna(0, inplace=True)

        pivot_df = pivot_df.reset_index()

        pivot_df = pivot_df.astype("str")

        # Use the save_dataframe_in_tab function to save the dataframe to Google Sheets
        save_dataframe_in_tab(pivot_df, google_sheet_id, title)


# Assuming df is your dataframe and save_dataframe_in_tab is defined elsewhere
weekly_top_five_names_per_title(df)


#################################engagement##################################################################################################

def aggregate_and_save(df, file_name, folder_location):
    # Group by 'title' and sum the specified columns
    aggregated_df = df.groupby('title').agg({
        'likes': 'sum',
        'quotes': 'sum',
        'replies': 'sum'
    }).reset_index()

    # Calculate the total engagement for each row
    aggregated_df['TotalEngagement'] = aggregated_df['likes'] + aggregated_df['quotes'] + aggregated_df['replies']

    # Compute the percentages
    aggregated_df['Likes'] = (aggregated_df['likes'] / aggregated_df['TotalEngagement']) * 100
    aggregated_df['Quotes'] = (aggregated_df['quotes'] / aggregated_df['TotalEngagement']) * 100
    aggregated_df['Replies'] = (aggregated_df['replies'] / aggregated_df['TotalEngagement']) * 100

    # Keep only the desired columns
    aggregated_df = aggregated_df[['title', 'Likes', 'Quotes', 'Replies']]

    # Save the aggregated dataframe to drive
    save_dataframe_to_drive(aggregated_df, file_name, folder_location)

    return aggregated_df  # Return the aggregated dataframe, in case you want to inspect/use it elsewhere

# Your save_dataframe_to_drive function should be defined above this code

file_name = "engagement.xlsx"
folder_location = "1XmS1IlBZ4FXHK81cks2L2J8uS884Twwv"
aggregate_and_save(df, file_name, folder_location)



#########################themes count#######################################################


def count_themes_by_title(df):
    selection = ['Economy', 'External Relations', 'Social Groups', 'Freedom and Democracy']

    df_filtered = df[df['topic_label'].isin(selection)]

    # Group by "title" and "topic_label", count occurrences, and unstack the result
    topic_counts = df_filtered.groupby(['title', 'topic_label']).size().unstack('title', fill_value=0)

    # Calculate the total counts for each title
    total_counts = topic_counts.sum()

    # Divide each count by the total and convert to percentage
    topic_percents = topic_counts.divide(total_counts) * 100

    # Format as percentage with 0 decimal places
    topic_percents = topic_percents.applymap('{:.0f}%'.format)
    #topic_percents.to_excel("test.xlsx")
    return topic_percents.reset_index()

theme=count_themes_by_title(df)
theme=theme.astype("str")
theme_folder="1Xixi04FOd87tkKT-TX6TV248HE6JmHVH"
save_dataframe_to_drive(theme, "themes.xlsx" ,theme_folder)

####################### sentiment analysis######################################################################



def sentiment_distribution(df):
    # Convert continuous sentiment scores to categorical values
    df['sentiment'] = np.where(df['sent_code'] <= -0.02, 'Negative',
                               np.where(df['sent_code'] >= 0.02, 'Positive', 'Neutral'))

    # Group by 'title' and get the count of each sentiment category
    sentiment_counts = df.groupby('title')['sentiment'].value_counts(normalize=True).unstack().fillna(0) * 100

    # Reorder columns
    order = ['Negative', 'Neutral', 'Positive']
    sentiment_counts = sentiment_counts[order]

    # Transpose the df for desired format
    sentiment_counts = sentiment_counts.transpose()

    return sentiment_counts.reset_index()



# Get sentiment distribution
result = sentiment_distribution(df)

# Save result to Google Drive using your existing function
save_dataframe_to_drive(result, "sentiment_distribution.xlsx", "1Xmr1n5opkBp0S8oGmpykFFbCgdLhu9D8")


def sentiment_distribution_politician(df):
    # Filter the dataframe to only include rows with politician names
    names_order = [
        'Donald Tusk',
        'Mateusz Morawiecki (PM)',
        'Paweł Kukiz',
        'Sławomir Mentzen',
        'Władysław Kosiniak-Kamysz',
        'Włodzimierz Czarzasty'
    ]
    df = df[df['name'].isin(names_order)]

    # Convert continuous sentiment scores to categorical values
    df['sentiment'] = np.where(df['sent_code'] <= -0.02, 'Negative',
                               np.where(df['sent_code'] >= 0.02, 'Positive', 'Neutral'))

    # Group by 'names' and get the count of each sentiment category
    sentiment_counts = df.groupby('name')['sentiment'].value_counts(normalize=True).unstack().fillna(0) * 100

    # Reorder columns
    order = ['Negative', 'Neutral', 'Positive']
    sentiment_counts = sentiment_counts[order]

    return sentiment_counts.reset_index()


# Get sentiment distribution
result = sentiment_distribution_politician(df)

# Save result to Google Drive using your existing function
save_dataframe_to_drive(result, "sentiment_distribution_politicians.xlsx", "1Xmr1n5opkBp0S8oGmpykFFbCgdLhu9D8")


#########################################toxicity##############################################################
# def count_high_toxicity_entries(df):
#     # Filter the dataframe for entries with 'toxicity' greater than 0.7
#     filtered_df = df[df['toxicity'] > 0.7]
#
#     # Group by 'title' column and count the instances
#     toxic_counts = filtered_df.groupby('title')['toxicity'].count()
#
#     return toxic_counts.reset_index().rename(columns={"toxicity": "high_toxicity_count"})
#
# toxic_counts = count_high_toxicity_entries(df)
#
# toxic_counts = toxic_counts.astype({"title": "str", "high_toxicity_count": "int"})
# theme_folder = "1X_0AJ2imRje94euXNApXd81T0pcOho61"
# save_dataframe_to_drive(toxic_counts, "toxic.xlsx", theme_folder)
#
# import pandas as pd
#
#
# def breakdown_by_title(df):
#     # Filter out rows where emotion is 'neutral'
#     filtered_df = df[df['emotion'] != 'neutral']
#
#     # Initialize a dictionary to keep counts
#     counts = {}
#
#     # Iterate over filtered DataFrame to populate counts
#     for idx, row in filtered_df.iterrows():
#         title = row['title']
#         emotion = row['emotion']
#
#         if title not in counts:
#             counts[title] = {}
#
#         if emotion not in counts[title]:
#             counts[title][emotion] = 0
#
#         counts[title][emotion] += 1
#
#     # Convert counts to DataFrame
#     pivot_df = pd.DataFrame.from_dict(counts, orient='index').fillna(0)
#
#     # Transpose DataFrame for desired orientation
#     pivot_df = pivot_df.transpose()
#
#     # Convert counts to percentage
#     for col in pivot_df.columns:
#         pivot_df[col] = (pivot_df[col] / pivot_df[col].sum()) * 100
#
#     return pivot_df.reset_index()
#
#
#
#               # Use the function
# result_df = breakdown_by_title(df)
# emotions_folder = "1XUL-JqcBWqUHeaikcd1kuei0nt2PZzEd"
# save_dataframe_to_drive(result_df, "emotions.xlsx", emotions_folder)
#
# import pandas as pd


def process_and_upload(df, mapping_dict):
    # Extracting month name
    df['month'] = pd.to_datetime(df['date']).dt.strftime('%B')

    # List of names to be considered
    names_order = [
        'Donald Tusk',
        'Mateusz Morawiecki (PM)',
        'Paweł Kukiz',
        'Sławomir Mentzen',
        'Władysław Kosiniak-Kamysz',
        'Włodzimierz Czarzasty'
    ]

    # Rename the columns based on the mapping_dict
    df = df.rename(columns=mapping_dict)

    # Subset the DataFrame for rows with 'National Politicians' in the 'title' column and the given names
    df = df[(df['title'] == 'National Politicians') & (df['name'].isin(names_order))]

    # Create an empty dictionary to store the aggregated data for each group
    aggregated_data = {}

    # Count the number of posts for each group by month
    message_count = df.pivot_table(index='name', columns='month', aggfunc='size', fill_value=0).reset_index()

    # Ensure all names are present in the aggregated data
    all_names_df = pd.DataFrame({'name': names_order})
    message_count = all_names_df.merge(message_count, on='name', how='left').fillna(0)

    aggregated_data['message count'] = message_count

    # Calculate averages for the renamed columns and store in the aggregated_data dictionary
    for original_col, renamed_col in mapping_dict.items():
        group_data = df.pivot_table(index='name', columns='month', values=renamed_col, aggfunc='mean',
                                    fill_value=0).reset_index()

        # Ensure all names are present in the aggregated data
        group_data = all_names_df.merge(group_data, on='name', how='left').fillna(0)

        aggregated_data[renamed_col] = group_data

    # Use the previous function to upload each aggregated DataFrame to the specified Google Sheet
    spreadsheet_id = "1Rmr2oP_c65_m2B23ntFed2JoRe8rFWOUYYexFP1cS_Q"
    for tab_name, data in aggregated_data.items():
        # Convert the entire DataFrame to string format to prevent JSON errors
        data = data.astype("str")
        save_dataframe_preserve_col_A(data, spreadsheet_id, tab_name)

def process_and_upload(df, mapping_dict):
    # Extracting year and week number
    df['year_week'] = pd.to_datetime(df['date']).dt.strftime('%Y-W%U')

    # List of names to be considered
    names_order = [
        'Donald Tusk',
        'Mateusz Morawiecki (PM)',
        'Paweł Kukiz',
        'Sławomir Mentzen',
        'Władysław Kosiniak-Kamysz',
        'Włodzimierz Czarzasty'
    ]

    # Rename the columns based on the mapping_dict
    df = df.rename(columns=mapping_dict)

    # Subset the DataFrame for rows with 'National Politicians' in the 'title' column and the given names
    df = df[(df['title'] == 'National Politicians') & (df['name'].isin(names_order))]

    # Create an empty dictionary to store the aggregated data for each group
    aggregated_data = {}

    # Count the number of posts for each group by week
    message_count = df.pivot_table(index='name', columns='year_week', aggfunc='size', fill_value=0).reset_index()

    # Ensure all names are present in the aggregated data
    all_names_df = pd.DataFrame({'name': names_order})
    message_count = all_names_df.merge(message_count, on='name', how='left').fillna(0)

    aggregated_data['message count'] = message_count

    # Calculate averages for the renamed columns and store in the aggregated_data dictionary
    for original_col, renamed_col in mapping_dict.items():
        group_data = df.pivot_table(index='name', columns='year_week', values=renamed_col, aggfunc='mean',
                                    fill_value=0).reset_index()

        # Ensure all names are present in the aggregated data
        group_data = all_names_df.merge(group_data, on='name', how='left').fillna(0)

        aggregated_data[renamed_col] = group_data

    # Use the previous function to upload each aggregated DataFrame to the specified Google Sheet
    spreadsheet_id = "1Rmr2oP_c65_m2B23ntFed2JoRe8rFWOUYYexFP1cS_Q"
    for tab_name, data in aggregated_data.items():
        # Convert the entire DataFrame to string format to prevent JSON errors
        data = data.astype("str")
        save_dataframe_preserve_col_A(data, spreadsheet_id, tab_name)



mapping_dict = {
    'retweets':"retweet/share",
    'actual.shareCount':"retweet/share",
    'replies': "reply/comment",
    'actual.commentCount': "reply/comment",
    'likes':"likes",
    'actual.likeCount':"likes"
}

# Assuming df has already been defined or loaded
process_and_upload(df2, mapping_dict)



###save



