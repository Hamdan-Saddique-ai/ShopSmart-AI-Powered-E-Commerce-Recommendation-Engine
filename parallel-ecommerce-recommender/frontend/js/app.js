// API Configuration
const API_URL = 'http://localhost:8000';
let currentUser = null;
let darkMode = localStorage.getItem('darkMode') === 'true';

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    checkAuth();
    loadCategories();
    loadProducts();
    setupEventListeners();
    
    if (darkMode) {
        document.body.classList.add('dark-mode');
    }
}

function setupEventListeners() {
    // Search input
    document.getElementById('searchInput')?.addEventListener('input', debounce(handleSearch, 500));
    
    // Category filter
    document.getElementById('categoryFilter')?.addEventListener('change', handleCategoryFilter);
}

function showPage(pageName) {
    // Hide all pages
    const pages = ['homePage', 'productsPage', 'dashboardPage', 'profilePage'];
    pages.forEach(page => {
        const element = document.getElementById(page);
        if (element) element.classList.add('hidden');
    });
    
    // Show selected page
    const selectedPage = document.getElementById(`${pageName}Page`);
    if (selectedPage) {
        selectedPage.classList.remove('hidden');
        selectedPage.classList.add('fade-in');
    }
    
    // Load page-specific data
    if (pageName === 'dashboard' && currentUser) {
        loadDashboard();
    } else if (pageName === 'profile' && currentUser) {
        loadProfile();
    } else if (pageName === 'home') {
        loadRecommendations();
    }
}

function toggleDarkMode() {
    darkMode = !darkMode;
    localStorage.setItem('darkMode', darkMode);
    document.body.classList.toggle('dark-mode');
}

async function loadCategories() {
    try {
        const response = await fetch(`${API_URL}/categories`);
        const categories = await response.json();
        
        const categorySelect = document.getElementById('categoryFilter');
        const categoryGrid = document.getElementById('categories');
        
        if (categorySelect) {
            categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category;
                option.textContent = category;
                categorySelect.appendChild(option);
            });
        }
        
        if (categoryGrid) {
            categories.slice(0, 5).forEach(category => {
                const categoryCard = document.createElement('div');
                categoryCard.className = 'bg-gradient-to-br from-blue-500 to-purple-500 rounded-lg p-6 text-white text-center cursor-pointer hover:opacity-90';
                categoryCard.innerHTML = `
                    <i class="fas fa-tag text-3xl mb-2"></i>
                    <p class="font-semibold">${category}</p>
                `;
                categoryCard.onclick = () => filterByCategory(category);
                categoryGrid.appendChild(categoryCard);
            });
        }
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

async function loadProducts() {
    const productsGrid = document.getElementById('productsGrid');
    if (!productsGrid) return;
    
    productsGrid.innerHTML = '<div class="loading-spinner mx-auto col-span-4"></div>';
    
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_URL}/products?limit=20`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const products = await response.json();
        displayProducts(products);
    } catch (error) {
        console.error('Error loading products:', error);
        productsGrid.innerHTML = '<p class="text-red-500 col-span-4">Error loading products</p>';
    }
}

function displayProducts(products) {
    const productsGrid = document.getElementById('productsGrid');
    if (!productsGrid) return;
    
    productsGrid.innerHTML = '';
    
    products.forEach(product => {
        const productCard = createProductCard(product);
        productsGrid.appendChild(productCard);
    });
}

function createProductCard(product) {
    const card = document.createElement('div');
    card.className = 'product-card bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden cursor-pointer';
    card.onclick = () => viewProduct(product.id);
    
    card.innerHTML = `
        <img src="${product.image_url}" alt="${product.name}" class="w-full h-48 object-cover">
        <div class="p-4">
            <h3 class="font-semibold text-lg mb-2 dark:text-white">${product.name}</h3>
            <p class="text-gray-600 dark:text-gray-400 text-sm mb-2">${product.description.substring(0, 80)}...</p>
            <div class="flex justify-between items-center">
                <span class="text-2xl font-bold text-blue-600">$${product.price}</span>
                <div class="flex items-center">
                    <i class="fas fa-star text-yellow-400 mr-1"></i>
                    <span class="dark:text-white">${product.rating}</span>
                </div>
            </div>
            <button onclick="event.stopPropagation(); addToFavorites(${product.id})" 
                    class="mt-3 w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700">
                <i class="fas fa-heart"></i> Add to Favorites
            </button>
        </div>
    `;
    
    return card;
}

function handleSearch() {
    const searchTerm = document.getElementById('searchInput').value;
    filterProducts(searchTerm, document.getElementById('categoryFilter').value);
}

function handleCategoryFilter() {
    const category = document.getElementById('categoryFilter').value;
    filterProducts(document.getElementById('searchInput').value, category);
}

async function filterProducts(search, category) {
    const productsGrid = document.getElementById('productsGrid');
    productsGrid.innerHTML = '<div class="loading-spinner mx-auto col-span-4"></div>';
    
    try {
        const token = localStorage.getItem('access_token');
        let url = `${API_URL}/products?`;
        if (search) url += `search=${search}&`;
        if (category) url += `category=${category}&`;
        url += 'limit=20';
        
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const products = await response.json();
        displayProducts(products);
    } catch (error) {
        console.error('Error filtering products:', error);
        productsGrid.innerHTML = '<p class="text-red-500 col-span-4">Error loading products</p>';
    }
}

function filterByCategory(category) {
    document.getElementById('categoryFilter').value = category;
    showPage('products');
    filterProducts('', category);
}

async function viewProduct(productId) {
    // Record view interaction
    try {
        const token = localStorage.getItem('access_token');
        await fetch(`${API_URL}/user-interaction`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                product_id: productId,
                interaction_type: 'view'
            })
        });
        
        showToast('Product viewed', 'info');
    } catch (error) {
        console.error('Error recording interaction:', error);
    }
}

async function addToFavorites(productId) {
    if (!currentUser) {
        showToast('Please login to add favorites', 'warning');
        return;
    }
    
    try {
        const token = localStorage.getItem('access_token');
        await fetch(`${API_URL}/favorites/${productId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        showToast('Added to favorites!', 'success');
    } catch (error) {
        console.error('Error adding to favorites:', error);
        showToast('Error adding to favorites', 'error');
    }
}

