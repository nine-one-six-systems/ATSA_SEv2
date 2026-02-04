// Joint Analysis JavaScript
// Placeholder - will be implemented in Plan 03-02

document.addEventListener('DOMContentLoaded', function() {
    console.log('Joint Analysis page loaded');

    // Initialize Split.js if available and not on mobile
    if (typeof Split !== 'undefined' && window.innerWidth > 768) {
        Split(['#spouse1-panel', '#spouse2-panel'], {
            sizes: [50, 50],
            minSize: 200,
            gutterSize: 10,
            cursor: 'col-resize'
        });
    }
});
