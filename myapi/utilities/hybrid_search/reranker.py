import voyageai
from backend.config import settings

class RerankService:
    vo= voyageai.Client(api_key= settings.reranker_voyage_ai_api_key.get_secret_value())


    @staticmethod
    def get_top_reranked_results(query: str, chunks: list, top_k= 3):

        if not chunks:
            print("No chunks Found!")
            return []

        documents= [chunk.chunk for chunk in chunks]

        reranking= RerankService.vo.rerank(
            query= query,
            documents= documents,
            model= "rerank-2.5"
        )

        return [chunks[res.index] for res in reranking.results]
    
