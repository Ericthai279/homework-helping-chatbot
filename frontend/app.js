// NOTE: This file replaces the entire content of frontend/static/app.js
// It already includes the payment-page UI logic, Lucide loading, and activation on page show.

// API Base URL
const API_BASE_URL = '/api';

// Global state
let authToken = null;
let currentExerciseId = null;
let currentRoadmapJobId = null;

// --- Component Templates ---
const headerTemplate = document.getElementById('global-header-template');
const footerTemplate = document.getElementById('global-footer-template');

// Inject Header/Footer once per page switch
function injectGlobalComponents() {
    document.querySelector('header')?.remove();
    document.querySelector('footer')?.remove();

    document.body.prepend(headerTemplate.content.cloneNode(true).querySelector('header'));
    document.body.appendChild(footerTemplate.content.cloneNode(true).querySelector('footer'));

    document.getElementById('global-logout-btn')?.addEventListener('click', handleLogout);
}

// --- Page Navigation & Auth ---
function showPage(pageId) {
    // Clear any active QR timer before switching pages
    if (document.getElementById('payment-qr-page')?.dataset.timerInterval) {
        clearInterval(document.getElementById('payment-qr-page').dataset.timerInterval);
    }
    
    // Layout handling
    if (pageId === 'login-page' || pageId === 'register-page') {
        document.body.classList.add('flex', 'items-center', 'justify-center', 'min-h-screen');
        document.body.classList.remove('flex-col');
        document.querySelector('header')?.remove();
        document.querySelector('footer')?.remove();
    } else {
        document.body.classList.remove('flex', 'items-center', 'justify-center', 'min-h-screen');
        document.body.classList.add('flex-col');
        injectGlobalComponents();
        setNavigationActiveState(pageId);
    }

    // Activate page
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const activePage = document.getElementById(pageId);
    if (activePage) activePage.classList.add('active');

    // === PAYMENT PAGE INITIALIZATION ===
    if (pageId === 'payment-page') {
        // Load Lucide icons once
        if (typeof lucide === 'undefined') {
            const script = document.createElement('script');
            script.src = 'https://unpkg.com/lucide@latest/dist/umd/lucide.min.js';
            script.onload = () => lucide.createIcons();
            document.head.appendChild(script);
        }
        setupPaymentPageLogic();
    }
    if (pageId === 'payment-qr-page') {
        setupPaymentQrPage();
    }
}

// NEW: Function to check auth status before navigating to a protected page (like chat)
function checkAuthAndNavigate(pageId) {
    if (pageId === 'chat-page' && !authToken) {
        // If the user wants to access chat without a token, redirect to register/login
        showPage('register-page');
        const messageEl = document.getElementById('register-form')?.querySelector('.message');
        if (messageEl) {
            messageEl.textContent = 'Please register or log in to use the Chatbot service.';
            messageEl.style.color = 'orange';
        }
    } else if (pageId === 'chat-page' && authToken) {
        // If authenticated, go to chat
        showPage('chat-page');
    } else {
        // For all other pages, just navigate
        showPage(pageId);
    }
}


// Navigation active state
function setNavigationActiveState(currentPageId) {
    const pageKey = currentPageId.replace('-page', '');
    const header = document.querySelector('header');

    document.querySelectorAll('header nav a').forEach(a => {
        a.classList.remove('text-[#0259dd]', 'text-white', 'font-bold'); 
        a.classList.add('text-gray-600');
    });

    if (header) {
        if (currentPageId === 'service-page') {
            header.classList.remove('bg-[#fffdf5]', 'border-gray-200');
            header.classList.add('bg-[#0259dd]');
            document.querySelectorAll('header nav a').forEach(a => {
                a.classList.remove('text-gray-600');
                a.classList.add('text-white/80');
            });
            document.getElementById('global-logout-btn')?.classList.remove('text-white', 'bg-[#0259dd]');
            document.getElementById('global-logout-btn')?.classList.add('bg-white', 'text-[#0259dd]');
        } else {
            header.classList.add('bg-[#fffdf5]', 'border-gray-200');
            header.classList.remove('bg-[#0259dd]');
            document.getElementById('global-logout-btn')?.classList.remove('bg-white', 'text-[#0259dd]');
            document.getElementById('global-logout-btn')?.classList.add('bg-[#0259dd]', 'text-white');
            document.querySelectorAll('header nav a').forEach(a => a.classList.remove('text-white/80'));
        }
    }

    const activeLink = document.getElementById(`nav-${pageKey}`);
    if (activeLink) {
        activeLink.classList.remove('text-gray-600', 'text-white/80');
        activeLink.classList.add('font-bold');
        activeLink.classList.add(currentPageId === 'service-page' ? 'text-white' : 'text-[#0259dd]');
    }
}

