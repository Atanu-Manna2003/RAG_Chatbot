class RAGFrontend {
    constructor() {
        this.apiBaseUrl = '/api/v1';
        this.currentFile = null;
        this.documents = [];
        this.showSources = false;
        
        this.initializeEventListeners();
        this.checkBackendConnection();
    }

    async checkBackendConnection() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/health`);
            if (response.ok) {
                console.log('Backend connection successful');
                this.loadDocuments();
            } else {
                this.showStatus('Backend is not responding properly', 'error');
            }
        } catch (error) {
            console.error('Backend connection failed:', error);
            this.showStatus('Cannot connect to backend server. Please make sure the server is running.', 'error');
        }
    }

    initializeEventListeners() {
        // File upload elements
        this.dropArea = document.getElementById('dropArea');
        this.fileInput = document.getElementById('fileInput');
        this.fileInfo = document.getElementById('fileInfo');
        this.fileName = document.getElementById('fileName');
        this.fileSize = document.getElementById('fileSize');
        this.uploadBtn = document.getElementById('uploadBtn');
        this.uploadStatus = document.getElementById('uploadStatus');

        // Chat elements
        this.chatMessages = document.getElementById('chatMessages');
        this.chatInput = document.getElementById('chatInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.showSourcesToggle = document.getElementById('showSourcesToggle');

        // Event listeners for file upload
        this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        this.uploadBtn.addEventListener('click', () => this.uploadFile());

        // Browse button click - trigger file input click
        const browseBtn = this.dropArea.querySelector('.browse-btn');
        browseBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.fileInput.click();
        });

        // Drag and drop events
        this.dropArea.addEventListener('dragover', (e) => this.handleDragOver(e));
        this.dropArea.addEventListener('dragleave', () => this.handleDragLeave());
        this.dropArea.addEventListener('drop', (e) => this.handleDrop(e));

        // Chat events
        this.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
        this.sendBtn.addEventListener('click', () => this.sendMessage());

        // Sources toggle
        this.showSourcesToggle.addEventListener('change', (e) => {
            this.showSources = e.target.checked;
            this.toggleAllSourcesVisibility();
        });
    }

    handleDragOver(e) {
        e.preventDefault();
        this.dropArea.style.borderColor = '#28a745';
        this.dropArea.style.background = '#f0fff4';
    }

    handleDragLeave() {
        this.dropArea.style.borderColor = '#3498db';
        this.dropArea.style.background = '';
    }

    handleDrop(e) {
        e.preventDefault();
        this.handleDragLeave();
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.fileInput.files = files;
            this.handleFileSelect({ target: this.fileInput });
        }
    }

    handleFileSelect(e) {
        const file = e.target.files[0];
        if (!file) return;

        // Validate file type by extension
        const fileExtension = file.name.toLowerCase().split('.').pop();
        const allowedExtensions = ['pdf', 'docx', 'doc', 'txt', 'md'];
        
        if (!allowedExtensions.includes(fileExtension)) {
            this.showStatus('Please select a valid file (PDF, DOCX, TXT, MD)', 'error');
            return;
        }

        // Validate file size (100MB)
        if (file.size > 100 * 1024 * 1024) {
            this.showStatus('File size must be less than 100MB', 'error');
            return;
        }

        this.currentFile = file;
        this.fileName.textContent = file.name;
        this.fileSize.textContent = this.formatFileSize(file.size);
        this.fileInfo.style.display = 'block';
        this.uploadBtn.disabled = false;

        this.showStatus('File selected and ready to upload', 'info');
    }

    async uploadFile() {
        if (!this.currentFile) return;

        this.uploadBtn.disabled = true;
        this.uploadBtn.innerHTML = '<div class="loading"></div> Uploading...';

        const formData = new FormData();
        formData.append('file', this.currentFile);

        try {
            const response = await fetch(`${this.apiBaseUrl}/documents/upload`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                let errorMessage = `Upload failed: ${response.status}`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorMessage;
                } catch (e) {
                    errorMessage = `${errorMessage} - ${response.statusText}`;
                }
                throw new Error(errorMessage);
            }

            const result = await response.json();
            this.showStatus('Document uploaded successfully! Processing in background...', 'success');
            
            // Clear current file
            this.currentFile = null;
            this.fileInput.value = '';
            this.fileInfo.style.display = 'none';
            this.uploadBtn.disabled = true;
            this.uploadBtn.innerHTML = '<i class="fas fa-upload"></i> Upload Document';

            // Wait a bit then reload documents to check processing status
            setTimeout(() => this.loadDocuments(), 2000);

        } catch (error) {
            console.error('Upload error:', error);
            this.showStatus(`Upload failed: ${error.message}`, 'error');
            this.uploadBtn.disabled = false;
            this.uploadBtn.innerHTML = '<i class="fas fa-upload"></i> Upload Document';
        }
    }

    async loadDocuments() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/documents`);
            if (response.ok) {
                this.documents = await response.json();
                this.renderDocumentsList();
                
                // Enable chat if we have processed documents
                const hasProcessedDocuments = this.documents.some(doc => doc.processed);
                if (hasProcessedDocuments) {
                    this.chatInput.disabled = false;
                    this.sendBtn.disabled = false;
                    this.chatInput.placeholder = "Ask a question about your documents...";
                } else if (this.documents.length > 0) {
                    this.chatInput.placeholder = "Documents are processing...";
                } else {
                    this.chatInput.placeholder = "Upload a document first...";
                }
            } else {
                throw new Error(`Failed to load documents: ${response.status}`);
            }
        } catch (error) {
            console.error('Error loading documents:', error);
            this.showStatus('Failed to load documents list', 'error');
        }
    }

    renderDocumentsList() {
        const container = document.getElementById('documentsList');
        container.innerHTML = '';

        if (this.documents.length === 0) {
            container.innerHTML = '<p>No documents uploaded yet.</p>';
            return;
        }

        this.documents.forEach(doc => {
            const docElement = document.createElement('div');
            docElement.className = 'document-item';
            docElement.innerHTML = `
                <div>
                    <strong>${doc.filename}</strong>
                    <br>
                    <small>${this.formatFileSize(doc.file_size)} • ${doc.processed ? '✅ Processed' : '⏳ Processing...'}</small>
                </div>
                <button class="delete-btn" onclick="frontend.deleteDocument('${doc.id}')">
                    <i class="fas fa-trash"></i>
                </button>
            `;
            container.appendChild(docElement);
        });
    }

    async deleteDocument(documentId) {
        if (!confirm('Are you sure you want to delete this document?')) return;

        try {
            const response = await fetch(`${this.apiBaseUrl}/documents/${documentId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showStatus('Document deleted successfully', 'success');
                await this.loadDocuments();
            } else {
                throw new Error('Delete failed');
            }
        } catch (error) {
            this.showStatus('Failed to delete document', 'error');
        }
    }

    async sendMessage() {
        const question = this.chatInput.value.trim();
        if (!question) return;

        // Add user message to chat
        this.addMessage(question, 'user');
        this.chatInput.value = '';
        this.chatInput.disabled = true;
        this.sendBtn.disabled = true;
        this.sendBtn.innerHTML = '<div class="loading"></div>';

        try {
            const response = await fetch(`${this.apiBaseUrl}/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: question,
                    top_k: 5
                })
            });

            if (!response.ok) {
                let errorMessage = `Request failed: ${response.status}`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorMessage;
                } catch (e) {
                    errorMessage = `${errorMessage} - ${response.statusText}`;
                }
                throw new Error(errorMessage);
            }

            const result = await response.json();
            
            // Add bot response to chat - sources hidden by default
            let botMessage = `<strong>AI Assistant:</strong> ${result.answer}`;
            
            if (result.sources && result.sources.length > 0) {
                const sourcesHtml = `
                    <div class="sources ${this.showSources ? 'show' : ''}">
                        <strong>Sources (${result.sources.length}):</strong>
                        ${result.sources.map((source, index) => `
                            <div class="source-item">
                                <strong>Source ${index + 1}</strong> from "${source.metadata.filename}" 
                                (Relevance: ${source.relevance_percentage || (source.score * 100).toFixed(1)}%)<br>
                                <em>${source.content.substring(0, 120)}...</em>
                            </div>
                        `).join('')}
                    </div>
                    <button class="show-sources-btn" onclick="this.previousElementSibling.classList.toggle('show'); this.textContent = this.previousElementSibling.classList.contains('show') ? 'Hide Sources' : 'Show Sources'">
                        ${this.showSources ? 'Hide Sources' : 'Show Sources'}
                    </button>
                `;
                botMessage += sourcesHtml;
            }

            this.addMessage(botMessage, 'bot');

        } catch (error) {
            console.error('Query error:', error);
            this.addMessage(`<strong>AI Assistant:</strong> Sorry, I encountered an error: ${error.message}`, 'bot');
        } finally {
            this.chatInput.disabled = false;
            this.sendBtn.disabled = false;
            this.sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
            this.chatInput.focus();
        }
    }

    toggleAllSourcesVisibility() {
        // Toggle visibility of all existing sources in chat
        const allSources = this.chatMessages.querySelectorAll('.sources');
        const allToggleButtons = this.chatMessages.querySelectorAll('.show-sources-btn');
        
        allSources.forEach(sources => {
            if (this.showSources) {
                sources.classList.add('show');
            } else {
                sources.classList.remove('show');
            }
        });
        
        allToggleButtons.forEach(button => {
            button.textContent = this.showSources ? 'Hide Sources' : 'Show Sources';
        });
    }

    addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        if (type === 'user') {
            messageDiv.innerHTML = `<strong>You:</strong> ${content}`;
        } else {
            messageDiv.innerHTML = content;
        }
        
        this.chatMessages.appendChild(messageDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    showStatus(message, type) {
        this.uploadStatus.innerHTML = `<div class="status ${type}">${message}</div>`;
        setTimeout(() => {
            this.uploadStatus.innerHTML = '';
        }, 5000);
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// Initialize the frontend when the page loads
let frontend;
document.addEventListener('DOMContentLoaded', () => {
    frontend = new RAGFrontend();
});