async function loadDashboard() {
    await loadPerformanceStats();
    await loadRecentlyViewed();
    await loadFavorites();
}

async function loadPerformanceStats() {
    const statsContainer = document.getElementById('performanceStats');
    if (!statsContainer) return;
    
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_URL}/performance/stats`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const stats = await response.json();
        
        statsContainer.innerHTML = `
            <div class="grid grid-cols-2 gap-4">
                <div class="bg-blue-50 dark:bg-gray-700 p-4 rounded-lg">
                    <p class="text-sm text-gray-600 dark:text-gray-400">Sequential Time</p>
                    <p class="text-2xl font-bold text-blue-600">${stats.sequential_time?.toFixed(2) || 'N/A'}s</p>
                </div>
                <div class="bg-green-50 dark:bg-gray-700 p-4 rounded-lg">
                    <p class="text-sm text-gray-600 dark:text-gray-400">Parallel Time</p>
                    <p class="text-2xl font-bold text-green-600">${stats.parallel_time?.toFixed(2) || 'N/A'}s</p>
                </div>
                <div class="bg-purple-50 dark:bg-gray-700 p-4 rounded-lg">
                    <p class="text-sm text-gray-600 dark:text-gray-400">Speedup</p>
                    <p class="text-2xl font-bold text-purple-600">${stats.speedup?.toFixed(2) || 'N/A'}x</p>
                </div>
                <div class="bg-orange-50 dark:bg-gray-700 p-4 rounded-lg">
                    <p class="text-sm text-gray-600 dark:text-gray-400">Efficiency</p>
                    <p class="text-2xl font-bold text-orange-600">${stats.efficiency_percent?.toFixed(1) || 'N/A'}%</p>
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error loading performance stats:', error);
        statsContainer.innerHTML = '<p class="text-red-500">Error loading stats</p>';
    }
}

async function loadRecentlyViewed() {
    const container = document.getElementById('recentlyViewed');
    if (!container) return;
    
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_URL}/recently-viewed`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        
        if (data.recently_viewed && data.recently_viewed.length > 0) {
            container.innerHTML = data.recently_viewed.map(product => `
                <div class="flex items-center space-x-3 p-3 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg cursor-pointer"
                     onclick="viewProduct(${product.id})">
                    <img src="${product.image_url}" alt="${product.name}" class="w-12 h-12 rounded object-cover">
                    <div class="flex-1">
                        <p class="font-semibold dark:text-white">${product.name}</p>
                        <p class="text-sm text-gray-600 dark:text-gray-400">$${product.price}</p>
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p class="text-gray-500 dark:text-gray-400">No recently viewed items</p>';
        }
    } catch (error) {
        console.error('Error loading recently viewed:', error);
    }
}

async function loadFavorites() {
    const container = document.getElementById('favorites');
    if (!container) return;
    
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_URL}/favorites`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        
        if (data.favorites && data.favorites.length > 0) {
            container.innerHTML = data.favorites.map(product => `
                <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 cursor-pointer" onclick="viewProduct(${product.id})">
                    <img src="${product.image_url}" alt="${product.name}" class="w-full h-32 object-cover rounded mb-2">
                    <h4 class="font-semibold dark:text-white">${product.name}</h4>
                    <p class="text-blue-600 font-bold">$${product.price}</p>
                    <button onclick="event.stopPropagation(); removeFromFavorites(${product.id})" 
                            class="mt-2 text-red-600 text-sm hover:text-red-700">
                        <i class="fas fa-trash"></i> Remove
                    </button>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p class="text-gray-500 dark:text-gray-400 col-span-3">No favorites yet</p>';
        }
    } catch (error) {
        console.error('Error loading favorites:', error);
    }
}

async function removeFromFavorites(productId) {
    try {
        const token = localStorage.getItem('access_token');
        await fetch(`${API_URL}/favorites/${productId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        showToast('Removed from favorites', 'success');
        loadFavorites();
    } catch (error) {
        console.error('Error removing from favorites:', error);
        showToast('Error removing from favorites', 'error');
    }
}

function loadProfile() {
    const container = document.getElementById('profileInfo');
    if (!container || !currentUser) return;
    
    container.innerHTML = `
        <div class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">Username</label>
                <p class="mt-1 text-lg dark:text-white">${currentUser.username}</p>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">User ID</label>
                <p class="mt-1 text-lg dark:text-white">${currentUser.user_id}</p>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300">Member Since</label>
                <p class="mt-1 text-lg dark:text-white">${new Date().toLocaleDateString()}</p>
            </div>
            <button onclick="logout()" class="w-full bg-red-600 text-white py-2 rounded-lg hover:bg-red-700">
                <i class="fas fa-sign-out-alt"></i> Logout
            </button>
        </div>
    `;
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        warning: 'bg-yellow-500',
        info: 'bg-blue-500'
    };
    
    toast.className = `toast ${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg mb-3`;
    toast.innerHTML = `
        <div class="flex items-center">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'} mr-2"></i>
            <span>${message}</span>
        </div>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}