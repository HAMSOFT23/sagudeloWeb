const postsContainer = document.getElementById('posts-container');
const loader = document.getElementById('loader');

// Get the first content block to use as a template for cloning
const originalContent = document.querySelector('.repeat-item');
let isFetching = false; // Flag to prevent multiple loads at once

// Function to clone and add the original content
function cloneAndAppendContent() {
    // Use cloneNode(true) to make a deep copy of the content element
    const clone = originalContent.cloneNode(true);
    postsContainer.appendChild(clone);
}

// Function to show the loader
function showLoader() {
    loader.style.display = 'block';
}

// Function to hide the loader
function hideLoader() {
    loader.style.display = 'none';
}

// Function to load more content
function loadMoreContent() {
    if (isFetching) return; // Prevent multiple fetches
    isFetching = true;
    showLoader();
    
    // Simulate a network request delay
    setTimeout(() => {
        cloneAndAppendContent();
        hideLoader();
        isFetching = false;
    }, 1000); // 1-second delay
}

// Event listener for scrolling
window.addEventListener('scroll', () => {
    const { scrollTop, scrollHeight, clientHeight } = document.documentElement;

    // Check if the user has scrolled near the bottom
    if (scrollTop + clientHeight >= scrollHeight - 5) {
        loadMoreContent();
    }
});