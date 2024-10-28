document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    socket.on('update', function(msg) {
        fetch(`/pages`)
                .then(response => response.json())
                .then(data => {
                    pages = data;
                    renderPages();
                })
                .catch(error => {
                    console.error('Error fetching status:', error);
                    clearInterval(intervalId); // Stop polling if there's an error
                });
    });

    socket.on('count', function(data) {
        const counter = document.getElementById(`counter${data.hash}`);
        counter.innerText=data.value;
    });

    const urlInput = document.getElementById('urlInput');
    const crawlButton = document.getElementById('crawlButton');
    const popupOverlay = document.getElementById('popupOverlay');
    const confirmCrawlButton = document.getElementById('confirmCrawlButton');
    const closePopupButton = document.getElementById('closePopupButton');
    const pagesList = document.getElementById('pagesList');
    let pages = [];

    let currentEndpoint = '/crawl'; // Default endpoint for crawling

    // Show popup with specified endpoint when 'Crawl' button is clicked
    crawlButton.addEventListener('click', () => {
        currentEndpoint = '/crawl';
        popupOverlay.style.display = 'flex';
    });

    // Close popup when 'Cancel' button is clicked
    closePopupButton.addEventListener('click', () => {
        popupOverlay.style.display = 'none';
    });

    // Send crawl data when 'Start Crawl' button in popup is clicked
    confirmCrawlButton.addEventListener('click', () => {
        const url = urlInput.value.trim();
        const threads = document.getElementById('threads').value;
        const pattern = document.getElementById('pattern').value;
        const iterations = document.getElementById('iterations').value;
        const linksToCrawl = document.getElementById('linksToCrawl').value;

        if (!url || !threads || !iterations || !linksToCrawl) {
            alert('Please fill in all fields.');
            return;
        }

        fetch(currentEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                url: url,
                threads: threads,
                pattern: pattern,
                iterations: iterations,
                linksToCrawl: linksToCrawl,
                socket_id: socket.id
            })
        })
        .then(response => response.json())
        .then(data => {
            if (currentEndpoint === '/crawl') {
                pages.unshift(data);
                renderPages();
                urlInput.value = ''; // Clear the URL input field
            } else {
                for (let page of pages) {
                    if (page.url === url) {
                      const [crawled, uncrawled] = page.status.match(/\d+ crawled, \d+ remaining/)[0].split(", ");
                      page.status = `${crawled}, ${uncrawled}, Crawling...`;
                      renderPages();
                      break;
                    }
                  }
            }
            
            popupOverlay.style.display = 'none';

        })
        .catch(error => console.error('Error:', error));
    });


    function getFaviconUrl(url) {
        try {
            const parsedUrl = new URL(url);
            const baseUrl = `${parsedUrl.protocol}//${parsedUrl.host}`;
            return `${baseUrl}/favicon.ico`;
        } catch (error) {
            console.error("Invalid URL:", error);
            return null;
        }
    }

    function renderPages() {
        pagesList.innerHTML = '';
        pages.forEach(page => {
            const li = document.createElement('li');
            li.className = 'page-item';
            li.innerHTML = `
                <span title="${page.url}" style="flex-grow: 1">
                    <img style="padding-top:6px; padding-right:4px" height="18" width="20" src='http://www.google.com/s2/favicons?domain=${page.url}' />
                    <a class="myurl" href="${page.url}" target="_blank" > ${truncateUrl(page.url)} </a>
                </span>
                <span class="status ora status-${page.status}">${page.status}</span>
                <span class="status ora status-${page.status}" id="counter${page.id}"></span>
                <div class="actions">
                    <button class="crawl" data-id="${page.url}" title="Crawl again">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
                            <path d="M12 4V1l-4 4 4 4V5a7 7 0 1 1-6 10.9l-2.3-2.3A9 9 0 1 0 12 4z"/>
                        </svg>
                    </button>
                    <button class="goto" data-id="${page.id}" title="Goto Search for this page">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-link">
                            <path d="M10 13H7a4 4 0 0 1-4-4V5a4 4 0 0 1 4-4h3a4 4 0 0 1 4 4v3"></path>
                            <path d="M14 11h3a4 4 0 0 1 4 4v4a4 4 0 0 1-4 4h-3a4 4 0 0 1-4-4v-4"></path>
                        </svg>
                    </button>
                    
                    <button class="download" data-id="${page.id}" title="Download" onclick="window.open('/download/${page.id}', '_blank')"
>
                    
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-download">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                        <polyline points="7 10 12 15 17 10" />
                        <line x1="12" y1="15" x2="12" y2="3" />
                    </svg>
                </button>
                    <button class="delete" data-id="${page.id}" title="Delete">
                        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-trash">
                            <polyline points="3 6 5 6 21 6" />
                            <path d="M19 6l-2 14H7L5 6" />
                            <path d="M10 11v6" />
                            <path d="M14 11v6" />
                        </svg>
                    </button>
                </div>
            `;
            pagesList.appendChild(li);
        });

        function truncateUrl(url) {
            if (url.length > 30) {
                return url.slice(0, 30) + "..."; // Truncate and add ellipsis
            }
            return url; // Return the full URL if it's short enough
        }

        // Add event listeners to buttons
        document.querySelectorAll('.delete').forEach(button => {
            button.addEventListener('click', handleDelete);
        });
        document.querySelectorAll('.crawl').forEach(button => {
            button.addEventListener('click', handleCrawl);
        });
        document.querySelectorAll('.goto').forEach(button => {
            button.addEventListener('click', handleGoto);
        });
        // document.querySelectorAll('.download').forEach(button => {
        //     button.addEventListener('click', handleDownload)
        // })
    }


    function handleGoto(e){
        const id = e.target.closest('.goto').dataset.id;
        window.location.assign("/search/"+id);
    }

    function handleCrawl(e) {
        const url = e.target.closest('.crawl').dataset.id;
        urlInput.value = url; // Prefill URL input
        currentEndpoint = '/crawlnext'; // Set to '/crawlnext' for next crawl
        popupOverlay.style.display = 'flex'; // Show popup
    }

    function handleDelete(e) {
        const id = e.target.closest('.delete').dataset.id; // Get the ID from the button
        pages = pages.filter(item => item.id !== id);
        renderPages();
        try {
            fetch("/delete", {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                body: new URLSearchParams({ pageid: id })
            });
        } catch (error) {
            console.error("Error:", error);
        }
    }

    fetch(`/pages`)
    .then(response => response.json())
    .then(data => {
        pages = data;
        renderPages();
    })
    .catch(error => {
        console.error('Error fetching status:', error);
    });
});