function setupPaymentPageLogic() {
    const paymentPage = document.getElementById('payment-page');
    if (!paymentPage) return;
    
    // Load Lucide (Check if needed again due to page switch logic)
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    const radioInputs = paymentPage.querySelectorAll('input[name="payment_method"]');
    const paymentLabels = paymentPage.querySelectorAll('.payment-card-label');
    
    function updateSelection(selectedId) {
        paymentLabels.forEach(label => {
            const input = document.getElementById(label.getAttribute('for'));
            const radioDot = label.querySelector('.custom-radio-input > div');
            const card = label.querySelector('div[class*="p-5"]');
    
            if (input.id === selectedId) {
                card.classList.add('border-blue-600', 'shadow-md');
                card.classList.remove('border-gray-300');
                radioDot.classList.remove('hidden');
            } else {
                card.classList.remove('border-blue-600', 'shadow-md');
                card.classList.add('border-gray-300');
                radioDot.classList.add('hidden');
            }
        });
    }
    
    // Initial state
    const checked = paymentPage.querySelector('input[name="payment_method"]:checked');
    if (checked) updateSelection(checked.id);
    
    // Clear and re-attach listeners:
    const currentInputs = paymentPage.querySelectorAll('input[name="payment_method"]');
    const currentLabels = paymentPage.querySelectorAll('.payment-card-label');

    currentInputs.forEach(input => {
        input.removeEventListener('change', updateSelection); // Remove old listener
        input.addEventListener('change', () => updateSelection(input.id));
    });
    
    currentLabels.forEach(label => {
        label.removeEventListener('click', handleLabelClick); // Remove old listener
        label.addEventListener('click', handleLabelClick);
    });

    function handleLabelClick() {
        const input = document.getElementById(this.getAttribute('for'));
        if (input) {
            input.checked = true;
            updateSelection(input.id);
        }
    }
    
    // === CONTINUE PAYMENT BUTTON ===
    const continueBtn = paymentPage.querySelector('#continue-payment-btn');
    if (continueBtn) {
        // Ensure only one listener is attached
        continueBtn.removeEventListener('click', handleContinuePayment); 
        continueBtn.addEventListener('click', handleContinuePayment);
    }
}

function handleContinuePayment() {
    const paymentPage = document.getElementById('payment-page');
    const selectedMethod = paymentPage.querySelector('input[name="payment_method"]:checked');
            
    if (!selectedMethod) {
        alert('Vui lòng chọn phương thức thanh toán');
        return;
    }
    
    const method = selectedMethod.id;
    
    if (method === 'momo') {
        showPage('payment-qr-page');
    } 
    else if (method === 'card') {
        alert('Thanh toán bằng thẻ tín dụng đang phát triển...');
    }
    else if (method === 'bank') {
        alert('Chuyển khoản ngân hàng đang phát triển...');
    }
}

