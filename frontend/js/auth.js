import { auth, provider } from './firebase-config.js';
import { signInWithPopup, signOut, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-auth.js";
import { API_BASE } from './api.js';

export function initAuth(onLoginCallback, onLogoutCallback) {
    const loginBtn = document.getElementById('login-btn');
    const authWarning = document.getElementById('auth-warning');

    if (loginBtn) {
        loginBtn.addEventListener('click', () => {
            signInWithPopup(auth, provider).catch(error => console.error("Login failed:", error));
        });
    }

    onAuthStateChanged(auth, async (user) => {
        if (user) {
            try {
                const res = await fetch(`${API_BASE}/user?uid=${user.uid}`);
                const data = await res.json();
                
                if (!data.exists || !data.user.display_name) {
                    showDisplayNameModal(user, onLoginCallback);
                } else {
                    completeLogin(user, data.user.display_name, onLoginCallback);
                }
            } catch (error) {
                console.error("Failed to check user status:", error);
            }
        } else {
            window.currentUserUid = null;
            window.currentUserDisplayName = null;
            
            const profileLink = document.getElementById('profile-link');
            
            if (loginBtn) loginBtn.style.display = 'inline-block';
            if (profileLink) profileLink.style.display = 'none';
            if (authWarning) authWarning.style.display = 'block';
            
            if (onLogoutCallback) onLogoutCallback();
        }
    });
}

function showDisplayNameModal(user, onLoginCallback) {
    let modal = document.getElementById('display-name-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'display-name-modal';
        modal.innerHTML = `
            <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 1000; display: flex; justify-content: center; align-items: center; backdrop-filter: blur(5px);">
                <div style="background: var(--card-bg); padding: 40px; border-radius: 16px; text-align: center; max-width: 400px; width: 90%; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
                    <h2 style="margin-top: 0; margin-bottom: 10px;">Welcome to Anime Ranker!</h2>
                    <p style="color: var(--text-muted); margin-bottom: 24px;">Please choose a unique display name.</p>
                    <input type="text" id="display-name-input" placeholder="Display Name" style="padding: 14px; margin-bottom: 10px; width: 100%; border-radius: 8px; border: 1px solid rgba(255,255,255,0.2); background: rgba(0,0,0,0.2); color: white; font-size: 1rem; box-sizing: border-box;">
                    <p id="display-name-error" style="color: #ef4444; display: none; margin-bottom: 16px; font-size: 0.9rem;"></p>
                    <button id="submit-display-name" class="primary-btn" style="width: 100%;">Save & Continue</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        document.getElementById('submit-display-name').addEventListener('click', async () => {
            const input = document.getElementById('display-name-input');
            const errorMsg = document.getElementById('display-name-error');
            const name = input.value.trim();
            
            if (!name) {
                errorMsg.innerText = "Display name cannot be empty.";
                errorMsg.style.display = 'block';
                return;
            }
            
            const btn = document.getElementById('submit-display-name');
            btn.innerText = "Saving...";
            btn.disabled = true;

            try {
                const response = await fetch(`${API_BASE}/user/display_name`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ uid: user.uid, display_name: name })
                });
                const resData = await response.json();
                
                if (response.ok) {
                    modal.style.display = 'none';
                    completeLogin(user, name, onLoginCallback);
                } else {
                    errorMsg.innerText = resData.error || "Name already taken.";
                    errorMsg.style.display = 'block';
                    btn.innerText = "Save & Continue";
                    btn.disabled = false;
                }
            } catch (err) {
                errorMsg.innerText = "Network error. Please try again.";
                errorMsg.style.display = 'block';
                btn.innerText = "Save & Continue";
                btn.disabled = false;
            }
        });
    }
    modal.style.display = 'block';
}

function completeLogin(user, displayName, onLoginCallback) {
    window.currentUserUid = user.uid;
    window.currentUserDisplayName = displayName;
    
    const loginBtn = document.getElementById('login-btn');
    const profileLink = document.getElementById('profile-link');
    const profilePic = document.getElementById('profile-pic');
    const authWarning = document.getElementById('auth-warning');

    if (loginBtn) loginBtn.style.display = 'none';
    
    if (profileLink && profilePic) {
        profileLink.style.display = 'inline-block';
        profilePic.src = user.photoURL || '/frontend/images/default.webp';
    }
    
    if (authWarning) authWarning.style.display = 'none';
    
    if (onLoginCallback) onLoginCallback(user);
}
