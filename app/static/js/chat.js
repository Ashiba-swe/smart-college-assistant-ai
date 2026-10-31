// Smart College Assistant AI - Interactive Chat Engine
document.addEventListener('DOMContentLoaded', function () {
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const chatContainer = document.getElementById('chat-messages');
    const typingIndicator = document.getElementById('typing-indicator');
    const sendBtn = document.getElementById('send-btn');
    const currentConvId = document.getElementById('current-conversation-id') ? document.getElementById('current-conversation-id').value : '';

    // Scroll chat pane to bottom
    function scrollToBottom() {
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }
    scrollToBottom();

    // Suggested Question Pill Click
    document.querySelectorAll('.prompt-pill').forEach(pill => {
        pill.addEventListener('click', function () {
            const query = this.getAttribute('data-query');
            if (messageInput) {
                messageInput.value = query;
                chatForm.dispatchEvent(new Event('submit'));
            }
        });
    });

    // Form Submission
    if (chatForm) {
        chatForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const message = messageInput.value.trim();
            if (!message) return;

            // 1. Clear input & disable send
            messageInput.value = '';
            messageInput.disabled = true;
            if (sendBtn) sendBtn.disabled = true;

            // 2. Append User Message Bubble
            appendUserMessage(message);
            scrollToBottom();

            // 3. Show Typing Indicator
            if (typingIndicator) {
                typingIndicator.classList.remove('d-none');
                scrollToBottom();
            }

            try {
                const response = await fetch('/api/chat/send', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        message: message,
                        conversation_id: currentConvId || null
                    })
                });

                const data = await response.json();

                // Hide Typing Indicator
                if (typingIndicator) {
                    typingIndicator.classList.add('d-none');
                }

                if (response.ok && data.success) {
                    // Update URL if this is a newly created conversation
                    if (!currentConvId && data.conversation_id) {
                        window.history.pushState({}, '', '/chat/' + data.conversation_id);
                        const hiddenConvInput = document.getElementById('current-conversation-id');
                        if (hiddenConvInput) hiddenConvInput.value = data.conversation_id;
                    }

                    appendAssistantMessage(data.assistant_message, data.is_no_answer);
                    scrollToBottom();
                } else {
                    appendSystemErrorMessage(data.error || 'Unable to retrieve answer. Please try again.');
                    scrollToBottom();
                }
            } catch (err) {
                console.error('Chat error:', err);
                if (typingIndicator) typingIndicator.classList.add('d-none');
                appendSystemErrorMessage('Network error connecting to the college assistant. Please check your connection.');
                scrollToBottom();
            } finally {
                messageInput.disabled = false;
                if (sendBtn) sendBtn.disabled = false;
                messageInput.focus();
            }
        });
    }

    // Helper: Append User Message
    function appendUserMessage(text) {
        const timeNow = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const bubble = document.createElement('div');
        bubble.className = 'd-flex justify-content-end mb-3';
        bubble.innerHTML = `
            <div class="message-bubble message-user shadow-sm">
                <div class="text-white">${escapeHtml(text)}</div>
                <div class="text-end text-light opacity-75 small mt-1" style="font-size: 0.75rem;">
                    ${timeNow} <i class="bi bi-person-fill ms-1"></i>
                </div>
            </div>
        `;
        chatContainer.appendChild(bubble);
    }

    // Helper: Append Assistant Message with Citations and Feedback Controls
    function appendAssistantMessage(msg, isNoAnswer) {
        const bubble = document.createElement('div');
        bubble.className = 'd-flex justify-content-start mb-3';

        let citationsHtml = '';
        if (msg.sources && msg.sources.length > 0) {
            citationsHtml = `
                <div class="mt-2 pt-2 border-top border-secondary-subtle">
                    <div class="d-flex align-items-center mb-1 text-teal fw-semibold small cursor-pointer" 
                         data-bs-toggle="collapse" data-bs-target="#sources-${msg.id}" style="cursor: pointer;">
                        <i class="bi bi-shield-check me-1 text-success"></i> 
                        <span>Verified Citations (${msg.sources.length} sources)</span>
                        <i class="bi bi-chevron-down ms-auto small"></i>
                    </div>
                    <div class="collapse show" id="sources-${msg.id}">
                        ${msg.sources.map((s, idx) => `
                            <div class="source-citation-card">
                                <div class="d-flex justify-content-between align-items-center">
                                    <span class="fw-bold text-dark"><i class="bi bi-file-earmark-text text-primary me-1"></i>${escapeHtml(s.title)}</span>
                                    <span class="badge bg-light text-dark border">Page ${s.page}</span>
                                </div>
                                <div class="text-muted small mt-1">${escapeHtml(s.snippet || '')}</div>
                                <div class="text-end mt-1">
                                    <span class="badge bg-teal-subtle text-teal" style="font-size: 0.7rem;">Match: ${s.similarity}%</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        let noAnswerNotice = '';
        if (isNoAnswer) {
            noAnswerNotice = `
                <div class="alert alert-warning py-2 px-3 small mt-2 mb-0 d-flex align-items-center">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    <div>Information not found in college knowledge base. You can report this missing topic below.</div>
                </div>
            `;
        }

        bubble.innerHTML = `
            <div class="message-bubble message-assistant shadow-sm w-100" style="max-width: 88%;">
                <div class="d-flex align-items-center mb-2">
                    <span class="badge bg-teal text-white me-2"><i class="bi bi-robot"></i> Apex Assistant</span>
                    <span class="text-muted small" style="font-size: 0.75rem;">${msg.created_at || 'Just now'}</span>
                </div>
                <div class="text-dark" id="msg-content-${msg.id}" style="white-space: pre-wrap;">${escapeHtml(msg.content)}</div>
                ${noAnswerNotice}
                ${citationsHtml}
                <div class="d-flex align-items-center justify-content-between mt-3 pt-2 border-top border-light-subtle">
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-secondary btn-sm py-0 px-2" title="Copy answer" onclick="copyToClipboard('msg-content-${msg.id}', this)">
                            <i class="bi bi-clipboard"></i> Copy
                        </button>
                    </div>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-success btn-sm py-0 px-2" title="Helpful answer" onclick="sendFeedback(${msg.id}, 1, 'HELPFUL', this)">
                            <i class="bi bi-hand-thumbs-up"></i>
                        </button>
                        <button class="btn btn-outline-danger btn-sm py-0 px-2" title="Report issue" onclick="openReportModal(${msg.id})">
                            <i class="bi bi-flag"></i> Report
                        </button>
                    </div>
                </div>
            </div>
        `;
        chatContainer.appendChild(bubble);
    }

    function appendSystemErrorMessage(errText) {
        const bubble = document.createElement('div');
        bubble.className = 'd-flex justify-content-center mb-3';
        bubble.innerHTML = `
            <div class="alert alert-danger py-2 px-3 small shadow-sm">
                <i class="bi bi-exclamation-circle me-1"></i> ${escapeHtml(errText)}
            </div>
        `;
        chatContainer.appendChild(bubble);
    }

    function escapeHtml(text) {
        if (!text) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    }
});