// ==================== PAYMENT QR PAGE LOGIC ====================
function setupPaymentQrPage() {
    const qrPage = document.getElementById('payment-qr-page');
    if (!qrPage) return;
    
    // Load Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    // Back button
    const backBtn = qrPage.querySelector('#qr-back-btn');
    backBtn?.removeEventListener('click', handleQrBack);
    backBtn?.addEventListener('click', handleQrBack);
    
    // Confirm button
    const confirmBtn = qrPage.querySelector('#confirm-payment-btn');
    confirmBtn?.removeEventListener('click', handleQrConfirm);
    confirmBtn?.addEventListener('click', handleQrConfirm);

    // Reset countdown state and start new timer
    qrPage.dataset.timerInterval = '';
    
    // === FAKE QR + COUNTDOWN (Replace with real API later) ===
    const qrImg = qrPage.querySelector('#momo-qr-code');
    const timerEl = qrPage.querySelector('#qr-timer');
    
    // Fake QR (replace with real data URL from backend)
    qrImg.src = 'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=momo://pay?amount=99000&note=Edukie-nang-cao';
    
    // Countdown: 10 minutes
    let seconds = 600;
    
    // Ensure countdown display is reset
    timerEl.textContent = '10:00';
    timerEl.parentElement.classList.replace('bg-gray-100', 'bg-red-50');
    timerEl.parentElement.classList.replace('text-gray-500', 'text-red-700');
    confirmBtn.disabled = false;
    confirmBtn.classList.remove('opacity-50', 'cursor-not-allowed');

    const interval = setInterval(() => {
        seconds--;
        const mins = String(Math.floor(seconds / 60)).padStart(2, '0');
        const secs = String(seconds % 60).padStart(2, '0');
        timerEl.textContent = `${mins}:${secs}`;
    
        if (seconds <= 0) {
            clearInterval(interval);
            timerEl.textContent = 'Hết hạn';
            timerEl.parentElement.classList.replace('bg-red-50', 'bg-gray-100');
            timerEl.parentElement.classList.replace('text-red-700', 'text-gray-500');
            confirmBtn.disabled = true;
            confirmBtn.classList.add('opacity-50', 'cursor-not-allowed');
        }
    }, 1000);
    
    // Store interval to clear later if needed
    qrPage.dataset.timerInterval = interval;
}

function handleQrBack(e) {
    e.preventDefault();
    showPage('payment-page'); // Always go back to payment method selection
}

function handleQrConfirm() {
    // Clear interval when confirmed
    if (document.getElementById('payment-qr-page')?.dataset.timerInterval) {
        clearInterval(document.getElementById('payment-qr-page').dataset.timerInterval);
    }

    alert('Thanh toán thành công! Bạn đã nâng cấp lên Edukie nâng cao.');
    showPage('home-page'); // Redirect to home/success page
}


