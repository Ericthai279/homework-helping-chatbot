// API Base URL
const API_BASE_URL = '/api';

// Global state
let authToken = null;
let currentExerciseId = null;

// --- Page Navigation & Auth ---
function showPage(pageId) {
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
    });
    const activePage = document.getElementById(pageId);
    if (activePage) {
        activePage.classList.add('active');
    }
}
const loginForm = document.getElementById('login-form');
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(loginForm);
    const messageEl = loginForm.querySelector('.message');
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/token`, {
            method: 'POST',
            body: formData,
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Login failed');
        }
        
        authToken = data.access_token;
        localStorage.setItem('edu-token', authToken);
        showPage('main-app-page');
        loginForm.reset();
        if(messageEl) messageEl.textContent = '';
        
    } catch (error) {
        if(messageEl) messageEl.textContent = `Error: ${error.message}`;
    }
});

// --- THIS IS THE UPDATED REGISTER FUNCTION ---
const registerForm = document.getElementById('register-form');
registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // --- Get all new form values ---
    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const gender = document.querySelector('input[name="gender"]:checked')?.value;
    
    // --- Date Formatting Fix ---
    // We must pad the month and day to be 2 digits (e.g., "YYYY-MM-DD")
    const dobDay = document.getElementById('register-dob-day').value.padStart(2, '0');
    const dobMonth = document.getElementById('register-dob-month').value.padStart(2, '0');
    const dobYear = document.getElementById('register-dob-year').value;
    const date_of_birth = `${dobYear}-${dobMonth}-${dobDay}`;
    // --- End of Date Fix ---

    const major = document.getElementById('register-major').value;
    const school = document.getElementById('register-school').value;
    const terms = document.getElementById('register-terms').checked;
    
    const messageEl = registerForm.querySelector('.message');

    // --- Basic validation ---
    if (!terms) {
        if(messageEl) {
            messageEl.textContent = 'Bạn phải đồng ý với Điều khoản sử dụng và Chính sách bảo mật.';
            messageEl.style.color = 'red';
        }
        return;
    }
    // --- This is the data your backend currently accepts ---
    const payload = {
        email: email,
        password: password,
        username: username,
        gender: gender,
        date_of_birth: date_of_birth,
        major: major,
        school: school
    };
    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload), // Send the complete payload
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            // This will now show the *specific* error from the backend
            // e.g., "Username already taken"
            throw new Error(data.detail || 'Registration failed');
        }
        
        if(messageEl) {
            messageEl.textContent = 'Registration successful! Please log in.';
            messageEl.style.color = 'green';
        }
        registerForm.reset();
        
        setTimeout(() => {
            showPage('login-page');
            if(messageEl) {
                messageEl.textContent = '';
                messageEl.style.color = '';
            }
        }, 2000);
        
    } catch (error) {
        if(messageEl) {
            messageEl.textContent = `Error: ${error.message}`;
            messageEl.style.color = 'red';
        }
    }
});
// --- END OF UPDATED FUNCTION ---


function handleLogout() {
    authToken = null;
    localStorage.removeItem('edu-token');
    currentExerciseId = null;
    showPage('login-page');
    chatMessages.innerHTML = `
        <div class="flex">
            <div class="bg-blue-600 text-white p-4 rounded-xl rounded-bl-none max-w-lg shadow">
                <p>Hello! I'm Edukie. Please enter your exercise (or attach an image) to get step-by-step hints.</p>
            </div>
        </div>`;
    resetChatState();
}

// --- Image Handling Logic (Converts to Base64) ---
const fileInput = document.getElementById('file-input');
const imagePreviewContainer = document.getElementById('image-preview-container');
const imagePreview = document.getElementById('image-preview');
const removeImageBtn = document.getElementById('remove-image-btn');
let attachedFileBase64 = null; // <-- This will store the base64 string

if(fileInput) {
    fileInput.addEventListener('change', () => {
        const file = fileInput.files[0];
        if (file) {
            if (currentExerciseId) {
                addMessage("You can only attach an image when starting a new exercise.", 'ai', 'error');
                fileInput.value = null;
                return;
            }
            
            const reader = new FileReader();
            reader.onload = (e) => {
                const base64String = e.target.result;
                imagePreview.src = base64String;
                attachedFileBase64 = base64String.split(',')[1];
            };
            reader.readAsDataURL(file);
            imagePreviewContainer.classList.remove('hidden');
        }
    });
}
if(removeImageBtn) {
    removeImageBtn.addEventListener('click', () => {
        attachedFileBase64 = null;
        if(fileInput) fileInput.value = null;
        if(imagePreview) imagePreview.src = "";
        if(imagePreviewContainer) imagePreviewContainer.classList.add('hidden');
    });
}

// --- Chat Logic (Tutor Model) ---
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatMessages = document.getElementById('chat-messages');
const chatStateHelper = document.getElementById('chat-state-helper');

if(chatForm) {
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const message = chatInput.value.trim();

        if (currentExerciseId) {
            // --- MODE 1: SUBMITTING AN ANSWER ---
            if (!message) return;
            handleSubmitAnswer(message);
        } else {
            // --- MODE 2: SUBMITTING A NEW EXERCISE ---
            if (!message && !attachedFileBase64) return;
            handleNewExercise(message, attachedFileBase64);
        }
        
        chatInput.value = '';
        if(removeImageBtn) removeImageBtn.click();
    });
}

// Submit a new exercise to get a hint
async function handleNewExercise(prompt, base64Image) {
    // --- THIS IS THE FIX ---
    // Add the user's messages (text and/or image) to the chat history
    if (prompt) {
        addMessage(prompt, 'user');
    }
    if (base64Image) {
        // We need to reconstruct the data URL to display it
        const imageUrl = `data:image/jpeg;base64,${base64Image}`;
        // We create an HTML string for the image
        const imageHtml = `<img src="${imageUrl}" alt="Exercise Image" class="w-full h-auto max-w-xs rounded-lg">`;
        addMessage(imageHtml, 'user');
    }
    // --- END OF FIX ---

    chatStateHelper.textContent = 'Status: AI is analyzing the exercise...';
    
    const payload = {
        prompt: prompt,
        base64_image: base64Image
    };

    try {
        const response = await fetch(`${API_BASE_URL}/exercises/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        if (!response.ok) { throw new Error(data.detail || 'Unknown error'); }

        addMessage(data.interactions[0].ai_response, 'ai');
        
        currentExerciseId = data.id;
        chatStateHelper.textContent = `Status: Working on Exercise #${data.id}. Please enter your answer.`;
        if(fileInput) fileInput.disabled = true;

    } catch (error) {
        addMessage(`Error: ${error.message}`, 'ai', 'error');
        resetChatState();
        checkToken(error);
    }
}

