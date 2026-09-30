/**
 * Smart Learning App - Enhanced JavaScript Features
 * - Timer with auto-submit
 * - Read Aloud functionality
 * - Progress tracking
 * - Answer validation
 */

// Timer function with visual warnings
function startTimer(duration, displayId, formId) {
    let timer = duration * 60;
    const display = document.getElementById(displayId);
    const timerElement = document.getElementById('timer');
    const form = document.getElementById(formId);

    const interval = setInterval(function() {
        const minutes = parseInt(timer / 60, 10);
        const seconds = parseInt(timer % 60, 10);
        
        const minutesStr = minutes < 10 ? "0" + minutes : minutes;
        const secondsStr = seconds < 10 ? "0" + seconds : seconds;
        
        display.textContent = minutesStr + ":" + secondsStr;

        // Visual warnings
        if (timer <= 300 && timer > 60) { // Last 5 minutes
            timerElement.style.background = 'linear-gradient(135deg, #ffc107 0%, #ff9800 100%)';
        } else if (timer <= 60) { // Last minute
            timerElement.style.background = 'linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)';
            timerElement.style.animation = 'pulse 0.5s infinite';
        }

        if (--timer < 0) {
            clearInterval(interval);
            alert('⏰ Time\'s up! Submitting your exam automatically...');
            if (form) {
                form.submit();
            }
        }
    }, 1000);
}

// Read Aloud functionality with enhanced features
function readAloud() {
    // Cancel any ongoing speech
    speechSynthesis.cancel();
    
    const questions = [];
    
    // Get MCQ questions
    const mcqCards = document.querySelectorAll('.mcq-card');
    mcqCards.forEach((card, index) => {
        const questionText = card.querySelector('.question-text');
        if (questionText) {
            const difficulty = card.querySelector('.difficulty-badge')?.textContent || 'medium';
            questions.push(`Multiple choice question ${index + 1}. Difficulty: ${difficulty}. ${questionText.textContent}`);
            
            // Read options
            const options = card.querySelectorAll('.option-text');
            options.forEach((opt, optIndex) => {
                questions.push(`Option ${String.fromCharCode(65 + optIndex)}. ${opt.textContent}`);
            });
        }
    });
    
    // Get Descriptive questions
    const descCards = document.querySelectorAll('.desc-card');
    descCards.forEach((card, index) => {
        const questionText = card.querySelector('.question-text');
        if (questionText) {
            const difficulty = card.querySelector('.difficulty-badge')?.textContent || 'medium';
            questions.push(`Descriptive question ${index + 1}. Difficulty: ${difficulty}. ${questionText.textContent}`);
        }
    });
    
    if (questions.length === 0) {
        alert('No questions found to read!');
        return;
    }
    
    // Create and speak
    const text = questions.join('. ');
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9; // Slightly slower for clarity
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    
    // Visual feedback
    const readButton = event?.target;
    if (readButton) {
        readButton.textContent = '🔊 Reading...';
        readButton.disabled = true;
    }
    
    utterance.onend = function() {
        if (readButton) {
            readButton.textContent = '🔊 Read Questions Aloud';
            readButton.disabled = false;
        }
    };
    
    utterance.onerror = function() {
        alert('⚠️ Text-to-speech is not available in your browser.');
        if (readButton) {
            readButton.textContent = '🔊 Read Questions Aloud';
            readButton.disabled = false;
        }
    };
    
    speechSynthesis.speak(utterance);
}

// Stop reading
function stopReading() {
    speechSynthesis.cancel();
}

// Highlight unanswered questions
function highlightUnanswered() {
    const cards = document.querySelectorAll('.question-card');
    let unansweredCount = 0;
    
    cards.forEach(card => {
        if (card.dataset.answered === 'false') {
            card.classList.add('unanswered-highlight');
            unansweredCount++;
            
            // Remove highlight after animation
            setTimeout(() => {
                card.classList.remove('unanswered-highlight');
            }, 2000);
        }
    });
    
    if (unansweredCount === 0) {
        alert('✅ All questions have been answered!');
    } else {
        alert(`⚠️ You have ${unansweredCount} unanswered question(s)!`);
    }
}

// Scroll to next unanswered question
function scrollToNext() {
    const cards = document.querySelectorAll('.question-card');
    
    for (let card of cards) {
        if (card.dataset.answered === 'false') {
            card.scrollIntoView({ behavior: 'smooth', block: 'center' });
            card.classList.add('pulse-animation');
            
            setTimeout(() => {
                card.classList.remove('pulse-animation');
            }, 1000);
            
            return;
        }
    }
    
    alert('✅ All questions answered! Ready to submit.');
}

// Auto-save functionality (optional)
function autoSave() {
    const formData = new FormData(document.getElementById('examForm'));
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    localStorage.setItem('examProgress', JSON.stringify(data));
    console.log('Progress auto-saved');
}

// Restore saved progress
function restoreProgress() {
    const saved = localStorage.getItem('examProgress');
    
    if (saved && confirm('Restore your previous progress?')) {
        const data = JSON.parse(saved);
        
        for (let [key, value] of Object.entries(data)) {
            const input = document.querySelector(`[name="${key}"]`);
            
            if (input) {
                if (input.type === 'radio') {
                    const radio = document.querySelector(`[name="${key}"][value="${value}"]`);
                    if (radio) radio.checked = true;
                } else {
                    input.value = value;
                }
            }
        }
        
        // Update progress after restoring
        if (typeof updateProgress === 'function') {
            updateProgress();
        }
    }
}

// Clear saved progress on successful submit
function clearSavedProgress() {
    localStorage.removeItem('examProgress');
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + S to save progress
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        autoSave();
        alert('💾 Progress saved!');
    }
    
    // Ctrl/Cmd + Enter to submit (with confirmation)
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        if (typeof confirmSubmit === 'function') {
            confirmSubmit();
        }
    }
});

// Prevent accidental page close
window.addEventListener('beforeunload', function(e) {
    const form = document.getElementById('examForm');
    if (form) {
        e.preventDefault();
        e.returnValue = 'You have an exam in progress. Are you sure you want to leave?';
        return e.returnValue;
    }
});

// Initialize on page load
window.addEventListener('load', function() {
    // Check for saved progress
    if (document.getElementById('examForm')) {
        const hasSaved = localStorage.getItem('examProgress');
        if (hasSaved) {
            setTimeout(restoreProgress, 500);
        }
        
        // Auto-save every 30 seconds
        setInterval(autoSave, 30000);
    }
});

// Export functions for use in HTML
window.startTimer = startTimer;
window.readAloud = readAloud;
window.stopReading = stopReading;
window.highlightUnanswered = highlightUnanswered;
window.scrollToNext = scrollToNext;
