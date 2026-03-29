def reciprocal_rank_fusion(vector_results, keyword_results, k=60):
    scores = {}
    
    # Rank 1 gets 1/(60+1), Rank 2 gets 1/(60+2)...
    for rank, chunk in enumerate(vector_results, 1):
        scores[chunk.id] = scores.get(chunk.id, 0) + 1 / (k + rank)
        
    for rank, chunk in enumerate(keyword_results, 1):
        scores[chunk.id] = scores.get(chunk.id, 0) + 1 / (k + rank)
        
    # Sort by the new fused score
    sorted_ids = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_ids[:5] # Return top 5
