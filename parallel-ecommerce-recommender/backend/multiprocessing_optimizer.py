import multiprocessing as mp
from multiprocessing import Pool, Process, Queue
from typing import List, Dict, Any
import numpy as np
from functools import partial
import time
from utils.logger import logger
from .config import Config

class MultiprocessingOptimizer:
    def __init__(self):
        self.num_processes = Config.NUM_PROCESSES
        self.performance_stats = {}
        
    def parallel_recommendation_generation(self, user_ids: List[int], recommendation_function, **kwargs):
        """Generate recommendations for multiple users in parallel"""
        logger.info(f"Generating recommendations for {len(user_ids)} users using {self.num_processes} processes")
        
        start_time = time.time()
        
        # Create a pool of workers
        with Pool(processes=self.num_processes) as pool:
            # Prepare arguments for each user
            func_partial = partial(recommendation_function, **kwargs)
            
            # Map users to processes
            results = pool.map(func_partial, user_ids)
        
        execution_time = time.time() - start_time
        
        self.performance_stats['parallel_execution_time'] = execution_time
        logger.info(f"Parallel execution completed in {execution_time:.2f} seconds")
        
        return results
    
    def sequential_recommendation_generation(self, user_ids: List[int], recommendation_function, **kwargs):
        """Generate recommendations sequentially for comparison"""
        logger.info(f"Generating recommendations for {len(user_ids)} users sequentially")
        
        start_time = time.time()
        
        results = []
        for user_id in user_ids:
            result = recommendation_function(user_id, **kwargs)
            results.append(result)
        
        execution_time = time.time() - start_time
        
        self.performance_stats['sequential_execution_time'] = execution_time
        logger.info(f"Sequential execution completed in {execution_time:.2f} seconds")
        
        return results
    
    def parallel_similarity_computation(self, matrix: np.ndarray) -> np.ndarray:
        """Compute similarity matrix in parallel"""
        logger.info(f"Computing similarity matrix of shape {matrix.shape} in parallel")
        
        n_items = matrix.shape[0]
        chunk_size = n_items // self.num_processes
        
        # Create chunks for parallel processing
        chunks = []
        for i in range(0, n_items, chunk_size):
            chunks.append(matrix[i:i+chunk_size])
        
        start_time = time.time()
        
        # Compute similarity for chunks in parallel
        with Pool(processes=self.num_processes) as pool:
            similarity_chunks = pool.map(self._compute_similarity_chunk, chunks)
        
        # Combine results
        similarity_matrix = np.vstack(similarity_chunks)
        
        execution_time = time.time() - start_time
        self.performance_stats['similarity_computation_time'] = execution_time
        
        logger.info(f"Parallel similarity computation completed in {execution_time:.2f} seconds")
        
        return similarity_matrix
    
    @staticmethod
    def _compute_similarity_chunk(chunk: np.ndarray) -> np.ndarray:
        """Compute similarity for a chunk of the matrix"""
        from sklearn.metrics.pairwise import cosine_similarity
        return cosine_similarity(chunk)
    
    def parallel_batch_processing(self, items: List[Any], processing_function, batch_size: int = 100):
        """Process items in parallel batches"""
        logger.info(f"Processing {len(items)} items in batches of {batch_size}")
        
        # Create batches
        batches = [items[i:i+batch_size] for i in range(0, len(items), batch_size)]
        
        start_time = time.time()
        
        with Pool(processes=self.num_processes) as pool:
            results = pool.map(processing_function, batches)
        
        execution_time = time.time() - start_time
        self.performance_stats['batch_processing_time'] = execution_time
        
        # Flatten results
        flattened_results = [item for batch in results for item in batch]
        
        logger.info(f"Parallel batch processing completed in {execution_time:.2f} seconds")
        
        return flattened_results
    
    def get_performance_comparison(self) -> Dict:
        """Get performance comparison between sequential and parallel execution"""
        if 'sequential_execution_time' in self.performance_stats and 'parallel_execution_time' in self.performance_stats:
            speedup = self.performance_stats['sequential_execution_time'] / self.performance_stats['parallel_execution_time']
            efficiency = (speedup / self.num_processes) * 100
            
            return {
                'sequential_time': self.performance_stats['sequential_execution_time'],
                'parallel_time': self.performance_stats['parallel_execution_time'],
                'speedup': speedup,
                'efficiency_percent': efficiency,
                'num_processes': self.num_processes
            }
        
        return {}

class RecommendationWorker:
    """Worker class for processing recommendations in parallel"""
    
    def __init__(self, recommendation_engine):
        self.recommendation_engine = recommendation_engine
        
    def generate_user_recommendations(self, user_id: int, db_session, n_recommendations: int = 10):
        """Generate recommendations for a single user"""
        try:
            recommendations = self.recommendation_engine.get_hybrid_recommendations(
                user_id, db_session, n_recommendations
            )
            return {'user_id': user_id, 'recommendations': recommendations, 'success': True}
        except Exception as e:
            logger.error(f"Error generating recommendations for user {user_id}: {str(e)}")
            return {'user_id': user_id, 'recommendations': [], 'success': False}