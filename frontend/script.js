const BACKEND_URL = window.location.origin;
let currentResumeText = "";
let chatHistory = [];

// Screens
const landingScreen = document.getElementById('landingScreen');
const processingScreen = document.getElementById('processingScreen');
const dashboardScreen = document.getElementById('dashboardScreen');

// Core Elements
const resumeInput = document.getElementById('resumeInput');
const fileSelectedBanner = document.getElementById('fileSelectedBanner');
const fileSelectedName = document.getElementById('fileSelectedName');
const uploadPrimary = document.getElementById('uploadPrimary');
const matchBtn = document.getElementById('matchBtn');
const processingLabel = document.getElementById('processingLabel');
const backBtn = document.getElementById('backBtn');

// Dashboard Elements
const resumeContent = document.getElementById('resumeContent');
const jobsGrid = document.getElementById('jobsGrid');
const jobsCountText = document.getElementById('jobsCountText');

// Chat Elements
const chatPanel = document.getElementById('chatPanel');
const openChatBtn = document.getElementById('openChatBtn');
const closeChatBtn = document.getElementById('closeChatBtn');
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const sendBtn = document.getElementById('sendBtn');
const chatTyping = document.getElementById('chatTyping');

// === STEP TRACKING ===
function updateStatus(text, stepId = null) {
    processingLabel.textContent = text;
    if (stepId) {
        // Mark previous steps as done
        const steps = ['step1', 'step2', 'step3', 'step4', 'step5'];
        const currentIdx = steps.indexOf(stepId);
        
        steps.forEach((id, idx) => {
            const el = document.getElementById(id);
            if (!el) return;
            if (idx < currentIdx) {
                el.classList.remove('active');
                el.classList.add('done');
            } else if (idx === currentIdx) {
                el.classList.add('active');
                el.classList.remove('done');
            } else {
                el.classList.remove('active', 'done');
            }
        });
    }
}

// === FILE SELECTION ===
resumeInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        fileSelectedName.textContent = file.name;
        fileSelectedBanner.classList.remove('hidden');
        uploadPrimary.textContent = "Resume Selected";
        matchBtn.disabled = false;
    } else {
        fileSelectedBanner.classList.add('hidden');
        uploadPrimary.textContent = "Drop your PDF resume here";
        matchBtn.disabled = true;
    }
});

// Allow clicking the upload zone (but avoid double-triggering if label/browse is clicked)
document.getElementById('uploadZone').addEventListener('click', (e) => {
    if (e.target.tagName !== 'LABEL' && e.target.tagName !== 'INPUT' && !e.target.classList.contains('upload-browse')) {
        resumeInput.click();
    }
});

// === MATCHING LOGIC ===
matchBtn.addEventListener('click', async () => {
    const file = resumeInput.files[0];
    if (!file) return;

    // Transition to Processing
    landingScreen.classList.remove('active');
    processingScreen.classList.add('active');
    
    updateStatus("Extracting resume content...", "step1");

    const formData = new FormData();
    formData.append('file', file);

    try {
        // Parallel status updates for better UX feel
        setTimeout(() => updateStatus("Generating search keywords...", "step2"), 2000);
        setTimeout(() => updateStatus("Scraping live job listings...", "step3"), 5000);
        
        const response = await fetch(`${BACKEND_URL}/match`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || "Failed to process resume");
        }

        const data = await response.json();
        
        updateStatus("Running semantic matching...", "step4");
        
        // Final polish steps
        setTimeout(() => updateStatus("Generating AI insights...", "step5"), 1000);
        
        await new Promise(r => setTimeout(r, 1500));

        // Transition to Dashboard
        currentResumeText = data.resume_text;
        displayResults(data);
        
        processingScreen.classList.remove('active');
        dashboardScreen.classList.add('active');

    } catch (error) {
        console.error("Error:", error);
        alert("Error: " + error.message);
        processingScreen.classList.remove('active');
        landingScreen.classList.add('active');
    }
});

