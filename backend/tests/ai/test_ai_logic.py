import pytest
from app.ai.similarity import calculate_cosine_similarity
from app.ai.clustering import run_dbscan_clustering

def test_cosine_similarity_identical_vectors():
    """Verify similarity of identical vectors yields exactly 1.0."""
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    similarity = calculate_cosine_similarity(v1, v2)
    assert abs(similarity - 1.0) < 1e-5


def test_cosine_similarity_orthogonal_vectors():
    """Verify similarity of orthogonal vectors yields exactly 0.0."""
    v1 = [1.0, 0.0, 0.0]
    v2 = [0.0, 1.0, 0.0]
    similarity = calculate_cosine_similarity(v1, v2)
    assert abs(similarity - 0.0) < 1e-5


def test_cosine_similarity_inverse_vectors():
    """Verify similarity of opposite vectors yields exactly -1.0."""
    v1 = [1.0, 0.0, 0.0]
    v2 = [-1.0, 0.0, 0.0]
    similarity = calculate_cosine_similarity(v1, v2)
    assert abs(similarity - (-1.0)) < 1e-5


def test_dbscan_grouping():
    """Verify DBSCAN clustering groups close vectors and splits far ones."""
    # 3 close vectors (Cluster 0), 2 other close vectors (Cluster 1)
    embeddings = [
        [1.0, 0.0, 0.0],
        [0.99, 0.01, 0.0],
        [0.98, 0.02, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.99, 0.01]
    ]
    
    # eps = 0.05 (distance = 1 - similarity. 1 - 0.99 = 0.01 <= 0.05. Grouped!)
    labels = run_dbscan_clustering(embeddings, eps=0.05, min_samples=1)
    
    # Assert vectors 0, 1, 2 have the same cluster label
    assert labels[0] == labels[1] == labels[2]
    # Assert vectors 3, 4 have a different cluster label
    assert labels[3] == labels[4]
    assert labels[0] != labels[3]
