import datetime


def search_with_decay(self, query_embedding, k=10, decay_factor=0.95):
    """
    Weight recent memories higher than old ones

    Score = Similarity * (decay_factor ^ days_ago)
    """
    candidates = self.search(query_embedding, k=k * 5)

    current_time = datetime.now()

    for result in candidates:
        age_days = (current_time - result["metadata"]["timestamp"]).days
        decay_multiplier = decay_factor**age_days
        result["relevance"] *= decay_multiplier

    # Re-sort by adjusted relevance
    candidates.sort(key=lambda x: x["relevance"], reverse=True)

    return candidates[:k]
