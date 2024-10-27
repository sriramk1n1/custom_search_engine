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
                <span title="${page.url}">
                    <svg viewBox="0 0 24 24" class="icon"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z"/></svg>
                    <a href="${page.url}" target="_blank" > ${page.url} </a>
                </span>
                <span class="status ora status-${page.status}">${page.status}</span>
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

    function handleDownload(e){
        console.log("HHHHIIII")
        const id = e.target.closest('.download').dataset.id;
        fetch('/download', {
            method: "POST",
            headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                },
            body: new URLSearchParams({ pageid: id })
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.blob();
            })
            .then(blob => {
                let filename = 'output.zip';

                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename; // Set filename dynamically based on header
                document.body.appendChild(a); // Append link to the body
                a.click(); // Trigger download
                a.remove(); // Remove link after download
                window.URL.revokeObjectURL(url); // Release the blob URL
            })
            .catch(error => {
                    console.error('There was a problem with the fetch operation:', error);
        });
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
