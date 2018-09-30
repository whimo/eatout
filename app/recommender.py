from app import app, models
from lightfm import LightFM
from lightfm.data import Dataset
import pickle
import numpy as np


LIGHTFM_LOSS = 'warp'
LIGHTFM_COMPONENTS = 32
LIGHTFM_EPOCHS = 8

POSITIVE_FILENAME = 'positive_recommender.pkl'
COMBINED_FILENAME = 'combined_recommender.pkl'


class PositiveRecommender:
    def __init__(self,
                 loss=LIGHTFM_LOSS,
                 n_components=LIGHTFM_COMPONENTS,
                 epochs=LIGHTFM_EPOCHS,
                 user_ids=None,
                 place_ids=None):
        self.model = LightFM(loss=loss, no_components=n_components)
        self.dataset = Dataset()
        self.dataset.fit(user_ids if user_ids else (user.id for user in models.User.query.distinct()),
                         place_ids if place_ids else (place.id for place in models.Place.query.distinct()))

        self.user_model_map = self.dataset.mapping()[0]
        self.model_place_map = {v: k for k, v in self.dataset.mapping()[2].items()}

        self.n_places = self.dataset.interactions_shape()[1]

        # Construct array of places database IDs, with indices indicating the place's index in the dataset
        self.place_ids = np.array([self.model_place_map.get(i) for i in range(self.n_places)])

        self.epochs = epochs

    def fit(self, reviews=None, save=True):
        if not reviews:
            reviews = models.Review.query.filter(models.Review.rating > 4)

        interactions, weights = self.dataset.build_interactions(((review.user_id, review.place_id)
                                                                 for review in reviews))
        self.model.fit(interactions, epochs=self.epochs)

        if save:
            self.save()

    def fit_partial(self, reviews, save=True):
        interactions, weights = self.dataset.build_interactions(((review.user_id, review.place_id)
                                                                 for review in reviews))
        self.model.fit_partial(interactions, epochs=self.epochs)

        if save:
            self.save()

    def recommend(self, user_id, filter_place_ids=None):
        if not filter_place_ids:
            model_place_ids = np.arange(self.n_places)
        else:
            model_place_ids = [self.place_model_map[id] for id in filter_place_ids]

        model_user_id = self.user_model_map[user_id]
        scores = self.model.predict(model_user_id, model_place_ids)
        places_ranking = self.place_ids[model_place_ids[np.argsort(-scores)]]

        return places_ranking

    def save(self, filename=POSITIVE_FILENAME):
        with open(filename, 'wb') as f:
            pickle.dump(self.__dict__, f, 2)

    def load(self, filename=POSITIVE_FILENAME):
        with open(filename, 'rb') as f:
            self.__dict__.update(pickle.load(f))


class CombinedRecommender:
    def __init__(self,
                 positive_loss=LIGHTFM_LOSS,
                 negative_loss=LIGHTFM_LOSS,
                 positive_n_components=LIGHTFM_COMPONENTS,
                 negative_n_components=LIGHTFM_COMPONENTS,
                 positive_epochs=LIGHTFM_EPOCHS,
                 negative_epochs=LIGHTFM_EPOCHS,
                 weighed_negatives=True,
                 user_ids=None,
                 place_ids=None):
        self.positive_model = LightFM(loss=positive_loss, no_components=positive_n_components)
        self.negative_model = LightFM(loss=negative_loss, no_components=negative_n_components)

        self.update_dataset(user_ids, place_ids)

        self.positive_epochs = positive_epochs
        self.negative_epochs = negative_epochs

    def update_dataset(self, user_ids=None, place_ids=None):
        self.dataset = Dataset()
        self.dataset.fit(user_ids if user_ids else (user.id for user in models.User.query.distinct()),
                         place_ids if place_ids else (place.id for place in models.Place.query.distinct()))

        self.user_model_map = self.dataset.mapping()[0]
        self.place_model_map = self.dataset.mapping()[2]
        self.model_place_map = {v: k for k, v in self.place_model_map.items()}

        self.n_places = self.dataset.interactions_shape()[1]

        # Construct array of places database IDs, with indices indicating the place's index in the dataset
        self.place_ids = np.array([self.model_place_map.get(i) for i in range(self.n_places)])

    def fit(self, reviews=None, save=True):
        if not reviews:
            positive_reviews = models.Review.query.filter(models.Review.rating > 4)
            negative_reviews = models.Review.query.filter(models.Review.rating <= 4)

        self.update_dataset()

        positive_interactions, _ = self.dataset.build_interactions(((review.user_id, review.place_id)
                                                                    for review in positive_reviews))

        negative_interactions, negative_weights =\
            self.dataset.build_interactions(((review.user_id, review.place_id, 5 - review.rating)
                                             for review in negative_reviews))

        self.positive_model.fit(positive_interactions, epochs=self.positive_epochs)
        self.negative_model.fit(negative_interactions, sample_weight=negative_weights,
                                epochs=self.negative_epochs)

        if save:
            self.save()

    def fit_partial(self, reviews, save=True):
        positive_interactions, _ =\
            self.dataset.build_interactions(((review.user_id, review.place_id)
                                             for review in reviews if review.rating > 4))

        negative_interactions, negative_weights =\
            self.dataset.build_interactions(((review.user_id, review.place_id, 5 - review.rating)
                                             for review in reviews if review.rating <= 4))

        self.positive_model.fit_partial(positive_interactions, epochs=self.positive_epochs)
        self.negative_model.fit_partial(negative_interactions, sample_weight=negative_weights,
                                        epochs=self.negative_epochs)

        if save:
            self.save()

    def recommend(self, user_id, filter_place_ids=None):
        if not filter_place_ids:
            model_place_ids = np.arange(self.n_places)
        else:
            model_place_ids = np.array([self.place_model_map[id] for id in filter_place_ids])

        model_user_id = self.user_model_map[user_id]
        positive_scores = self.positive_model.predict(model_user_id, model_place_ids)
        negative_scores = self.negative_model.predict(model_user_id, model_place_ids)
        places_ranking = self.place_ids[model_place_ids[np.argsort(-positive_scores / negative_scores)]]

        return places_ranking

    def save(self, filename=COMBINED_FILENAME):
        with open(filename, 'wb') as f:
            pickle.dump(self.__dict__, f, 2)

    def load(self, filename=COMBINED_FILENAME):
        with open(filename, 'rb') as f:
            self.__dict__.update(pickle.load(f))
