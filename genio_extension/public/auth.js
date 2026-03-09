// FILE: public/auth.js
// public/auth.js
// This script runs on the HOSTED auth.html page, not in the extension.

// This event listener waits for the entire page, including deferred scripts, to be loaded.
document.addEventListener('DOMContentLoaded', () => {
    try {
        // Firebase is now initialized automatically by /__/firebase/init.js
        // We just need to wait for it to be available.
        if (typeof firebase === 'undefined') {
            console.error("Firebase SDK not loaded. This page must be hosted on Firebase.");
            document.body.innerHTML = '<h1>A critical error occurred. Firebase SDK not found.</h1>';
            return;
        }
        
        // Now that Firebase is guaranteed to be initialized, run the main app logic.
        runAuthFlow();

    } catch (e) {
        console.error("Fatal Error during Firebase initialization:", e);
        document.body.innerHTML = '<h1>A critical error occurred. Please try again.</h1>';
    }
});


function runAuthFlow() {
    const fbAuth = firebase.auth();
    // We are no longer using firebase.functions() on the client.

    // --- Get Extension ID from URL ---
    const urlParams = new URLSearchParams(window.location.search);
    const extensionId = urlParams.get('extensionId');
    if (!extensionId) {
        document.body.innerHTML = '<h1>Error: Missing Extension ID. This page must be opened from the Genio Feed extension.</h1>';
        return;
    }

    // --- DOM Elements ---
    const elements = {
        login: {
            container: document.getElementById('loginContainer'),
            email: document.getElementById('email'),
            password: document.getElementById('password'),
            btn: document.getElementById('loginBtn'),
            emailError: document.getElementById('emailError'),
            passwordError: document.getElementById('passwordError')
        },
        signup: {
            container: document.getElementById('signupContainer'),
            name: document.getElementById('signupName'),
            email: document.getElementById('signupEmail'),
            password: document.getElementById('signupPassword'),
            btn: document.getElementById('signupBtn'),
            nameError: document.getElementById('nameError'),
            emailError: document.getElementById('signupEmailError'),
            passwordError: document.getElementById('signupPasswordError')
        },
        links: {
            showSignup: document.getElementById('showSignup'),
            showLogin: document.getElementById('showLogin')
        },
        passwordToggles: document.querySelectorAll('.toggle-password')
    };

    // --- Utility Functions ---
    const showError = (element, message) => {
        if (element) {
            element.textContent = message;
            element.style.display = 'block';
        }
    };
    const clearErrors = (errorElements) => errorElements.forEach(el => {
        if (el) {
            el.textContent = '';
            el.style.display = 'none';
        }
    });
    const setButtonState = (button, isLoading, defaultText) => {
        if (button) {
            button.disabled = isLoading;
            button.textContent = isLoading ? 'Loading...' : defaultText;
        }
    };

    // --- Core Auth Logic ---
    const onAuthSuccess = async (user) => {
        try {
            // Get the ID token from the successfully logged-in user.
            const idToken = await user.getIdToken();
            
            // Use a direct fetch call instead of the callable function SDK.
            const response = await fetch('https://us-central1-genio-f9386.cloudfunctions.net/createToken', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ idToken: idToken }) 
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error?.message || 'Server responded with an error.');
            }

            const result = await response.json();
            const customToken = result.token;

            if (!customToken) {
                throw new Error("Cloud function did not return a valid token.");
            }

            // Send the custom token back to the extension
            chrome.runtime.sendMessage(extensionId, {
                command: 'authSuccess',
                payload: { token: customToken }
            }, (response) => {
                if (chrome.runtime.lastError || !response || !response.success) {
                    console.error("Failed to send token to extension:", chrome.runtime.lastError?.message);
                    document.body.innerHTML = '<h1>Authentication successful, but failed to connect back to the extension. Please close this tab and try again.</h1>';
                } else {
                    // The background script will handle closing the tab.
                    document.body.innerHTML = '<h1>Success! You can now close this tab.</h1>';
                }
            });
        } catch (error) {
            console.error("Error creating or sending token:", error);
            document.body.innerHTML = `<h1>Error: ${error.message}. Please close this tab and try again.</h1>`;
        }
    };

    const handleLogin = async () => {
        const { email, password, btn, emailError, passwordError } = elements.login;
        clearErrors([emailError, passwordError]);
        setButtonState(btn, true, 'Log In');
        try {
            const userCredential = await fbAuth.signInWithEmailAndPassword(email.value, password.value);
            await onAuthSuccess(userCredential.user);
        } catch (error) {
            if (error.code === 'auth/user-not-found' || error.code === 'auth/invalid-email' || error.code === 'auth/invalid-credential') {
                showError(passwordError, "Invalid email or password.");
            } else {
                showError(passwordError, error.message);
            }
            setButtonState(btn, false, 'Log In');
        }
    };

    const handleSignup = async () => {
        const { name, email, password, btn, nameError, emailError, passwordError } = elements.signup;
        clearErrors([nameError, emailError, passwordError]);
        setButtonState(btn, true, 'Sign Up');
        try {
            const userCredential = await fbAuth.createUserWithEmailAndPassword(email.value, password.value);
            await userCredential.user.updateProfile({ displayName: name.value });
            // The user document creation is now handled by a Cloud Function trigger.
            await onAuthSuccess(userCredential.user);
        } catch (error) {
            if (error.code === 'auth/email-already-in-use' || error.code === 'auth/invalid-email') {
                showError(emailError, error.message);
            } else {
                showError(passwordError, error.message);
            }
            setButtonState(btn, false, 'Sign Up');
        }
    };

    // --- Event Listeners ---
    if (elements.login.btn) elements.login.btn.addEventListener('click', handleLogin);
    if (elements.signup.btn) elements.signup.btn.addEventListener('click', handleSignup);
    if (elements.links.showSignup) {
        elements.links.showSignup.addEventListener('click', (e) => {
            e.preventDefault();
            elements.login.container.style.display = 'none';
            elements.signup.container.style.display = 'flex';
        });
    }
    if (elements.links.showLogin) {
        elements.links.showLogin.addEventListener('click', (e) => {
            e.preventDefault();
            elements.signup.container.style.display = 'none';
            elements.login.container.style.display = 'flex';
        });
    }
    elements.passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', (event) => {
            const targetInput = document.getElementById(event.currentTarget.dataset.target);
            if (targetInput) {
                targetInput.type = targetInput.type === 'password' ? 'text' : 'password';
            }
        });
    });
}