# Disinfo Radar

The Disinfo Radar pipeline consists of these main steps:
1. Scrape articles 
2. Preprocess articles
3. Load sentences from articles
4. Extract technology-related spans from sentences
5. Predict disinformation potential factor scores for each span
6. Analyze overall disinformation potential for tech topics

Here is an example of how to set up and run the pipeline:

1. `conda create -n dr_test python=3.9`
2. `conda activate dr_test`
3. `pip install -r requirements.txt`
4. `python DisinfoPipeline.py`

For now, output data is stored locally in the `Output` directory and a subset is uploaded to Google Drive to feed into Infogram visualizations.