// --- Login Form ---
const loginForm = document.getElementById('login-form');
loginForm?.addEventListener('submit', async e => {
    e.preventDefault();
    const formData = new FormData(loginForm);
    const messageEl = loginForm.querySelector('.message');

    try {
        const response = await fetch(`${API_BASE_URL}/auth/token`, {
            method: 'POST',
            body: formData,
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Login failed');

        authToken = data.access_token;
        localStorage.setItem('edu-token', authToken);
        showPage('home-page');
        loginForm.reset();
        if (messageEl) messageEl.textContent = '';
    } catch (error) {
        if (messageEl) messageEl.textContent = `Error: ${error.message}`;
    }
});

// --- Register Form ---
const registerForm = document.getElementById('register-form');
registerForm?.addEventListener('submit', async e => {
    e.preventDefault();
    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const gender = document.querySelector('input[name="gender"]:checked')?.value;
    const dobDay = document.getElementById('register-dob-day').value.padStart(2, '0');
    const dobMonth = document.getElementById('register-dob-month').value.padStart(2, '0');
    const dobYear = document.getElementById('register-dob-year').value;
    const date_of_birth = `${dobYear}-${dobMonth}-${dobDay}`;
    const major = document.getElementById('register-major').value;
    const school = document.getElementById('register-school').value;
    const terms = document.getElementById('register-terms').checked;
    const messageEl = registerForm.querySelector('.message');

    if (!terms) {
        if (messageEl) {
            messageEl.textContent = 'Bạn phải đồng ý với Điều khoản sử dụng và Chính sách bảo mật.';
            messageEl.style.color = 'red';
        }
        return;
    }

    const payload = { email, password, username, gender, date_of_birth, major, school };
    try {
        const response = await fetch(`${API_BASE_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Registration failed');

        if (messageEl) {
            messageEl.textContent = 'Registration successful! Please log in.';
            messageEl.style.color = 'green';
        }
        registerForm.reset();
        setTimeout(() => {
            showPage('login-page');
            if (messageEl) { messageEl.textContent = ''; messageEl.style.color = ''; }
        }, 2000);
    } catch (error) {
        if (messageEl) {
            messageEl.textContent = `Error: ${error.message}`;
            messageEl.style.color = 'red';
        }
    }
});

// --- Logout ---
function handleLogout() {
    authToken = null;
    localStorage.removeItem('edu-token');
    currentExerciseId = null;
    showPage('login-page'); // Redirects to login
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
        chatMessages.innerHTML = `<div class="flex"><div class="bg-blue-600 text-white p-4 rounded-xl rounded-bl-none max-w-lg shadow"><p>Xin chào! Tôi là Edukie. Vui lòng nhập bài tập (hoặc đính kèm hình ảnh) để nhận gợi ý từng bước.</p></div></div>`;
    }
    resetChatState();
}

// --- Image Handling ---
const fileInput = document.getElementById('file-input');
const imagePreviewContainer = document.getElementById('image-preview-container');
const imagePreview = document.getElementById('image-preview');
const removeImageBtn = document.getElementById('remove-image-btn');
let attachedFileBase64 = null;

if (fileInput) {
    fileInput.addEventListener('change', () => {
        const file = fileInput.files[0];
        if (file) {
            if (currentExerciseId) {
                addMessage("You can only attach an image when starting a new exercise.", 'ai', 'error');
                fileInput.value = null;
                return;
            }
            const reader = new FileReader();
            reader.onload = e => {
                const base64String = e.target.result;
                imagePreview.src = base64String;
                attachedFileBase64 = base64String.split(',')[1];
            };
            reader.readAsDataURL(file);
            imagePreviewContainer.classList.remove('hidden');
        }
    });
}
if (removeImageBtn) {
    removeImageBtn.addEventListener('click', () => {
        attachedFileBase64 = null;
        if (fileInput) fileInput.value = null;
        if (imagePreview) imagePreview.src = "";
        if (imagePreviewContainer) imagePreviewContainer.classList.add('hidden');
    });
}

// --- Chat Logic ---
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const chatMessages = document.getElementById('chat-messages');
const chatStateHelper = document.getElementById('chat-state-helper');

if (chatForm) {
    chatForm.addEventListener('submit', e => {
        e.preventDefault();
        const message = chatInput.value.trim();
        if (!authToken) {
            addMessage("Please log in or register to start a new exercise.", 'ai', 'error');
            return;
        }

        if (currentExerciseId) {
            if (!message) return;
            handleSubmitAnswer(message);
        } else {
            if (!message && !attachedFileBase64) return;
            handleNewExercise(message, attachedFileBase64);
        }
        chatInput.value = '';
        if (removeImageBtn) removeImageBtn.click();
    });
}

async function handleNewExercise(prompt, base64Image) {
    if (prompt) addMessage(prompt, 'user');
    if (base64Image) {
        const imageUrl = `data:image/jpeg;base64,${base64Image}`;
        const imageHtml = `<img src="${imageUrl}" alt="Exercise Image" class="w-full h-auto max-w-xs rounded-lg">`;
        addMessage(imageHtml, 'user');
    }
    if (chatStateHelper) chatStateHelper.textContent = 'Status: AI is analyzing the exercise...';

    const payload = { prompt, base64_image: base64Image };
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
        if (!response.ok) throw new Error(data.detail || 'Unknown error');

        addMessage(data.interactions[0].ai_response, 'ai');
        currentExerciseId = data.id;
        if (chatStateHelper) chatStateHelper.textContent = `Status: Working on Exercise #${data.id}. Please enter your answer.`;
        if (fileInput) fileInput.disabled = true;
    } catch (error) {
        addMessage(`Error: ${error.message}`, 'ai', 'error');
        resetChatState();
        checkToken(error);
    }
}

async function handleSubmitAnswer(answer) {
    addMessage(answer, 'user');
    if (chatStateHelper) chatStateHelper.textContent = 'Status: AI is checking your answer...';

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
        if (!response.ok) throw new Error(data.detail || 'Unknown error');

        addMessage(data.check_response, 'ai', data.is_correct ? 'success' : 'normal');
        if (data.is_correct) {
            if (data.suggested_exercise) {
                addMessage("Good job! Here is a similar exercise for you to practice:\n\n" + data.suggested_exercise, 'ai');
            }
            resetChatState();
        } else {
            if (chatStateHelper) chatStateHelper.textContent = `Status: Working on Exercise #${currentExerciseId}. Please try again.`;
        }
    } catch (error) {
        addMessage(`Error: ${error.message}`, 'ai', 'error');
        if (chatStateHelper) chatStateHelper.textContent = 'Status: An error occurred.';
        checkToken(error);
    }
}

function resetChatState() {
    currentExerciseId = null;
    if (chatStateHelper) chatStateHelper.textContent = 'Status: Ready for a new exercise.';
    if (fileInput) fileInput.disabled = false;
}

function addMessage(text, sender = 'ai', type = 'normal') {
    if (!chatMessages) return;
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('flex', 'w-full');

    let bubbleClasses = 'p-4 rounded-xl max-w-lg shadow ';
    if (sender === 'user') {
        messageDiv.classList.add('justify-end');
        bubbleClasses += 'bg-gray-200 text-gray-800 rounded-br-none';
    } else {
        if (type === 'error') bubbleClasses += 'bg-red-500 text-white rounded-bl-none';
        else if (type === 'success') bubbleClasses += 'bg-green-500 text-white rounded-bl-none';
        else bubbleClasses += 'bg-blue-600 text-white rounded-bl-none';
    }

    messageDiv.innerHTML = `<div class="${bubbleClasses}">${
        sender === 'user' && text.startsWith('<img') ? text : `<p style="white-space: pre-wrap;">${text}</p>`
    }</div>`;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function checkToken(error) {
    if (error.message.includes('401') || error.message.includes('Could not validate credentials')) {
        handleLogout();
    }
}

// --- Initial Load ---
function init() {
    // Populate DOB dropdowns
    const daySelect = document.getElementById('register-dob-day');
    const monthSelect = document.getElementById('register-dob-month');
    const yearSelect = document.getElementById('register-dob-year');
    if (daySelect && monthSelect && yearSelect) {
        for (let i = 1; i <= 31; i++) daySelect.innerHTML += `<option value="${i}">${i}</option>`;
        for (let i = 1; i <= 12; i++) monthSelect.innerHTML += `<option value="${i}">${i}</option>`;
        const currentYear = new Date().getFullYear();
        for (let i = currentYear - 15; i >= currentYear - 75; i--) yearSelect.innerHTML += `<option value="${i}">${i}</option>`;
    }

    const token = localStorage.getItem('edu-token');
    if (token) {
        authToken = token;
        showPage('home-page');
    } else {
        // Always default to home-page if not logged in, as requested.
        showPage('home-page'); 
    }

    // Logout listeners
    document.getElementById('nav-logout-btn')?.addEventListener('click', handleLogout);
    document.getElementById('about-logout-btn')?.addEventListener('click', handleLogout);
    document.getElementById('service-logout-btn')?.addEventListener('click', handleLogout);
    document.getElementById('shop-logout-btn')?.addEventListener('click', handleLogout);
    document.getElementById('contact-logout-btn')?.addEventListener('click', handleLogout);
    document.getElementById('global-logout-btn')?.addEventListener('click', handleLogout);
    document.getElementById('logout-btn')?.addEventListener('click', handleLogout); // For chat page header
    document.getElementById('logout-btn-sidebar')?.addEventListener('click', handleLogout); // For chat page sidebar

    // Sidebar toggle
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const hamburgerBtn = document.getElementById('hamburger-btn');
    const closeSidebarBtn = document.getElementById('close-sidebar-btn');

    hamburgerBtn?.addEventListener('click', () => {
        sidebar.classList.add('open');
        overlay.classList.remove('hidden');
    });
    closeSidebarBtn?.addEventListener('click', () => {
        sidebar.classList.remove('open');
        overlay.classList.add('hidden');
    });
    overlay?.addEventListener('click', () => {
        sidebar.classList.remove('open');
        overlay.classList.add('hidden');
    });

    // Roadmap modal
    const roadmapModal = document.getElementById('roadmap-modal');
    const goPremiumBtn = document.getElementById('go-premium-btn');
    const closeRoadmapBtn = document.getElementById('close-roadmap-btn');
    const roadmapForm = document.getElementById('roadmap-form');

    goPremiumBtn?.addEventListener('click', () => {
        roadmapModal.classList.remove('hidden');
        document.getElementById('roadmap-status').classList.add('hidden');
        document.getElementById('roadmap-display').classList.add('hidden');
        document.getElementById('generate-roadmap-btn').disabled = false;
    });
    closeRoadmapBtn?.addEventListener('click', () => roadmapModal.classList.add('hidden'));
    roadmapForm?.addEventListener('submit', handleRoadmapRequest);
}

// Placeholder for handleRoadmapRequest (not provided in prompt but referenced)
async function handleRoadmapRequest(e) {
    e.preventDefault();
    const target = document.getElementById('learning-target-input').value;
    const statusEl = document.getElementById('roadmap-status');
    const displayEl = document.getElementById('roadmap-display');
    const generateBtn = document.getElementById('generate-roadmap-btn');

    statusEl.classList.remove('hidden', 'bg-green-100', 'text-green-700', 'bg-red-100', 'text-red-700');
    statusEl.classList.add('bg-yellow-100', 'text-yellow-700');
    statusEl.textContent = 'Generating roadmap...';
    generateBtn.disabled = true;

    // FAKE API CALL DELAY
    await new Promise(resolve => setTimeout(resolve, 2000));

    if (target.toLowerCase().includes('error')) {
         statusEl.classList.replace('bg-yellow-100', 'bg-red-100');
         statusEl.classList.replace('text-yellow-700', 'text-red-700');
         statusEl.textContent = 'Error generating roadmap. Please try again.';
         generateBtn.disabled = false;
         displayEl.classList.add('hidden');
         return;
    }

    statusEl.classList.replace('bg-yellow-100', 'bg-green-100');
    statusEl.classList.replace('text-yellow-700', 'text-green-700');
    statusEl.textContent = 'Roadmap generated successfully!';
    
    displayEl.innerHTML = `
        <h4 class="font-semibold text-blue-600">Lộ trình cho: ${target}</h4>
        <p class="text-sm"><strong>Tuần 1:</strong> Ôn tập cơ bản và các định lý chính.</p>
        <p class="text-sm"><strong>Tuần 2:</strong> Bài tập ứng dụng và kiểm tra giữa kỳ.</p>
        <p class="text-sm"><strong>Tuần 3:</strong> Mô hình hóa và dự đoán nâng cao.</p>
        <p class="text-sm"><strong>Tuần 4:</strong> Tổng hợp và chuẩn bị thi.</p>
    `;
    displayEl.classList.remove('hidden');
    generateBtn.disabled = false;
}

init();