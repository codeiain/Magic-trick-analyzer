#!/usr/bin/env python3
"""
Script to automatically approve all seeded tricks for training.
This marks seeded trick data as quality training data.
"""

import sys
import os

# Add the backend directory to the Python path to use the correct models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from infrastructure.database.models import TrickModel, TrainingReviewModel
from infrastructure.database.database import DatabaseManager
from infrastructure.config import get_config
from datetime import datetime
import uuid

def main():
    """Main function to approve all seeded tricks for training."""
    
    # Use the backend's database connection
    config = get_config()
    db_manager = DatabaseManager(config)
    db_manager.initialize()
    
    session = db_manager.get_session()
    
    try:
        # Get all tricks that don't have training reviews
        tricks_without_reviews = session.query(TrickModel).outerjoin(
            TrainingReviewModel, TrickModel.id == TrainingReviewModel.trick_id
        ).filter(TrainingReviewModel.id.is_(None)).all()
        
        print(f'Found {len(tricks_without_reviews)} tricks without training reviews')
        
        if len(tricks_without_reviews) == 0:
            print("All tricks already have training reviews!")
            return
        
        # Create training reviews for all seeded tricks
        created_count = 0
        for trick in tricks_without_reviews:
            review = TrainingReviewModel(
                id=str(uuid.uuid4()),
                trick_id=trick.id,
                book_id=trick.book_id,
                is_accurate=True,  # Mark as accurate
                confidence_score=0.9,  # High confidence
                quality_score=0.9,  # High quality
                use_for_training=True,  # Use for training
                review_notes='Auto-approved seeded trick data',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(review)
            created_count += 1
            print(f'Created review for trick: {trick.name}')
        
        session.commit()
        print(f'\n✅ Successfully created {created_count} training reviews!')
        print('All seeded tricks have been approved for training!')
        
        # Verify the results
        total_reviews = session.query(TrainingReviewModel).count()
        approved_reviews = session.query(TrainingReviewModel).filter(
            TrainingReviewModel.is_accurate == True,
            TrainingReviewModel.use_for_training == True
        ).count()
        
        print(f'\n📊 Training Review Summary:')
        print(f'   Total reviews: {total_reviews}')
        print(f'   Approved for training: {approved_reviews}')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == '__main__':
    main()