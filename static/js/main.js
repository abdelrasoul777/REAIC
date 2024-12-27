document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const messagesContainer = document.getElementById('chat-messages');
    const fileUpload = document.getElementById('file-upload');
    const uploadedFilesList = document.getElementById('uploaded-files');
    const loadingIndicator = document.getElementById('loading');

    // Handle chat form submission
    chatForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const message = chatInput.value.trim();
        if (!message) return;

        // Disable input while processing
        chatInput.disabled = true;
        
        // Add user message to chat
        appendMessage(message, 'user');
        chatInput.value = '';

        // Show loading indicator
        loadingIndicator.style.display = 'block';

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            
            // Add AI response to chat
            if (data.response) {
                appendMessage(data.response, 'ai');
            } else {
                appendMessage('I apologize, but I encountered an issue processing your request. Could you please rephrase your question?', 'ai');
            }
        } catch (error) {
            console.error('Error:', error);
            appendMessage('I apologize, but I encountered a technical issue. Please try again in a moment.', 'ai');
        } finally {
            loadingIndicator.style.display = 'none';
            chatInput.disabled = false;
            chatInput.focus();
        }
    });

    // Handle file upload
    fileUpload.addEventListener('change', async function(e) {
        const files = e.target.files;
        if (!files.length) return;

        // Validate files
        const validFiles = Array.from(files).filter(file => file.type === 'application/pdf');
        if (validFiles.length === 0) {
            appendMessage('Please select PDF files only.', 'ai');
            fileUpload.value = '';
            return;
        }

        loadingIndicator.style.display = 'block';
        appendMessage('Uploading and processing files...', 'ai');

        const formData = new FormData();
        for (let file of validFiles) {
            formData.append('files', file);
        }

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            if (data.success) {
                updateUploadedFilesList(data.files);
                appendMessage(`Files uploaded and processed: ${data.message}`, 'ai');
                
                // Refresh the documents list
                fetchProcessedDocuments();
            } else {
                appendMessage(`Error: ${data.error}`, 'ai');
            }
        } catch (error) {
            console.error('Error:', error);
            appendMessage('Sorry, there was an error uploading the files: ' + error.message, 'ai');
        } finally {
            loadingIndicator.style.display = 'none';
            fileUpload.value = ''; // Reset file input
        }
    });

    // Function to fetch processed documents
    async function fetchProcessedDocuments() {
        try {
            const response = await fetch('/documents');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            updateUploadedFilesList(data.files);
        } catch (error) {
            console.error('Error fetching documents:', error);
        }
    }

    // Initial fetch of processed documents
    fetchProcessedDocuments();

    function appendMessage(message, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        messageDiv.textContent = message;
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function updateUploadedFilesList(files) {
        uploadedFilesList.innerHTML = '';
        files.forEach(file => {
            const fileDiv = document.createElement('div');
            fileDiv.className = 'uploaded-file';
            fileDiv.textContent = file;
            uploadedFilesList.appendChild(fileDiv);
        });
    }
});
