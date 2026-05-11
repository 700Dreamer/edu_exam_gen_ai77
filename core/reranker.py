from flashrank import Ranker, RerankRequest

class EduQuestReranker:
    def __init__(self, model_name="ms-marco-MiniLM-L-12-v2"):
        # Nano is faster and run on CPU excellently
        self.ranker = Ranker(model_name=model_name, cache_dir="/tmp/flashrank")

    def rerank(self, query, documents, top_n=5):
        """
        query: str
        documents: list of dicts with "text" and "metadata"
        """
        # FlashRank expects list of dicts: [{"id": 1, "text": "...", "metadata": {...}}]
        formatted_docs = []
        for i, doc in enumerate(documents):
            formatted_docs.append({
                "id": i,
                "text": doc.get("content", doc.get("text", "")),
                "metadata": doc.get("metadata", {})
            })
            
        rerankrequest = RerankRequest(query=query, passages=formatted_docs)
        results = self.ranker.rerank(rerankrequest)
        
        # Return top N
        return results[:top_n]

# singleton
_reranker = None
def get_reranker():
    global _reranker
    if _reranker is None:
        _reranker = EduQuestReranker()
    return _reranker
