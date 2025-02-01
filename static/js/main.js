document.addEventListener('DOMContentLoaded', function() {
    // Initialize style selection
    const styleOptions = document.querySelectorAll('.style-option');
    styleOptions.forEach(option => {
        option.addEventListener('click', function() {
            styleOptions.forEach(opt => opt.classList.remove('selected'));
            this.classList.add('selected');
            this.querySelector('input[type="radio"]').checked = true;
        });
    });
    const form = document.getElementById('newsForm');
    const progressArea = document.getElementById('progressArea');
    const progressBar = document.querySelector('.progress-bar');
    const statusText = document.getElementById('statusText');
    const generateBtn = document.getElementById('generateBtn');
    const resultsArea = document.getElementById('results');
    
    // Add animation classes to elements as they appear
    const animateElement = (element, animation) => {
        element.classList.add('animate__animated', animation);
        element.addEventListener('animationend', () => {
            element.classList.remove('animate__animated', animation);
        });
    };

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Get selected languages
        const selectedLanguages = Array.from(document.querySelectorAll('input[type="checkbox"]:checked'))
            .map(cb => cb.value);
            
        if (selectedLanguages.length === 0) {
            alert('Please select at least one target language');
            return;
        }

        const articleText = document.getElementById('articleText').value.trim();
        if (!articleText) {
            alert('Please enter the article text');
            return;
        }

        // Show progress area and disable submit button
        progressArea.classList.remove('d-none');
        generateBtn.disabled = true;
        resultsArea.innerHTML = '';
        
        try {
            for (const lang of selectedLanguages) {
                // Update progress
                const progress = (selectedLanguages.indexOf(lang) / selectedLanguages.length) * 100;
                progressBar.style.width = `${progress}%`;
                statusText.textContent = `Processing ${lang.toUpperCase()}...`;

                // Step 1: Generate summary
                const summaryResponse = await fetch('/api/summarize', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        text: articleText,
                        target_language: lang
                    })
                });

                if (!summaryResponse.ok) throw new Error(`Summary generation failed for ${lang}`);
                const summaryData = await summaryResponse.json();

                // Step 2: Generate speech
                const speechResponse = await fetch('/api/generate-speech', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        text: summaryData.summary,
                        language_code: lang
                    })
                });

                if (!speechResponse.ok) throw new Error(`Speech generation failed for ${lang}`);
                const speechData = await speechResponse.json();

                // Step 3: Generate video
                const videoResponse = await fetch('/api/generate-video', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        audio_path: speechData.audio_path
                    })
                });

                if (!videoResponse.ok) throw new Error(`Video generation failed for ${lang}`);
                const videoData = await videoResponse.json();

                // Add results to the page with animation
                const resultCard = document.createElement('div');
                resultCard.className = 'result-card';
                resultCard.innerHTML = `
                    <h4>${getLangName(lang)} Version</h4>
                    <div class="summary-text">
                        <strong>Summary:</strong>
                        <p class="summary-content">${summaryData.summary}</p>
                    </div>
                    <div class="video-container">
                        <strong>Generated Video:</strong>
                        <div class="video-status">
                            <span class="status-icon">✓</span>
                            <span>Video generated successfully!</span>
                        </div>
                        <div class="audio-preview mt-3">
                            <p class="audio-label">Preview Audio:</p>
                            <audio controls src="/uploads/${speechData.audio_path}" class="custom-audio"></audio>
                        </div>
                        <div class="video-info mt-2">
                            <small class="text-muted">Video ID: ${videoData.talk_id}</small>
                        </div>
                    </div>
                `;
                resultsArea.appendChild(resultCard);
                animateElement(resultCard, 'animate__fadeInUp');
            }

            // Complete progress bar with success animation
            progressBar.style.width = '100%';
            statusText.textContent = 'All content generated successfully!';
            animateElement(statusText, 'animate__pulse');
            
            // Show success message
            const successMessage = document.createElement('div');
            successMessage.className = 'alert alert-success mt-3 animate__animated animate__fadeIn';
            successMessage.innerHTML = `
                <strong>Success!</strong> Your content has been generated in ${selectedLanguages.length} language${selectedLanguages.length > 1 ? 's' : ''}.
            `;
            progressArea.appendChild(successMessage);
            
        } catch (error) {
            console.error('Error:', error);
            statusText.textContent = `Error: ${error.message}`;
            progressBar.classList.add('bg-danger');
        } finally {
            generateBtn.disabled = false;
        }
    });

    function getLangName(code) {
        const langMap = {
            'en': 'English',
            'es': 'Spanish',
            'hmn': 'Hmong',
            'so': 'Somali'
        };
        return langMap[code] || code.toUpperCase();
    }
});
