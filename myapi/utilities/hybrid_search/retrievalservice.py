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

        keyword_result = DocumentChunk.objects.filter(
            document__user=user,
            search_vector=search_query
        ).annotate(
            rank=SearchRank('search_vector', search_query)
        ).order_by("-rank")[:20]

        fused_score = reciprocal_rank_fusion(vector_results=vector_results, keyword_results=keyword_result)

        canditate_ids = [item[0] for item in fused_score[:20]]
        candidate_context_chunks = list(DocumentChunk.objects.filter(id__in=canditate_ids))

        final_context_objects= RerankService.get_top_reranked_results(
           query= query,
           chunks= candidate_context_chunks,
           top_k= 5
        )

        # This returns list of strings (JSON Serialisable) for State to pass on
        result_in_string= [obj.chunk for obj in final_context_objects]

        return result_in_string
    