// Submit an answer to be checked
async function handleSubmitAnswer(answer) {
    addMessage(answer, 'user');
    chatStateHelper.textContent = 'Status: AI is checking your answer...';

    try {
        const response = await fetch(`${API_BASE_URL}/exercises/${currentExerciseId}/answer`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({ answer: answer })
        });

        const data = await response.json();
        if (!response.ok) { throw new Error(data.detail || 'Unknown error'); }

        addMessage(data.check_response, 'ai', data.is_correct ? 'success' : 'normal');

        if (data.is_correct) {
            if (data.suggested_exercise) {
                addMessage("Good job! Here is a similar exercise for you to practice:\n\n" + data.suggested_exercise, 'ai');
            }
            resetChatState();
        } else {
            chatStateHelper.textContent = `Status: Working on Exercise #${currentExerciseId}. Please try again.`;
        }

    } catch (error) {
        addMessage(`Error: ${error.message}`, 'ai', 'error');
        chatStateHelper.textContent = 'Status: An error occurred.';
        checkToken(error);
    }
}

// Reset chat state
function resetChatState() {
    currentExerciseId = null;
    chatStateHelper.textContent = 'Status: Ready for a new exercise.';
    if(fileInput) fileInput.disabled = false;
}

// --- addMessage Function (handles message display) ---
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
            bubbleClasses += 'bg-green-500 text-white rounded-bl-none';
        } else {
            bubbleClasses += 'bg-blue-600 text-white rounded-bl-none';
        }
    }
    
    // Use pre-wrap to preserve formatting (line breaks, etc.)
    // This also allows it to render the HTML string for the image
    messageDiv.innerHTML = `<div class="${bubbleClasses}">${
        sender === 'user' && text.startsWith('<img') ? text : `<p style="white-space: pre-wrap;">${text}</p>`
    }</div>`;
    chatMessages.appendChild(messageDiv);
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// --- Utility (Token Check) ---
function checkToken(error) {
    if (error.message.includes('401') || error.message.includes('Could not validate credentials')) {
        handleLogout();
    }
}


// --- THIS IS THE UPDATED INIT FUNCTION ---
function init() {
    // --- Populate Date of Birth Dropdowns ---
    const daySelect = document.getElementById('register-dob-day');
    const monthSelect = document.getElementById('register-dob-month');
    const yearSelect = document.getElementById('register-dob-year');

    if(daySelect && monthSelect && yearSelect) {
        // Populate Days (value is "1", "2", etc.)
        for (let i = 1; i <= 31; i++) {
            daySelect.innerHTML += `<option value="${i}">${i}</option>`;
        }
        // Populate Months (value is "1", "2", etc.)
        for (let i = 1; i <= 12; i++) {
            monthSelect.innerHTML += `<option value="${i}">${i}</option>`;
        }
        // Populate Years (e.g., from 1950 to 2010)
        const currentYear = new Date().getFullYear();
        for (let i = currentYear - 15; i >= currentYear - 75; i--) {
            yearSelect.innerHTML += `<option value="${i}">${i}</option>`;
        }
    }
    // --- End of DOB Population ---


    const token = localStorage.getItem('edu-token');
    if (token) {
        authToken = token;
        showPage('main-app-page');
    } else {
        showPage('login-page');
    }
    
    const logoutBtn = document.getElementById('logout-btn');
    if(logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
    const logoutBtnSidebar = document.getElementById('logout-btn-sidebar');
    if(logoutBtnSidebar) {
        logoutBtnSidebar.addEventListener('click', handleLogout);
    }

    // Sidebar Toggle Logic
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const hamburgerBtn = document.getElementById('hamburger-btn');
    const closeSidebarBtn = document.getElementById('close-sidebar-btn');

    if (hamburgerBtn && sidebar && overlay) {
        hamburgerBtn.addEventListener('click', () => {
            sidebar.classList.add('open');
            overlay.classList.remove('hidden');
        });
    }

    if (closeSidebarBtn && sidebar && overlay) {
        closeSidebarBtn.addEventListener('click', () => {
            sidebar.classList.remove('open');
            overlay.classList.add('hidden');
        });
    }
    
    if (overlay && sidebar) {
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('open');
            overlay.classList.add('hidden');
        });
    }
}
// --- END OF UPDATED FUNCTION ---

init();