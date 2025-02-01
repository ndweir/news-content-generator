document.addEventListener('DOMContentLoaded', function() {
    // Initialize option groups
    function initOptionGroup(selector, allowMultiple = false) {
        const group = document.querySelector(selector);
        if (!group) return;

        group.addEventListener('click', (e) => {
            const chip = e.target.closest('.option-chip');
            if (!chip) return;

            if (allowMultiple) {
                chip.classList.toggle('active');
            } else {
                group.querySelectorAll('.option-chip').forEach(c => c.classList.remove('active'));
                chip.classList.add('active');
            }
        });

        return group;
    }
    // Initialize all option groups
    const form = document.getElementById('newsForm');
    const inputGroup = initOptionGroup('.option-group:has([data-input])');
    const languageGroup = initOptionGroup('.option-group:has([data-lang])', true);
    const outputGroup = initOptionGroup('.option-group:has([data-output])', true);
    const styleGroup = initOptionGroup('.option-group:has([data-style])');
    const ccGroup = initOptionGroup('.option-group:has([data-cc])');

    // Handle input type changes
    inputGroup.addEventListener('click', (e) => {
        const chip = e.target.closest('.option-chip');
        if (!chip) return;

        const inputType = chip.dataset.input;
        document.querySelectorAll('.input-section').forEach(section => {
            section.style.display = section.id === `${inputType}Input` ? 'block' : 'none';
        });

        // Show/hide voice style based on input type
        const voiceStyleSection = document.querySelector('.voice-style-section');
        voiceStyleSection.style.display = inputType === 'text' ? 'block' : 'none';
    });

    // Handle output format changes
    outputGroup.addEventListener('click', () => {
        const hasVideoOutput = outputGroup.querySelector('[data-output="video"].active');
        const ccSection = document.querySelector('.input-group:has([data-cc])');
        ccSection.style.display = hasVideoOutput ? 'block' : 'none';
    });

    // Handle closed captions selection
    ccGroup.addEventListener('click', (e) => {
        const chip = e.target.closest('.option-chip');
        if (!chip) return;

        const srtUpload = document.getElementById('srtUpload');
        srtUpload.style.display = chip.dataset.cc === 'upload' ? 'block' : 'none';
    });
    
    // Handle file uploads
    function initFileUpload(type) {
        const dropZone = document.getElementById(`${type}DropZone`);
        const fileInput = document.getElementById(`${type}File`);
        if (!dropZone || !fileInput) return;

        const handleFile = (file) => {
            if (!file) return;
            
            const icon = dropZone.querySelector('i');
            const title = dropZone.querySelector('h5');
            const text = dropZone.querySelector('p');
            
            icon.className = 'bi bi-check-circle';
            title.textContent = file.name;
            text.textContent = `${(file.size / 1024 / 1024).toFixed(1)} MB`;
            
            dropZone.classList.add('file-selected');
        };

        // Click to upload
        dropZone.addEventListener('click', () => fileInput.click());

        // Drag and drop
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('drag-over');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            const file = e.dataTransfer.files[0];
            if (file) {
                fileInput.files = e.dataTransfer.files;
                handleFile(file);
            }
        });

        // File input change
        fileInput.addEventListener('change', () => {
            const file = fileInput.files[0];
            if (file) handleFile(file);
        });
    }

    // Initialize all file uploads
    ['audio', 'video', 'srt'].forEach(initFileUpload);
    const videoPlayer = document.getElementById('videoPlayer');
    const progressBar = videoPlayer.querySelector('.progress-bar');
    const submitBtn = form.querySelector('button[type="submit"]');
    
    // Animation style configuration
    const styleConfig = {
        avatar: {
            color: '#4CAF50',
            icon: '👤',
            previewBg: 'linear-gradient(45deg, #4CAF50 10%, #2E7D32 90%)'
        },
        cartoon: {
            color: '#FF9800',
            icon: '😊',
            previewBg: 'linear-gradient(45deg, #FF9800 10%, #F57C00 90%)'
        },
        anime: {
            color: '#E91E63',
            icon: '⭐',
            previewBg: 'linear-gradient(45deg, #E91E63 10%, #C2185B 90%)'
        },
        claymation: {
            color: '#9C27B0',
            icon: '🎨',
            previewBg: 'linear-gradient(45deg, #9C27B0 10%, #7B1FA2 90%)'
        }
    };

    // Handle animation style selection
    const animationStyleGroup = document.querySelector('.animation-styles');
    let currentStyle = 'avatar';

    animationStyleGroup.addEventListener('click', (e) => {
        const chip = e.target.closest('.option-chip');
        if (!chip) return;

        const style = chip.dataset.style;
        currentStyle = style;
        updatePreviewStyle(style);

        // Show/hide corresponding character group
        document.querySelectorAll('.character-group').forEach(group => {
            group.style.display = group.dataset.style === style ? 'grid' : 'none';
        });
    });

    // Handle character selection
    const characterGrid = document.querySelector('.character-grid');
    characterGrid.addEventListener('click', (e) => {
        const option = e.target.closest('.character-option');
        if (!option) return;

        // Update active state within the same style group
        const group = option.closest('.character-group');
        group.querySelectorAll('.character-option').forEach(opt => {
            opt.classList.remove('active');
        });
        option.classList.add('active');
    });

    function updatePreviewStyle(style) {
        const config = styleConfig[style];
        if (!config) return;

        const preview = document.querySelector('.video-preview');
        if (preview) {
            preview.style.background = config.previewBg;
        }

        const icon = document.querySelector('.style-icon');
        if (icon) {
            icon.textContent = config.icon;
        }
    }

    // Video Preview Fullscreen
    const videoPreview = document.getElementById('videoPreview');
    const expandBtn = document.getElementById('expandBtn');
    let isFullscreen = false;

    function toggleFullscreen() {
        isFullscreen = !isFullscreen;
        if (isFullscreen) {
            videoPreview.classList.add('fullscreen');
            expandBtn.querySelector('i').className = 'bi bi-fullscreen-exit';
            document.body.style.overflow = 'hidden';
        } else {
            videoPreview.classList.remove('fullscreen');
            expandBtn.querySelector('i').className = 'bi bi-arrows-fullscreen';
            document.body.style.overflow = '';
        }
    }

    expandBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleFullscreen();
    });

    videoPreview.addEventListener('click', () => {
        toggleFullscreen();
    });

    // Close fullscreen on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && isFullscreen) {
            toggleFullscreen();
        }
    });

    // Form submission and video generation
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData();
        
        // Get input type and content
        const inputType = inputGroup.querySelector('.active').dataset.input;
        formData.append('inputType', inputType);
        
        // Show processing state
        const videoPreview = document.getElementById('videoPreview');
        const previewState = videoPreview.querySelector('.preview-state');
        const processingState = videoPreview.querySelector('.processing-state');
        
        previewState.classList.add('hidden');
        processingState.style.display = 'flex';
        
        if (inputType === 'text') {
            formData.append('text', document.getElementById('articleText').value);
        } else {
            const file = document.getElementById(`${inputType}File`).files[0];
            if (file) {
                formData.append(inputType, file);
            }
        }
        
        // Get selected languages
        const languages = Array.from(document.querySelectorAll('.language-selector .active'))
            .map(chip => chip.dataset.lang);
        languages.forEach(lang => formData.append('languages[]', lang));
        
        // Get selected output formats
        const outputFormats = Array.from(document.querySelectorAll('.output-selector .active'))
            .map(chip => chip.dataset.output);
        outputFormats.forEach(format => formData.append('outputFormats[]', format));
        
        // Get style
        const style = document.querySelector('.style-selector .active').dataset.style;
        formData.append('style', style);
        
        // Handle closed captions if video output is selected
        if (outputFormats.includes('video')) {
            const ccType = document.querySelector('.cc-selector .active').dataset.cc;
            formData.append('ccType', ccType);
            
            if (ccType === 'upload') {
                languages.forEach(lang => {
                    const ccFile = document.getElementById('srtFile').files[0];
                    if (ccFile) {
                        formData.append(`cc_file_${lang}`, ccFile);
                    }
                });
            }
        }
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


