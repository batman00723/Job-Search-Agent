from myapi.models import DocumentChunk
from pgvector.django import CosineDistance
from myapi.utilities.hybrid_search.rrf import reciprocal_rank_fusion
from myapi.utilities.hybrid_search.reranker import RerankService

class HybridRetrievalRerankService:
    @staticmethod
    def get_hybrid_reranked_content(user, query, query_vector, top_k= 5):
        
        
        vector_results= DocumentChunk.objects.filter(
            document__user= user,
        ).annotate(
            similarity= 1 - CosineDistance("embedding", query_vector)
        ).order_by("-similarity")[:20]

        keyword_result= DocumentChunk.objects.filter(
            document__user= user,
            search_vector= query
        ).order_by("-id")[:20]

        fused_score= reciprocal_rank_fusion(vector_results= vector_results,
                                            keyword_results= keyword_result)
        
        canditate_ids= [item[0] for item in fused_score[:20]]  # we are using item[0] cus rrf returns a list of tupules (id, score) so item[0] ensures we fetch only id not score.
        candidate_context_chunks= list(DocumentChunk.objects.filter(id__in= canditate_ids))

        final_context= RerankService.get_top_reranked_results(
            query= query,
            chunks= candidate_context_chunks,
            top_k= 5
        )

        return final_context