async function loadRecommendations() {
    const slider = document.getElementById('recommendationsSlider');
    if (!slider) return;
    
    slider.innerHTML = '<div class="loading-spinner mx-auto"></div>';
    
    try {
        const token = localStorage.getItem('access_token');
        if (!token) {
            slider.innerHTML = '<p class="text-gray-500 dark:text-gray-400 col-span-full">Please login to see personalized recommendations</p>';
            return;
        }
        
        const response = await fetch(`${API_URL}/recommendations?limit=10`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        
        if (data.recommendations && data.recommendations.length > 0) {
            displayRecommendations(data.recommendations);
            
            if (data.execution_time) {
                console.log(`Recommendations generated in ${data.execution_time.toFixed(3)}s`);
            }
        } else {
            slider.innerHTML = '<p class="text-gray-500 dark:text-gray-400 col-span-full">No recommendations available yet. Start browsing products!</p>';
        }
    } catch (error) {
        console.error('Error loading recommendations:', error);
        slider.innerHTML = '<p class="text-red-500">Error loading recommendations</p>';
    }
}

function displayRecommendations(products) {
    const slider = document.getElementById('recommendationsSlider');
    if (!slider) return;
    
    slider.innerHTML = '';
    
    products.forEach(product => {
        const card = document.createElement('div');
        card.className = 'product-card bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden cursor-pointer flex-shrink-0 w-64';
        card.onclick = () => viewProduct(product.id);
        
        card.innerHTML = `
            <img src="${product.image_url}" alt="${product.name}" class="w-full h-40 object-cover">
            <div class="p-3">
                <h3 class="font-semibold text-sm mb-1 dark:text-white truncate">${product.name}</h3>
                <p class="text-blue-600 font-bold">$${product.price}</p>
                <div class="flex items-center mt-1">
                    <i class="fas fa-star text-yellow-400 text-xs"></i>
                    <span class="text-xs ml-1 dark:text-white">${product.rating}</span>
                </div>
            </div>
        `;
        
        slider.appendChild(card);
    });
}

async function refreshRecommendations() {
    showToast('Refreshing recommendations...', 'info');
    
    // Clear cache by adding timestamp
    const slider = document.getElementById('recommendationsSlider');
    if (slider) {
        slider.innerHTML = '<div class="loading-spinner mx-auto"></div>';
    }
    
    try {
        const token = localStorage.getItem('access_token');
        if (!token) {
            showToast('Please login to see recommendations', 'warning');
            return;
        }
        
        const response = await fetch(`${API_URL}/recommendations?limit=10&refresh=true`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        
        if (data.recommendations && data.recommendations.length > 0) {
            displayRecommendations(data.recommendations);
            showToast('Recommendations refreshed!', 'success');
        } else {
            showToast('No recommendations available', 'warning');
        }
    } catch (error) {
        console.error('Error refreshing recommendations:', error);
        showToast('Error refreshing recommendations', 'error');
    }
}

// Performance test function
async function testPerformance() {
    if (!currentUser) {
        showToast('Please login to test performance', 'warning');
        return;
    }
    
    showToast('Running performance test...', 'info');
    
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(`${API_URL}/performance/test?num_users=10`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        
        if (data.performance_comparison) {
            const stats = data.performance_comparison;
            showToast(`Performance: ${stats.speedup.toFixed(2)}x speedup with ${stats.num_processes} processes`, 'success');
            
            // Log detailed stats
            console.log('Performance Comparison:', {
                'Sequential Time': `${stats.sequential_time.toFixed(3)}s`,
                'Parallel Time': `${stats.parallel_time.toFixed(3)}s`,
                'Speedup': `${stats.speedup.toFixed(2)}x`,
                'Efficiency': `${stats.efficiency_percent.toFixed(1)}%`
            });
        }
    } catch (error) {
        console.error('Error testing performance:', error);
        showToast('Error testing performance', 'error');
    }
}

// Add performance test button to dashboard
document.addEventListener('DOMContentLoaded', () => {
    const dashboard = document.getElementById('dashboardPage');
    if (dashboard) {
        const testButton = document.createElement('button');
        testButton.className = 'mt-4 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700';
        testButton.innerHTML = '<i class="fas fa-chart-line"></i> Test Performance';
        testButton.onclick = testPerformance;
        
        const statsCard = document.querySelector('#dashboardPage .card:first-child');
        if (statsCard) {
            statsCard.appendChild(testButton);
        }
    }
});