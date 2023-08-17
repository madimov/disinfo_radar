from sentence_transformers import SentenceTransformer
import pickle
from tqdm import tqdm

from Config import Config

class DisinfoFactorScorer:

    def __init__(self):
        print("creating DisinfoFactorScorer...")
        self.model_sentence_transformer = SentenceTransformer(Config.cfg['default']['model_name_sentence_transformer'])
        self.classifier_accessibility = self.load_obj(Config.cfg['default']['location_model_RE_accessibility'])
        self.classifier_content_gen = self.load_obj(Config.cfg['default']['location_model_RE_content_generation'])
        # self.classifier_automation = self.load_obj("models/RE_model_automation.pkl")
        self.classifier_automation = self.load_obj(Config.cfg['default']['location_model_RE_automation'])
        pass

    def predict_disinfo_factor(self, _sentence, _vectorizer, _classifier, with_probability=False):
        _embedding = _vectorizer.encode(_sentence)
        if with_probability:
            return _classifier.predict([_embedding])[0], list(_classifier.predict_proba([_embedding])[0])
        else:
            return _classifier.predict([_embedding])[0]

    def get_list_predictions_w_prob(self, _sentences, _vectorizer, _classifier):
        predictions = []
        probabilities = []
        
        for sentence in tqdm(_sentences):
            prediction, probability = self.predict_disinfo_factor(sentence, _vectorizer, _classifier, True)
            predictions.append(prediction)
            probabilities.append(probability)

        return predictions, probabilities

    def get_prediction_from_prob_pair(self, _prob_pair):
        prob_0 = _prob_pair[0]
        prob_1 = _prob_pair[1]
        if prob_0 >= prob_1:
            pred_from_prob = 0
        else:
            pred_from_prob = 1
        return pred_from_prob

    def get_predictions_from_probs(self, _probs):

        predictions_from_probs = []

        for prob_pair in _probs:
            predictions_from_probs.append(self.get_prediction_from_prob_pair(prob_pair))

        return predictions_from_probs

    def get_disinfo_factor_scores(self, text):
    #     print(text)
    #     print()
        prob_pair_accessibility = self.predict_disinfo_factor(text, self.model_sentence_transformer, self.classifier_accessibility, True)[1]
    #     prediction_accessibility = get_prediction_from_prob_pair(accessibility_prob_pair)
        score_accessibility = prob_pair_accessibility[1]
    #     print(f"accessibility: \t{score_accessibility}")
        
        prob_pair_content_gen = self.predict_disinfo_factor(text, self.model_sentence_transformer, self.classifier_content_gen, True)[1]
        score_content_gen = prob_pair_content_gen[1]
    #     print(f"content_gen: \t{score_content_gen}")
        
        prob_pair_automation = self.predict_disinfo_factor(text, self.model_sentence_transformer, self.classifier_automation, True)[1]
        score_automation = prob_pair_automation[1]
    #     print(f"automation: \t{score_automation}")
        
        scores_obj = {
            "accessibility": score_accessibility,
            "content_gen": score_content_gen,
            "automation": score_automation
        }
        
        return scores_obj
    
    def get_all_disinfo_factor_scores(self, span_data_objs):
        span_scores_data_objs = []
        for span_data_obj in tqdm(span_data_objs):
            
            scores_obj = self.get_disinfo_factor_scores(span_data_obj["sentence_masked"])
            combined_obj = {
                **span_data_obj, 
                **scores_obj
            }
            span_scores_data_objs.append(combined_obj)
        return span_scores_data_objs

    def save_obj(self, obj, filename):
        with open(filename, 'wb') as f:
            pickle.dump(obj, f)
            
    def load_obj(self, filename):
        with open(filename, 'rb') as f:
            obj = pickle.load(f)
            return obj