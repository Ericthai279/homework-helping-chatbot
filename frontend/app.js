// API Base URL (assuming your backend is on the same host)
// If your backend is at http://127.0.0.1:8000, use that.
const API_BASE_URL = 'http://127.0.0.1:8000/api';

// Global state
let authToken = null;
let currentExerciseId = null;

// --- Page Navigation ---
function showPage(pageId) {
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    document.getElementById(pageId).classList.add('active');
}

// --- Authentication ---
const loginForm = document.getElementById('login-form');
const loginError = document.getElementById('login-error');

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    loginError.textContent = '';
    
    // NOTE: The /token endpoint expects "form-data", not JSON.
    const formData = new FormData();
    formData.append('username', document.getElementById('login-email').value);
    formData.append('password', document.getElementById('login-password').value);
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/token`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Đăng nhập thất bại');
        }
        
        authToken = data.access_token;
        localStorage.setItem('edu-token', authToken);
        
        // On successful login, go to the main app
        showPage('main-app-page');

    } catch (error) {
        loginError.textContent = error.message;
    }
});

const registerForm = document.getElementById('register-form');
const registerError = document.getElementById('register-error');

registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    registerError.textContent = '';
    
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Đăng ký thất bại');
        }
        
        // On successful registration, show a message and go to login
        alert('Đăng ký thành công! Vui lòng đăng nhập.');
        showPage('login-page');

    } catch (error) {
        registerError.textContent = error.message;
    }
});

function handleLogout() {
    authToken = null;
    localStorage.removeItem('edu-token');
    currentExerciseId = null;
    showPage('login-page');
    document.getElementById('chat-messages').innerHTML = `
        <div class="flex">
            <div class="bg-blue-600 text-white p-4 rounded-xl rounded-bl-none max-w-lg shadow">
                <p>Xin chào! Tôi là Edukie. Hãy nhập bài tập hoặc câu hỏi của bạn vào bên dưới để bắt đầu.</p>
            </div>
        </div>`;
}

// --- Chat Logic ---
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatMessages = document.getElementById('chat-messages');
const chatStateHelper = document.getElementById('chat-state-helper');

chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const message = chatInput.value.trim();
    if (!message) return;

    if (currentExerciseId === null) {
        // We are starting a NEW exercise
        handleNewExercise(message);
    } else {
        // We are SUBMITTING an ANSWER to an existing exercise
        handleSubmitAnswer(message);
    }
    
    chatInput.value = '';
});

async function handleNewExercise(content) {
    addMessage(content, 'user');
    
    try {
        const response = await fetch(`${API_BASE_URL}/exercises/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ content })
        });
        
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail);

        // Save the new exercise ID
        currentExerciseId = data.id;
        
        // The first hint is in the interactions array
        const firstHint = data.interactions[0].ai_response;
        addMessage(firstHint, 'ai');

        // Update helper text
        chatStateHelper.textContent = `Trạng thái: Đang chờ câu trảGợi ý, câu trả lời, hoặc bài tập mới: #${currentExerciseId}`;

    } catch (error) {
        addMessage(`Lỗi: ${error.message}`, 'ai', 'error');
        checkToken(error);
    }
}

async function handleSubmitAnswer(answer) {
    addMessage(answer, 'user');
    
    try {
        const response = await fetch(`${API_BASE_URL}/exercises/${currentExerciseId}/answer`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ answer })
        });
        
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail);

        // Add the AI's check/explanation
        addMessage(data.explanation, 'ai', data.is_correct ? 'success' : 'normal');

        if (data.is_correct) {
            // Exercise is finished!
            addMessage(`Bài tập đã hoàn thành! Bạn có muốn làm một bài tập tương tự không?\n\n${data.suggested_exercise}`, 'ai', 'success');
            currentExerciseId = null; // Reset state
            chatStateHelper.textContent = 'Trạng thái: Đã hoàn thành! Sẵn sàng cho bài tập mới.';
        } else {
            // Exercise is not finished, waiting for new answer
            chatStateHelper.textContent = `Trạng thái: Đang chờ câu trả lời cho Bài tập #${currentExerciseId}`;
        }

    } catch (error) {
        addMessage(`Lỗi: ${error.message}`, 'ai', 'error');
        checkToken(error);
    }
}

function addMessage(text, sender = 'ai', type = 'normal') {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('flex', 'w-full');
    
    let bubbleClasses = 'p-4 rounded-xl max-w-lg shadow ';
    
    if (sender === 'user') {
        messageDiv.classList.add('justify-end');
        bubbleClasses += 'bg-gray-200 text-gray-800 rounded-br-none';
    } else {
        if (type === 'error') {
            bubbleClasses += 'bg-red-500 text-white rounded-bl-none';
        } else if (type === 'success') {
            bubbleClasses += 'bg-green-600 text-white rounded-bl-none';
        } else {
        
            bubbleClasses += 'bg-blue-600 text-white rounded-bl-none';
        }
    }
    
    messageDiv.innerHTML = `<div class="${bubbleClasses}"><p style="white-space: pre-wrap;">${text}</p></div>`;
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// --- Utility ---
function checkToken(error) {
    // If the error is a 401 (unauthorized), log the user out
    if (error.message.includes('401') || error.message.includes('validate')) {
        handleLogout();
    }
}

// --- Initial Load ---
function init() {
    const token = localStorage.getItem('edu-token');
    if (token) {
        authToken = token;
        showPage('main-app-page');
    } else {
        showPage('login-page');
    }
}

init(); // Run on page load