function sendMessage() {
    const userInput = document.getElementById('user-input').value.trim();
    const chatbox = document.getElementById('chatbox');
    const loadingIndicator = document.getElementById('loading-indicator');
    const errorMessage = document.getElementById('error-message');

    if (userInput) {
        // Clear error message
        errorMessage.style.display = 'none';

        // Add user's message to the chatbox
        chatbox.innerHTML += `
            <div class="message user">
                <span class="label">You</span>
                <p>${userInput}</p>
            </div>
        `;

        // Clear input field
        document.getElementById('user-input').value = '';

        // Auto Scrolling
        chatbox.scrollTop = chatbox.scrollHeight;

        // loading indicator
        chatbox.innerHTML += `
            <div id="typing-indicator" class="message bot">
                <span class="label">Bot</span>
                <p><em>Typing...</em></p>
                <div class="spinner-border spinner-border-sm text-secondary" role="status"></div>
            </div>
        `;

        // Auto-scroll
        chatbox.scrollTop = chatbox.scrollHeight;

        // API CAll to main.py
        fetch('/get_response', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: userInput }),
        })
            .then(response => response.json())
            .then(data => {
                // Removes typing indicator
                const typingIndicator = document.getElementById('typing-indicator');
                if (typingIndicator) {
                    typingIndicator.remove();
                }

                // Convert markdown to HTML using marked
                const formattedReply = marked.parse(data.reply);

                // Add bot's message to the chatbox
                chatbox.innerHTML += `
                    <div class="message bot">
                        <span class="label">Bot</span>
                        <div class="markdown-content">${formattedReply}</div>
                    </div>
                `;

                // Auto-scroll
                chatbox.scrollTop = chatbox.scrollHeight;
            })
            .catch(() => {
                errorMessage.style.display = 'block';
            })
            .finally(() => {
                // Ensure the loading indicator is hidden
                loadingIndicator.style.display = 'none';
            });
    }
}

// Add event listener for Enter key
document.getElementById('user-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});