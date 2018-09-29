from app import app, models
from lightfm import LightFM
from lightfm.data import Dataset
import numpy as np


LIGHTFM_LOSS = 'warp'
LIGHTFM_COMPONENTS = 32
LIGHTFM_EPOCHS = 8


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
        self.model_place_map = {v: k for k, v in self.dataset.mapping()[2]}

        self.n_places = self.dataset.interactions_shape()[1]

        # Construct array of places database IDs, with indices indicating the place's index in the dataset
        self.place_ids = np.array([self.model_place_map.get(i) for i in range(self.n_places)])

        self.epochs = epochs

    def fit(self, reviews=None):
        if not reviews:
            reviews = models.Review.query

        interactions, weights = self.dataset.build_interactions(((review.user_id, review.place_id)
                                                                 for review in reviews))
        self.model.fit(interactions, epochs=self.epochs)

    def recommend(self, user_id):
        model_user_id = self.dataset.mapping()[2][user_id]
        scores = self.model.predict(model_user_id, np.arange(self.n_places))
        places_ranking = self.place_ids[np.argsort(-scores)]

        return places_ranking