function displayResults(data) {
    resumeContent.textContent = data.resume_text || "No text extracted.";

    const matches = data.matches || [];
    jobsGrid.innerHTML = "";
    jobsCountText.textContent = `${matches.length} Jobs Found`;

    if (matches.length === 0) {
        jobsGrid.innerHTML = `<div class="empty-state">No matching opportunities found.</div>`;
    } else {
        matches.forEach(job => {
            const card = document.createElement('div');
            card.className = 'job-card';
            
            const scorePercent = Math.round(job.score * 100);
            let scoreClass = 'score-low';
            if (scorePercent >= 80) scoreClass = 'score-high';
            else if (scorePercent >= 50) scoreClass = 'score-mid';
            
            card.innerHTML = `
                <div class="job-card-top">
                    <div class="job-title-group">
                        <h3 class="job-title">${job.title}</h3>
                        <span class="job-company">${job.company}</span>
                    </div>
                    <div class="score-badge ${scoreClass}">
                        <span class="score-value">${scorePercent}%</span>
                        <span class="score-label">Match</span>
                    </div>
                </div>
                <div class="match-bar-wrap ${scoreClass}">
                    <div class="match-bar-track">
                        <div class="match-bar-fill" style="width: ${scorePercent}%"></div>
                    </div>
                </div>
                <p class="job-desc">${job.description ? job.description.substring(0, 200) + '...' : 'No description available.'}</p>
                ${job.analysis ? `
                    <div class="ai-insight">
                        <div class="ai-insight-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
                        </div>
                        <div class="ai-insight-text">
                            <span class="ai-insight-label">AI Analysis</span>
                            ${job.analysis}
                        </div>
                    </div>
                ` : ''}
                <div class="job-card-footer">
                    <a href="${job.url}" target="_blank" class="view-job-btn">View Opportunity →</a>
                </div>
            `;
            jobsGrid.appendChild(card);
        });
    }
}

// === NAVIGATION ===
backBtn.addEventListener('click', () => {
    dashboardScreen.classList.remove('active');
    landingScreen.classList.add('active');
    resumeInput.value = "";
    fileSelectedBanner.classList.add('hidden');
    uploadPrimary.textContent = "Drop your PDF resume here";
    matchBtn.disabled = true;
});

// === CHAT ===
openChatBtn.addEventListener('click', () => {
    chatPanel.classList.remove('hidden');
    chatInput.focus();
});

closeChatBtn.addEventListener('click', () => {
    chatPanel.classList.add('hidden');
});

document.getElementById('chatOverlay').addEventListener('click', () => {
    chatPanel.classList.add('hidden');
});

sendBtn.addEventListener('click', sendMessage);
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    addMessageToUI('user', text);
    chatInput.value = "";
    chatInput.style.height = 'auto';

    chatTyping.classList.remove('hidden');
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await fetch(`${BACKEND_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                resume_text: currentResumeText,
                message: text,
                history: chatHistory
            })
        });

        if (!response.ok) throw new Error("Failed to get response");
        const data = await response.json();
        
        addMessageToUI('bot', data.response);
        chatHistory.push({ role: 'user', content: text });
        chatHistory.push({ role: 'bot', content: data.response });

    } catch (error) {
        addMessageToUI('bot', "Error: " + error.message);
    } finally {
        chatTyping.classList.add('hidden');
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

function addMessageToUI(role, content) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-msg ${role}`;
    
    const avatar = role === 'bot' ? 
        `<div class="msg-avatar"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="8" r="4"/><path d="M6 20v-2a6 6 0 0 1 12 0v2"/></svg></div>` : '';
    
    // Use marked for bot responses, escape user input for safety
    const displayContent = role === 'bot' ? marked.parse(content) : escapeHTML(content);
    
    msgDiv.innerHTML = `
        ${avatar}
        <div class="msg-bubble">${displayContent}</div>
    `;
    
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = (chatInput.scrollHeight) + 'px';
});