// Feedback handlers
async function sendFeedback(messageId, rating, feedbackType, btnElement) {
    try {
        const res = await fetch('/api/feedback/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message_id: messageId, rating: rating, feedback_type: feedbackType })
        });
        const data = await res.json();
        if (data.success && btnElement) {
            btnElement.classList.remove('btn-outline-success');
            btnElement.classList.add('btn-success');
            btnElement.disabled = true;
        }
    } catch (e) {
        console.error(e);
    }
}

let activeReportMsgId = null;
function openReportModal(messageId) {
    activeReportMsgId = messageId;
    const reportModal = new bootstrap.Modal(document.getElementById('reportIssueModal'));
    reportModal.show();
}

async function submitReport() {
    if (!activeReportMsgId) return;
    const reason = document.getElementById('report-reason').value;
    const comments = document.getElementById('report-comments').value;

    try {
        const res = await fetch('/api/feedback/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message_id: activeReportMsgId,
                rating: -1,
                feedback_type: reason,
                comments: comments
            })
        });
        const data = await res.json();
        if (data.success) {
            bootstrap.Modal.getInstance(document.getElementById('reportIssueModal')).hide();
            alert('Report submitted successfully. Academic administrators will review and update the knowledge base.');
        }
    } catch (e) {
        alert('Failed to submit report. Please try again.');
    }
}
