document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('videoForm');
    const videoPlayer = document.getElementById('videoPlayer');
    const progressBar = videoPlayer.querySelector('.progress-bar');
    const submitBtn = form.querySelector('button[type="submit"]');
    
    // Style configuration
    const styleColors = {
        ruff: '#FFD700',
        felix: '#FF69B4',
        cronkite: '#4169E1',
        wordgirl: '#32CD32',
        anime: '#FF4500'
    };

    const styleIcons = {
        ruff: '🐶',
        felix: '🐱',
        cronkite: '🎙️',
        wordgirl: '📚',
        anime: '🎨'
    };

    // Style selector functionality
    const styleOptions = document.querySelectorAll('.style-option');
    let currentStyle = 'ruff';

    styleOptions.forEach(option => {
        option.addEventListener('click', () => {
            styleOptions.forEach(opt => opt.classList.remove('active'));
            option.classList.add('active');
            currentStyle = option.dataset.style;
            updatePlayerStyle(currentStyle);
        });
    });

    function updatePlayerStyle(style) {
        const icon = videoPlayer.querySelector('.style-icon');
        icon.textContent = styleIcons[style];
        videoPlayer.style.background = `linear-gradient(45deg, ${styleColors[style]}22, ${styleColors[style]}11)`;
        progressBar.style.background = styleColors[style];
    }

    // Form submission and video generation
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const articleText = document.getElementById('articleText').value.trim();
        if (!articleText) {
            alert('Please enter some text');
            return;
        }

        submitBtn.disabled = true;
        progressBar.style.width = '0%';
        videoPlayer.classList.add('generating');
        
        try {
            // Generate summary
            progressBar.style.width = '30%';
            const summaryResponse = await fetch('/api/summarize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: articleText,
                    target_language: 'en',
                    style: currentStyle
                })
            });

            if (!summaryResponse.ok) throw new Error('Summary generation failed');
            const summaryData = await summaryResponse.json();

            // Generate video
            progressBar.style.width = '60%';
            const videoResponse = await fetch('/api/generate-video', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: summaryData.summary,
                    style: currentStyle
                })
            });

            if (!videoResponse.ok) throw new Error('Video generation failed');
            const videoData = await videoResponse.json();

            // Update player with generated content
            videoPlayer.innerHTML = `
                <div class="style-icon" style="font-size: 48px">${styleIcons[currentStyle]}</div>
                <h3 class="mb-3" style="color: ${styleColors[currentStyle]}">${currentStyle.toUpperCase()} Style</h3>
                <div class="summary-text mb-4" style="font-size: 14px; padding: 0 20px;">
                    ${summaryData.summary}
                </div>
                <div class="video-controls mb-3">
                    <button class="btn btn-light btn-sm mx-1" onclick="window.location.reload()">🔄 New Video</button>
                </div>
                <div class="progress" style="width: 80%; height: 4px; background: rgba(255,255,255,0.2);">
                    <div class="progress-bar" role="progressbar" style="width: 100%; background: ${styleColors[currentStyle]}"></div>
                </div>
            `;

            // Start video animation
            videoPlayer.style.animation = 'pulse 2s infinite';

        } catch (error) {
            console.error('Error:', error);
            videoPlayer.innerHTML = `
                <div class="style-icon" style="font-size: 48px">⚠️</div>
                <h3 class="mb-3" style="color: #dc3545">Error</h3>
                <p class="mb-4">${error.message}</p>
                <button class="btn btn-light btn-sm" onclick="window.location.reload()">🔄 Try Again</button>
            `;
        } finally {
            submitBtn.disabled = false;
        }
    });
});


