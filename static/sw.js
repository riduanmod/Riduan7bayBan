self.addEventListener('install', (e) => {
    console.log('[Service Worker] Install');
});

self.addEventListener('fetch', (e) => {
    // offline ক্যাশিং বা অন্যান্য ফিচারের জন্য, আপাতত ফাঁকা রাখলেই PWA কাজ করবে
});
