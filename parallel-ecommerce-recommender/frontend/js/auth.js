async function handleAuth() {
    if (currentUser) {
        logout();
    } else {
        showLoginModal();
    }
}

function showLoginModal() {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
        <div class="bg-white dark:bg-gray-800 rounded-lg p-8 max-w-md w-full mx-4">
            <h2 class="text-2xl font-bold mb-6 dark:text-white">Login / Register</h2>
            
            <div class="mb-4">
                <input type="text" id="loginUsername" placeholder="Username" 
                       class="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600">
            </div>
            <div class="mb-4">
                <input type="password" id="loginPassword" placeholder="Password" 
                       class="w-full px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600">
            </div>
            
            <div class="flex space-x-4">
                <button onclick="login()" class="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700">
                    Login
                </button>
                <button onclick="register()" class="flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700">
                    Register
                </button>
            </div>
            
            <button onclick="this.parentElement.parentElement.remove()" 
                    class="mt-4 w-full text-gray-600 dark:text-gray-400 hover:text-gray-800">
                Cancel
            </button>
        </div>
    `;
    
    document.body.appendChild(modal);
}

async function login() {
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    
    if (!username || !password) {
        showToast('Please enter username and password', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('user_id', data.user_id);
            localStorage.setItem('username', data.username);
            
            currentUser = data;
            checkAuth();
            showToast('Login successful!', 'success');
            
            // Close modal
            document.querySelector('.fixed.inset-0')?.remove();
            
            // Load user data
            loadRecommendations();
        } else {
            showToast('Login failed', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showToast('Login failed', 'error');
    }
}

async function register() {
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    
    if (!username || !password) {
        showToast('Please enter username and password', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/register`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                username, 
                password,
                email: `${username}@example.com`
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('user_id', data.user_id);
            localStorage.setItem('username', username);
            
            currentUser = data;
            checkAuth();
            showToast('Registration successful!', 'success');
            
            // Close modal
            document.querySelector('.fixed.inset-0')?.remove();
            
            loadRecommendations();
        } else {
            const error = await response.json();
            showToast(error.detail || 'Registration failed', 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showToast('Registration failed', 'error');
    }
}

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('username');
    currentUser = null;
    checkAuth();
    showToast('Logged out successfully', 'info');
    showPage('home');
}

function checkAuth() {
    const token = localStorage.getItem('access_token');
    const username = localStorage.getItem('username');
    const userId = localStorage.getItem('user_id');
    
    if (token && username) {
        currentUser = {
            username: username,
            user_id: parseInt(userId)
        };
        
        const authButton = document.getElementById('authButton');
        if (authButton) {
            authButton.innerHTML = `<i class="fas fa-user"></i> ${username}`;
            authButton.classList.remove('bg-green-600', 'hover:bg-green-700');
            authButton.classList.add('bg-red-600', 'hover:bg-red-700');
        }
    } else {
        currentUser = null;
        const authButton = document.getElementById('authButton');
        if (authButton) {
            authButton.innerHTML = '<i class="fas fa-sign-in-alt"></i> Login';
            authButton.classList.remove('bg-red-600', 'hover:bg-red-700');
            authButton.classList.add('bg-green-600', 'hover:bg-green-700');
        }
    }
}