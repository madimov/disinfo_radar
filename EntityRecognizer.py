import spacy
from tqdm import tqdm

from Config import Config

class EntityRecognizer:

    def __init__(self):
        print("creating EntityRecognizer...")
        # self.nlp_spancat = spacy.load("models/SpanCategorizer/output_testing_spancat_single_label/model-best")
        self.nlp_spancat = spacy.load(Config.cfg['default']['location_model_spacy_spancat'])
        pass

    def get_spans_and_scores(self, doc_spacy):
        # used spancat_singlelabel, it works better!
        scores = doc_spacy.spans["sc"].attrs["scores"] 
        list_objs = []
        for i, span in enumerate(doc_spacy.spans["sc"]): # span_cat
        #     print(ent.text, ent.start_char, ent.end_char, ent.label_)
            score = scores[i]
        #     print(span, "\t\t\t", score)
        #     if score > 0.99:
        #         print(span, "\t\t\t", score, "!!!!!!!!!")
        #     else:
        #         print(span, "\t\t\t", score)
            obj = {
                "span": span,
                "score": score[0]
            }
            list_objs.append(obj)
        return list_objs
    
    def mask_technology_span(self, _text, start, end):
        mask = "{TECHNOLOGY_X}"
        masked_text = _text[0:start] + mask + _text[end:-1]
        return masked_text
    
    def get_spans_from_sentence_objs(self, raw_sentences_objs):
        span_data_objs = []
        for raw_sentence_obj in tqdm(raw_sentences_objs):
            doc_sentence = self.nlp_spancat(raw_sentence_obj["sentence"])
            spans_scores = self.get_spans_and_scores(doc_sentence)
            if (len(spans_scores) > 0):
        #         print(doc_sentence)
                for span_score in spans_scores:
        #             print()
                    span = span_score["span"]
        #             print(span_score)
                    masked_sentence = self.mask_technology_span(doc_sentence.text, span.start_char, span.end_char)
            
                    span_data = {
        #                 "sentence_original": sentence,
                        "span_text": span.text,
                        "span_score": span_score["score"],
                        "span_start_char": span.start_char,
                        "span_end_char": span.end_char,
                        "sentence_masked": masked_sentence
                    }
                
                    combined_obj = {
                        **raw_sentence_obj, 
                        **span_data
                    }
                    
                    span_data_objs.append(combined_obj)
        #             print(doc_sentence[span.start : span.end])
        #             print(masked_sentence)
        #             print("-----------")
        #         print("============================\n")
        return span_data_objs