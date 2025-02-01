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

    // Video Preview Handling
    const videoPreview = document.getElementById('videoPreview');
    const video = videoPreview.querySelector('video');
    const expandBtn = document.getElementById('expandBtn');
    const previewState = videoPreview.querySelector('.preview-state');
    const processingState = videoPreview.querySelector('.processing-state');

    // Toggle fullscreen
    function toggleFullScreen() {
        if (!document.fullscreenElement) {
            videoPreview.requestFullscreen().catch(err => {
                console.log(`Error attempting to enable fullscreen: ${err.message}`);
            });
        } else {
            document.exitFullscreen();
        }
    }

    // Handle expand button click
    expandBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        toggleFullScreen();
    });

    // Handle video preview click
    videoPreview.addEventListener('click', () => {
        toggleFullScreen();
    });

    // Handle fullscreen change
    document.addEventListener('fullscreenchange', () => {
        if (document.fullscreenElement) {
            videoPreview.classList.add('fullscreen');
            video.controls = true;
        } else {
            videoPreview.classList.remove('fullscreen');
            video.controls = false;
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
        const languages = [];
        document.querySelectorAll('[data-lang].active').forEach(lang => {
            languages.push(lang.dataset.lang);
        });
        languages.forEach(lang => formData.append('languages[]', lang));
        
        // Get selected output formats
        const outputFormats = [];
        document.querySelectorAll('[data-output].active').forEach(output => {
            outputFormats.push(output.dataset.output);
        });
        outputFormats.forEach(format => formData.append('outputFormats[]', format));
        
        // Get animation style
        const style = document.querySelector('[data-style].active').dataset.style;
        formData.append('style', style);
        
        // Get CC preference
        const ccType = document.querySelector('[data-cc].active').dataset.cc;
        formData.append('ccType', ccType);
        
        if (ccType === 'upload') {
            const srtFile = document.getElementById('srtFile').files[0];
            if (srtFile) {
                formData.append('srtFile', srtFile);
            }
        }
        
        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok) {
                // Update video source with the new URL
                video.src = result.data.video_url;
                video.load(); // Reload the video
                video.play(); // Start playing
                
                // Hide processing state and show preview
                processingState.style.display = 'none';
                previewState.classList.remove('hidden');
            } else {
                // Handle error
                console.error('Generation failed:', result.error);
                processingState.style.display = 'none';
                previewState.classList.remove('hidden');
            }
        } catch (error) {
            console.error('Error during generation:', error);
            processingState.style.display = 'none';
            previewState.classList.remove('hidden');
        }
    });
});
