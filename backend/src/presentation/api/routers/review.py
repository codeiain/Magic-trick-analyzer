"""
Web interface routes for trick review and feedback collection.
"""
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import HTMLResponse
from typing import List, Optional, Dict, Any
from uuid import UUID

from ....application.use_cases.magic_use_cases import SearchTricksUseCase, SearchTricksRequest
from ....domain.repositories.magic_repositories import TrickRepository, BookRepository
from ....domain.value_objects.common import TrickId, BookId
from ....infrastructure.ai.model_training import (
    FeedbackData, TrainingDataGenerator, ModelFineTuner, AdaptiveTrickDetector
)
from .schemas import FeedbackSchema, TrainingStatusSchema, ModelInfoSchema


def create_review_router(
    trick_repository: TrickRepository,
    book_repository: BookRepository,
    search_use_case: SearchTricksUseCase,
    training_data_generator: TrainingDataGenerator,
    model_fine_tuner: ModelFineTuner,
    adaptive_detector: AdaptiveTrickDetector
) -> APIRouter:
    """Create review router with injected dependencies."""
    
    router = APIRouter()
    
    @router.get("/", response_class=HTMLResponse)
    async def review_dashboard():
        """Serve the main review dashboard."""
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Magic Trick Analyzer - Review Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; color: #333; margin-bottom: 30px; }
                .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
                .stat-card { background: #6366f1; color: white; padding: 20px; border-radius: 8px; text-align: center; }
                .stat-number { font-size: 2em; font-weight: bold; margin-bottom: 5px; }
                .trick-card { border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin-bottom: 20px; background: #fafafa; }
                .trick-header { display: flex; justify-content: between; align-items: center; margin-bottom: 15px; }
                .trick-title { font-size: 1.2em; font-weight: bold; color: #333; }
                .confidence-badge { padding: 5px 10px; border-radius: 15px; color: white; font-size: 0.9em; }
                .confidence-high { background-color: #10b981; }
                .confidence-medium { background-color: #f59e0b; }
                .confidence-low { background-color: #ef4444; }
                .trick-details { margin-bottom: 15px; }
                .effect-type { background: #e5e7eb; padding: 3px 8px; border-radius: 12px; font-size: 0.9em; margin-right: 10px; }
                .feedback-section { border-top: 1px solid #ddd; padding-top: 15px; }
                .feedback-buttons { display: flex; gap: 10px; margin-bottom: 15px; }
                .btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; font-size: 0.9em; }
                .btn-correct { background: #10b981; color: white; }
                .btn-incorrect { background: #ef4444; color: white; }
                .btn-train { background: #6366f1; color: white; }
                .feedback-form { display: none; margin-top: 15px; padding: 15px; background: #f9fafb; border-radius: 4px; }
                .form-group { margin-bottom: 15px; }
                .form-label { display: block; margin-bottom: 5px; font-weight: bold; }
                .form-input { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
                .form-textarea { width: 100%; min-height: 80px; padding: 8px; border: 1px solid #ddd; border-radius: 4px; resize: vertical; }
                .loading { text-align: center; padding: 40px; color: #666; }
                .training-section { background: #f0f9ff; border: 1px solid #0ea5e9; border-radius: 8px; padding: 20px; margin-top: 30px; }
                .training-status { display: flex; align-items: center; gap: 10px; margin-bottom: 15px; }
                .status-indicator { width: 12px; height: 12px; border-radius: 50%; }
                .status-ready { background: #10b981; }
                .status-training { background: #f59e0b; }
                .status-error { background: #ef4444; }
                .pagination { text-align: center; margin-top: 20px; }
                .pagination button { margin: 0 5px; padding: 8px 12px; border: 1px solid #ddd; background: white; border-radius: 4px; cursor: pointer; }
                .pagination button.active { background: #6366f1; color: white; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎩 Magic Trick Analyzer - Review Dashboard</h1>
                    <p>Review AI-detected tricks and help improve the model</p>
                </div>
                
                <div class="stats-grid" id="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number" id="total-tricks">-</div>
                        <div>Total Tricks</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="pending-review">-</div>
                        <div>Pending Review</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="accuracy">-</div>
                        <div>Current Accuracy</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="training-examples">-</div>
                        <div>Training Examples</div>
                    </div>
                </div>
                
                <div class="training-section" id="training-section">
                    <h3>🤖 Model Training</h3>
                    <div class="training-status">
                        <div class="status-indicator status-ready" id="training-indicator"></div>
                        <span id="training-status-text">Ready for training</span>
                    </div>
                    <div style="display: flex; gap: 10px;">
                        <button class="btn btn-train" onclick="startTraining()">Start Training</button>
                        <button class="btn" onclick="loadFeedbackStats()" style="background: #64748b; color: white;">Refresh Stats</button>
                    </div>
                    <div id="training-progress" style="display: none; margin-top: 15px;">
                        <div style="background: #e5e7eb; border-radius: 10px; overflow: hidden;">
                            <div id="progress-bar" style="background: #6366f1; height: 20px; width: 0%; transition: width 0.3s;"></div>
                        </div>
                        <p id="progress-text" style="text-align: center; margin-top: 10px;">Preparing training data...</p>
                    </div>
                </div>
                
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h2>🔍 Review Detected Tricks</h2>
                    <div>
                        <select id="filter-confidence" onchange="loadTricks()">
                            <option value="">All Confidence Levels</option>
                            <option value="high">High Confidence (>80%)</option>
                            <option value="medium">Medium Confidence (60-80%)</option>
                            <option value="low">Low Confidence (<60%)</option>
                        </select>
                    </div>
                </div>
                
                <div id="tricks-container" class="loading">
                    Loading tricks...
                </div>
                
                <div class="pagination" id="pagination" style="display: none;"></div>
            </div>
            
            <script>
                let currentPage = 0;
                const pageSize = 10;
                let allTricks = [];
                
                // Load initial data
                document.addEventListener('DOMContentLoaded', function() {
                    loadTricks();
                    loadFeedbackStats();
                });
                
                async function loadTricks() {
                    const confidence = document.getElementById('filter-confidence').value;
                    const container = document.getElementById('tricks-container');
                    
                    try {
                        container.innerHTML = '<div class="loading">Loading tricks...</div>';
                        
                        let url = '/api/v1/tricks/?limit=1000';
                        const response = await fetch(url);
                        const tricks = await response.json();
                        
                        // Filter by confidence if selected
                        allTricks = tricks;
                        if (confidence) {
                            allTricks = tricks.filter(trick => {
                                const conf = trick.confidence || 0;
                                if (confidence === 'high') return conf > 0.8;
                                if (confidence === 'medium') return conf >= 0.6 && conf <= 0.8;
                                if (confidence === 'low') return conf < 0.6;
                                return true;
                            });
                        }
                        
                        currentPage = 0;
                        renderTricks();
                        
                    } catch (error) {
                        container.innerHTML = '<div style="text-align: center; color: #ef4444;">Error loading tricks: ' + error.message + '</div>';
                    }
                }
                
                function renderTricks() {
                    const container = document.getElementById('tricks-container');
                    const startIndex = currentPage * pageSize;
                    const endIndex = startIndex + pageSize;
                    const pageData = allTricks.slice(startIndex, endIndex);
                    
                    if (pageData.length === 0) {
                        container.innerHTML = '<div style="text-align: center; color: #666;">No tricks found.</div>';
                        return;
                    }
                    
                    const html = pageData.map(trick => `
                        <div class="trick-card" id="trick-${trick.id}">
                            <div class="trick-header">
                                <div class="trick-title">${trick.name}</div>
                                <div class="confidence-badge ${getConfidenceClass(trick.confidence)}">
                                    ${Math.round((trick.confidence || 0) * 100)}% confidence
                                </div>
                            </div>
                            <div class="trick-details">
                                <div style="margin-bottom: 10px;">
                                    <span class="effect-type">${trick.effect_type}</span>
                                    <span class="effect-type">${trick.difficulty}</span>
                                </div>
                                <p><strong>Description:</strong> ${trick.description.substring(0, 200)}${trick.description.length > 200 ? '...' : ''}</p>
                                ${trick.method ? `<p><strong>Method:</strong> ${trick.method.substring(0, 150)}${trick.method.length > 150 ? '...' : ''}</p>` : ''}
                                ${trick.props.length > 0 ? `<p><strong>Props:</strong> ${trick.props.join(', ')}</p>` : ''}
                                <p><strong>Book:</strong> ${trick.book_title} by ${trick.book_author}</p>
                            </div>
                            <div class="feedback-section">
                                <div class="feedback-buttons">
                                    <button class="btn btn-correct" onclick="markCorrect('${trick.id}')">✓ Correct</button>
                                    <button class="btn btn-incorrect" onclick="showFeedbackForm('${trick.id}')">✗ Incorrect</button>
                                </div>
                                <div id="feedback-form-${trick.id}" class="feedback-form">
                                    <div class="form-group">
                                        <label class="form-label">Suggested Name:</label>
                                        <input type="text" class="form-input" id="suggested-name-${trick.id}" placeholder="What should this trick be called?">
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">Suggested Description:</label>
                                        <textarea class="form-textarea" id="suggested-description-${trick.id}" placeholder="Better description of this trick..."></textarea>
                                    </div>
                                    <div class="form-group">
                                        <label class="form-label">Notes:</label>
                                        <textarea class="form-textarea" id="notes-${trick.id}" placeholder="Why is this detection incorrect?"></textarea>
                                    </div>
                                    <div style="display: flex; gap: 10px;">
                                        <button class="btn btn-incorrect" onclick="submitFeedback('${trick.id}', false)">Submit Correction</button>
                                        <button class="btn" onclick="hideFeedbackForm('${trick.id}')" style="background: #6b7280; color: white;">Cancel</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `).join('');
                    
                    container.innerHTML = html;
                    renderPagination();
                }
                
                function getConfidenceClass(confidence) {
                    if (!confidence) return 'confidence-low';
                    if (confidence > 0.8) return 'confidence-high';
                    if (confidence > 0.6) return 'confidence-medium';
                    return 'confidence-low';
                }
                
                function renderPagination() {
                    const totalPages = Math.ceil(allTricks.length / pageSize);
                    const pagination = document.getElementById('pagination');
                    
                    if (totalPages <= 1) {
                        pagination.style.display = 'none';
                        return;
                    }
                    
                    pagination.style.display = 'block';
                    
                    let html = '';
                    for (let i = 0; i < totalPages; i++) {
                        html += `<button ${i === currentPage ? 'class="active"' : ''} onclick="goToPage(${i})">${i + 1}</button>`;
                    }
                    
                    pagination.innerHTML = html;
                }
                
                function goToPage(page) {
                    currentPage = page;
                    renderTricks();
                }
                
                async function markCorrect(trickId) {
                    try {
                        const response = await fetch('/api/v1/review/feedback', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                trick_id: trickId,
                                is_correct: true
                            })
                        });
                        
                        if (response.ok) {
                            const card = document.getElementById(`trick-${trickId}`);
                            card.style.background = '#f0fdf4';
                            card.style.borderColor = '#10b981';
                            loadFeedbackStats();
                        }
                    } catch (error) {
                        alert('Error submitting feedback: ' + error.message);
                    }
                }
                
                function showFeedbackForm(trickId) {
                    document.getElementById(`feedback-form-${trickId}`).style.display = 'block';
                }
                
                function hideFeedbackForm(trickId) {
                    document.getElementById(`feedback-form-${trickId}`).style.display = 'none';
                }
                
                async function submitFeedback(trickId, isCorrect) {
                    try {
                        const feedback = {
                            trick_id: trickId,
                            is_correct: isCorrect
                        };
                        
                        if (!isCorrect) {
                            feedback.suggested_name = document.getElementById(`suggested-name-${trickId}`).value;
                            feedback.suggested_description = document.getElementById(`suggested-description-${trickId}`).value;
                            feedback.user_notes = document.getElementById(`notes-${trickId}`).value;
                        }
                        
                        const response = await fetch('/api/v1/review/feedback', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(feedback)
                        });
                        
                        if (response.ok) {
                            const card = document.getElementById(`trick-${trickId}`);
                            card.style.background = isCorrect ? '#f0fdf4' : '#fef2f2';
                            card.style.borderColor = isCorrect ? '#10b981' : '#ef4444';
                            hideFeedbackForm(trickId);
                            loadFeedbackStats();
                        }
                    } catch (error) {
                        alert('Error submitting feedback: ' + error.message);
                    }
                }
                
                async function loadFeedbackStats() {
                    try {
                        const response = await fetch('/api/v1/review/stats');
                        const stats = await response.json();
                        
                        document.getElementById('total-tricks').textContent = stats.total_tricks || 0;
                        document.getElementById('pending-review').textContent = stats.pending_review || 0;
                        document.getElementById('accuracy').textContent = (stats.accuracy * 100).toFixed(1) + '%';
                        document.getElementById('training-examples').textContent = stats.training_examples || 0;
                        
                    } catch (error) {
                        console.error('Error loading stats:', error);
                    }
                }
                
                async function startTraining() {
                    try {
                        const indicator = document.getElementById('training-indicator');
                        const statusText = document.getElementById('training-status-text');
                        const progress = document.getElementById('training-progress');
                        
                        indicator.className = 'status-indicator status-training';
                        statusText.textContent = 'Training in progress...';
                        progress.style.display = 'block';
                        
                        const response = await fetch('/api/v1/review/train', {
                            method: 'POST'
                        });
                        
                        if (response.ok) {
                            // Poll for training status
                            pollTrainingStatus();
                        } else {
                            throw new Error('Failed to start training');
                        }
                        
                    } catch (error) {
                        const indicator = document.getElementById('training-indicator');
                        const statusText = document.getElementById('training-status-text');
                        
                        indicator.className = 'status-indicator status-error';
                        statusText.textContent = 'Training failed: ' + error.message;
                    }
                }
                
                async function pollTrainingStatus() {
                    try {
                        const response = await fetch('/api/v1/review/training-status');
                        const status = await response.json();
                        
                        const progressBar = document.getElementById('progress-bar');
                        const progressText = document.getElementById('progress-text');
                        const indicator = document.getElementById('training-indicator');
                        const statusText = document.getElementById('training-status-text');
                        
                        if (status.status === 'completed') {
                            progressBar.style.width = '100%';
                            progressText.textContent = 'Training completed successfully!';
                            indicator.className = 'status-indicator status-ready';
                            statusText.textContent = 'Model updated and ready';
                            
                            setTimeout(() => {
                                document.getElementById('training-progress').style.display = 'none';
                            }, 3000);
                            
                        } else if (status.status === 'error') {
                            indicator.className = 'status-indicator status-error';
                            statusText.textContent = 'Training failed';
                            progressText.textContent = 'Error: ' + status.message;
                            
                        } else {
                            // Still training
                            const progress = status.progress || 0;
                            progressBar.style.width = progress + '%';
                            progressText.textContent = status.message || 'Training in progress...';
                            
                            setTimeout(pollTrainingStatus, 2000);
                        }
                        
                    } catch (error) {
                        console.error('Error polling training status:', error);
                    }
                }
            </script>
        </body>
        </html>
        """
        return html_content
    
    @router.post("/feedback")
    async def submit_feedback(feedback: FeedbackSchema):
        """Submit user feedback for a trick detection."""
        try:
            feedback_data = FeedbackData(
                trick_id=feedback.trick_id,
                is_correct=feedback.is_correct,
                user_notes=feedback.user_notes,
                suggested_name=feedback.suggested_name,
                suggested_description=feedback.suggested_description
            )
            
            await training_data_generator.add_feedback(feedback_data)
            
            return {"status": "success", "message": "Feedback recorded successfully"}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error recording feedback: {str(e)}")
    
    @router.get("/stats")
    async def get_review_stats():
        """Get statistics about the review process."""
        try:
            feedback_stats = await training_data_generator.get_feedback_stats()
            
            # Get total tricks count
            all_tricks = await trick_repository.find_all()
            total_tricks = len(all_tricks)
            
            # Calculate pending review (tricks without feedback)
            pending_review = max(0, total_tricks - feedback_stats['total_feedback'])
            
            return {
                "total_tricks": total_tricks,
                "pending_review": pending_review,
                "accuracy": feedback_stats['accuracy'],
                "training_examples": feedback_stats['total_feedback'],
                "correct_detections": feedback_stats['correct_detections'],
                "incorrect_detections": feedback_stats['incorrect_detections']
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")
    
    @router.get("/pending")
    async def get_pending_reviews():
        """Get tricks that need review."""
        try:
            # Get all tricks that haven't been reviewed yet
            all_tricks = await trick_repository.find_all()
            
            # Filter for tricks that need review (you might want to add a "reviewed" field to the Trick entity)
            # For now, return all tricks with confidence < 0.8 as pending review
            pending_tricks = [
                {
                    "id": str(trick.id.value),
                    "name": str(trick.name),
                    "description": trick.description,
                    "confidence": float(trick.confidence.value),
                    "source_document": str(trick.book_id.value),  # You might want to get the actual book title
                    "page_number": trick.page_range.start if trick.page_range else 1,
                    "effect_type": str(trick.effect_type.value),
                    "keywords": [],  # Add if you have keywords stored
                    "status": "pending"
                }
                for trick in all_tricks 
                if trick.confidence.value < 0.8
            ]
            
            return pending_tricks[:20]  # Limit to 20 for now
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting pending reviews: {str(e)}")
    
    @router.post("/tricks/{trick_id}/review")
    async def update_trick_review(trick_id: str, approved: bool, reviewed: bool = True):
        """Update a trick's review status."""
        try:
            trick_uuid = UUID(trick_id)
            
            # Here you would update the trick's review status
            # For now, we'll just return success
            # In a real implementation, you'd add review fields to the Trick entity
            
            return {
                "status": "success",
                "message": f"Trick {trick_id} {'approved' if approved else 'rejected'}"
            }
            
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid trick ID format")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error updating review: {str(e)}")
    
    @router.post("/train")
    async def start_model_training(background_tasks: BackgroundTasks):
        """Start model training based on user feedback."""
        try:
            # Start training in background
            async def train_model():
                try:
                    # Generate training examples
                    training_examples = await training_data_generator.generate_training_examples()
                    
                    if len(training_examples) < 10:
                        raise ValueError("Need at least 10 training examples to start training")
                    
                    # Fine-tune the model
                    model_path = await model_fine_tuner.fine_tune_model(training_examples)
                    
                    # Switch to the new model
                    await adaptive_detector.switch_to_fine_tuned_model(model_path)
                    
                except Exception as e:
                    # Log error - in production you'd want proper error handling
                    print(f"Training error: {str(e)}")
            
            background_tasks.add_task(train_model)
            
            return {
                "status": "started",
                "message": "Model training started in background"
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error starting training: {str(e)}")
    
    @router.get("/training-status")
    async def get_training_status():
        """Get current training status."""
        # This is a simplified implementation
        # In production, you'd track training state in database/cache
        try:
            model_info = model_fine_tuner.get_model_info()
            
            return {
                "status": "ready",  # Could be: ready, training, completed, error
                "progress": 100,
                "message": "Ready for training",
                "model_info": model_info
            }
            
        except Exception as e:
            return {
                "status": "error",
                "progress": 0,
                "message": f"Error: {str(e)}"
            }
    
    @router.get("/model-info", response_model=ModelInfoSchema)
    async def get_model_info():
        """Get information about the current model."""
        try:
            fine_tuned_info = model_fine_tuner.get_model_info()
            current_model_info = adaptive_detector.get_current_model_info()
            
            return ModelInfoSchema(
                base_model=current_model_info["base_model"],
                is_fine_tuned=current_model_info["is_fine_tuned"],
                fine_tuned_path=current_model_info.get("fine_tuned_model"),
                model_exists=fine_tuned_info["exists"],
                training_available=True
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error getting model info: {str(e)}")
    
    return router
