# Disinfo Radar

The Disinfo Radar pipeline consists of these main steps:
1. Scrape articles 
2. Preprocess articles
3. Load sentences from articles
4. Extract technology-related spans from sentences
5. Predict disinformation potential factor scores for each span
6. Analyze overall disinformation potential for tech topics

To run the pipeline, run the `DisinfoPipeline.py` script.
For now, output data is stored locally in the `Output` directory.
