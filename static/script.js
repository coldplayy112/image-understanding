const dropArea = document.getElementById('drop-area');
const fileElem = document.getElementById('fileElem');
const preview = document.getElementById('preview');
const resultDiv = document.getElementById('result');
const resultContent = document.getElementById('result-content');
const loadingDiv = document.getElementById('loading');

// Prevent default drag behaviors
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// Highlight drop area when item is dragged over it
['dragenter', 'dragover'].forEach(eventName => {
    dropArea.addEventListener(eventName, highlight, false);
});
['dragleave', 'drop'].forEach(eventName => {
    dropArea.addEventListener(eventName, unhighlight, false);
});

function highlight(e) {
    dropArea.classList.add('highlight');
}
function unhighlight(e) {
    dropArea.classList.remove('highlight');
}

// Handle dropped files
dropArea.addEventListener('drop', handleDrop, false);
function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
}

function handleFiles(files) {
    if (files.length > 0) {
        const file = files[0];
        previewFile(file);
        uploadFile(file);
    }
}

function previewFile(file) {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onloadend = function () {
        preview.src = reader.result;
        preview.style.display = 'block';
    }
}

function handleUrl() {
    const url = document.getElementById('urlInput').value;
    if (url) {
        preview.src = url;
        preview.style.display = 'block';
        uploadUrl(url);
    }
}

function uploadFile(file) {
    showLoading();
    const formData = new FormData();
    formData.append('file', file);

    fetch('/api/analyze', {
        method: 'POST',
        body: formData
    })
        .then(response => response.json())
        .then(data => displayResult(data))
        .catch(error => {
            console.error('Error:', error);
            displayResult({ error: "An error occurred during analysis." });
        });
}

function uploadUrl(url) {
    showLoading();
    fetch('/api/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url: url })
    })
        .then(response => response.json())
        .then(data => displayResult(data))
        .catch(error => {
            console.error('Error:', error);
            displayResult({ error: "An error occurred during analysis." });
        });
}

function showLoading() {
    resultDiv.classList.add('hidden');
    loadingDiv.classList.remove('hidden');
}

function displayResult(data) {
    loadingDiv.classList.add('hidden');
    resultDiv.classList.remove('hidden');

    if (data.error) {
        resultContent.innerText = "Error: " + data.error;
        resultContent.style.borderLeftColor = "#ff4b1f";
    } else if (data.result === "Blur") {
        resultContent.innerText = "⚠️ BLUR DETECTED\n\n" + (data.details || "");
        resultContent.style.borderLeftColor = "#ff4b1f";
    } else {
        resultContent.innerText = "✨ AI DESCRIPTION\n\n" + data.result;
        resultContent.style.borderLeftColor = "#2575fc";
    }
}
