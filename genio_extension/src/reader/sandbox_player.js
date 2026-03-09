document.addEventListener('DOMContentLoaded', () => {
    const urlParams = new URLSearchParams(window.location.search);
    const videoId = urlParams.get('v');
    const playerDiv = document.getElementById('player');

    if (videoId) {
        const iframe = document.createElement('iframe');
        // Usiamo youtube.com. Le regole DNR (rules.json) gestiranno gli header.
        iframe.src = `https://www.youtube.com/embed/${videoId}?autoplay=0&rel=0&modestbranding=1&playsinline=1`;

        iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share";
        iframe.allowFullscreen = true;

        // Stile per riempire la pagina
        iframe.style.width = "100%";
        iframe.style.height = "100%";
        iframe.style.border = "0";

        playerDiv.appendChild(iframe);
    } else {
        document.body.innerHTML = '<p style="color:#aaa;text-align:center;padding-top:20%;font-family:sans-serif;">Video ID not found</p>';
    }
});