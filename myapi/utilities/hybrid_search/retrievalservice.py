from myapi.models import DocumentChunk
from pgvector.django import CosineDistance
from myapi.utilities.hybrid_search.rrf import reciprocal_rank_fusion
from myapi.utilities.hybrid_search.reranker import RerankService
from django.contrib.postgres.search import SearchQuery, SearchRank

class HybridRetrievalRerankService:
    @staticmethod
    def get_hybrid_reranked_content(user, query, query_vector, top_k= 5):
        
        
        vector_results= DocumentChunk.objects.filter(
            document__user= user,
        ).annotate(
            similarity= 1 - CosineDistance("embedding", query_vector)
        ).order_by("-similarity")[:20]

        search_query= SearchQuery(query, config='english', search_type='websearch')

        keyword_result= DocumentChunk.objects.filter(
            document__user= user,
            search_vector= search_query
        ).order_by("-id")[:20]

        print(f"DEBUG: Vector Results Found: {vector_results.count()}")
        print(f"DEBUG: Keyword Results Found: {keyword_result.count()}")

        fused_score = reciprocal_rank_fusion(vector_results=vector_results, keyword_results=keyword_result)
        print(f"DEBUG: RRF Fused IDs: {fused_score}")

        canditate_ids = [item[0] for item in fused_score[:20]]
        candidate_context_chunks = list(DocumentChunk.objects.filter(id__in=canditate_ids))
        print(f"DEBUG: Final Chunks to LLM: {len(candidate_context_chunks)}")

        final_context= RerankService.get_top_reranked_results(
           query= query,
           chunks= candidate_context_chunks,
           top_k= 5
        )

        final_context = candidate_context_chunks[:5] 

        return final_context
    

