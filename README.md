# Disinfo Radar

The Disinfo Radar pipeline consists of these main steps:
1. Scrape articles 
2. Preprocess articles
3. Load sentences from articles
4. Extract technology-related spans from sentences
5. Predict disinformation potential factor scores for each span
6. Analyze overall disinformation potential for tech topics

Here is an example of how to set up and run the pipeline:

1. `conda create -n disinfo_pipeline python=3.9`
2. `conda activate disinfo_pipeline`
3. `pip install -r requirements.txt`
4. `python DisinfoPipeline.py`

A couple of NLTK packages are also needed, which can be installed from a Python shell like this:
1. `import nltk`
2. `nltk.download('punkt')`
3. `nltk.download('stopwords')`

For now, output data is stored locally in the `Output` directory and a subset is uploaded to Google Drive to feed into Infogram visualizations.

To see or edit file locations or pipeline settings, use the `config.ini` file.

For a quick test run of the pipeline with a small data sample, set `test_run_small_sample` to true in `config.ini`.
