import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.neighbors import NearestNeighbors
from sklearn.feature_extraction.text import TfidfVectorizer
from sqlalchemy.orm import Session
from typing import List, Dict, Tuple
import pickle
import os
from .database import Product, UserInteraction
from .config import Config
from utils.logger import logger

class RecommendationEngine:
    def __init__(self):
        self.user_item_matrix = None
        self.item_similarity_matrix = None
        self.user_similarity_matrix = None
        self.tfidf_matrix = None
        self.tfidf_vectorizer = None
        self.knn_model = None
        self.product_ids = []
        self.user_ids = []
        
    def build_collaborative_filtering(self, db: Session):
        """Build user-item interaction matrix"""
        logger.info("Building collaborative filtering model...")
        
        # Get all interactions
        interactions = db.query(UserInteraction).all()
        
        if not interactions:
            logger.warning("No interactions found")
            return
        
        # Create dataframe
        df = pd.DataFrame([
            {
                'user_id': i.user_id,
                'product_id': i.product_id,
                'rating': i.rating_value if i.rating_value else 1
            }
            for i in interactions
        ])
        
        # Create pivot table
        self.user_item_matrix = df.pivot_table(
            index='user_id', 
            columns='product_id', 
            values='rating',
            fill_value=0
        )
        
        self.user_ids = self.user_item_matrix.index.tolist()
        self.product_ids = self.user_item_matrix.columns.tolist()
        
        # Compute item-item similarity
        logger.info("Computing item similarity matrix...")
        self.item_similarity_matrix = cosine_similarity(self.user_item_matrix.T)
        
        # Compute user-user similarity
        logger.info("Computing user similarity matrix...")
        self.user_similarity_matrix = cosine_similarity(self.user_item_matrix)
        
        logger.info(f"Collaborative filtering built: {len(self.user_ids)} users, {len(self.product_ids)} products")
        
    def build_content_based_filtering(self, db: Session):
        """Build content-based filtering using product descriptions"""
        logger.info("Building content-based filtering model...")
        
        products = db.query(Product).all()
        
        if not products:
            logger.warning("No products found")
            return
        
        # Create product features
        product_features = []
        self.product_ids = [p.id for p in products]
        
        for product in products:
            # Combine description and category for text features
            feature_text = f"{product.name} {product.description} {product.category}"
            product_features.append(feature_text)
        
        # Create TF-IDF matrix
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(product_features)
        
        # Build KNN model for fast similarity search
        self.knn_model = NearestNeighbors(n_neighbors=Config.N_RECOMMENDATIONS, metric='cosine')
        self.knn_model.fit(self.tfidf_matrix)
        
        logger.info(f"Content-based filtering built: {len(self.product_ids)} products")
    
    def get_collaborative_recommendations(self, user_id: int, n_recommendations: int = None) -> List[int]:
        """Get collaborative filtering recommendations for a user"""
        if n_recommendations is None:
            n_recommendations = Config.N_RECOMMENDATIONS
            
        if self.user_item_matrix is None or user_id not in self.user_ids:
            return []
        
        user_idx = self.user_ids.index(user_id)
        user_ratings = self.user_item_matrix.iloc[user_idx].values
        
        # Get similar users
        similar_users = self.user_similarity_matrix[user_idx].argsort()[::-1][1:11]
        
        # Aggregate ratings from similar users
        similar_ratings = self.user_item_matrix.iloc[similar_users].mean(axis=0)
        
        # Exclude already interacted products
        interacted_products = user_ratings.nonzero()[0]
        similar_ratings.iloc[interacted_products] = 0
        
        # Get top recommendations
        top_products = similar_ratings.nlargest(n_recommendations).index.tolist()
        
        return top_products
    
    def get_content_based_recommendations(self, product_id: int, n_recommendations: int = None) -> List[int]:
        """Get content-based recommendations for a product"""
        if n_recommendations is None:
            n_recommendations = Config.N_RECOMMENDATIONS
            
        if self.tfidf_matrix is None or product_id not in self.product_ids:
            return []
        
        product_idx = self.product_ids.index(product_id)
        
        # Find similar products using KNN
        distances, indices = self.knn_model.kneighbors(
            self.tfidf_matrix[product_idx], 
            n_neighbors=n_recommendations + 1
        )
        
        # Skip the first one (the product itself)
        similar_indices = indices[0][1:]
        similar_products = [self.product_ids[i] for i in similar_indices]
        
        return similar_products
    
    def get_hybrid_recommendations(self, user_id: int, db: Session, n_recommendations: int = None) -> List[Dict]:
        """Get hybrid recommendations combining collaborative and content-based filtering"""
        if n_recommendations is None:
            n_recommendations = Config.N_RECOMMENDATIONS
        
        # Get collaborative recommendations
        collab_recs = self.get_collaborative_recommendations(user_id, n_recommendations * 2)
        
        # Get user's recent interactions for content-based recommendations
        recent_interactions = db.query(UserInteraction)\
            .filter(UserInteraction.user_id == user_id)\
            .order_by(UserInteraction.timestamp.desc())\
            .limit(5)\
            .all()
        
        content_recs = []
        for interaction in recent_interactions:
            product_recs = self.get_content_based_recommendations(
                interaction.product_id, 
                n_recommendations
            )
            content_recs.extend(product_recs)
        
        # Combine and deduplicate recommendations
        all_recs = list(dict.fromkeys(collab_recs + content_recs))
        
        # Get product details
        products = db.query(Product).filter(Product.id.in_(all_recs[:n_recommendations])).all()
        
        recommendations = []
        for product in products:
            recommendations.append({
                'id': product.id,
                'name': product.name,
                'description': product.description[:100],
                'price': product.price,
                'category': product.category,
                'image_url': product.image_url,
                'rating': product.rating,
                'score': 1.0  # Placeholder for recommendation score
            })
        
        return recommendations
    
    def save_models(self):
        """Save trained models to disk"""
        models_dir = "models"
        os.makedirs(models_dir, exist_ok=True)
        
        model_data = {
            'user_item_matrix': self.user_item_matrix,
            'item_similarity_matrix': self.item_similarity_matrix,
            'user_similarity_matrix': self.user_similarity_matrix,
            'tfidf_matrix': self.tfidf_matrix,
            'tfidf_vectorizer': self.tfidf_vectorizer,
            'knn_model': self.knn_model,
            'product_ids': self.product_ids,
            'user_ids': self.user_ids
        }
        
        with open(f"{models_dir}/recommendation_models.pkl", 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info("Models saved successfully")
    
    def load_models(self):
        """Load trained models from disk"""
        models_path = "models/recommendation_models.pkl"
        
        if os.path.exists(models_path):
            with open(models_path, 'rb') as f:
                model_data = pickle.load(f)
            
            self.user_item_matrix = model_data['user_item_matrix']
            self.item_similarity_matrix = model_data['item_similarity_matrix']
            self.user_similarity_matrix = model_data['user_similarity_matrix']
            self.tfidf_matrix = model_data['tfidf_matrix']
            self.tfidf_vectorizer = model_data['tfidf_vectorizer']
            self.knn_model = model_data['knn_model']
            self.product_ids = model_data['product_ids']
            self.user_ids = model_data['user_ids']
            
            logger.info("Models loaded successfully")
            return True
        
        return False