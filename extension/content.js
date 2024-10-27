// Create a search bar and results container
const searchBarContainer = document.createElement('div');
searchBarContainer.id = "customSearchBarContainer";
searchBarContainer.innerHTML = `
    <style>
        #customSearchBarContainer {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 20px;
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            width: 300px;
            min-width: 200px;
            min-height: 200px;
            height: auto;
            font-family: 'Poppins', sans-serif;
            color: #E2E8F0;
            overflow: hidden; /* Prevent overflowing content */
        }
        #customSearchBarHeader {
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: move;
            background: rgba(255, 255, 255, 0.1);
            padding: 10px 15px;
            border-radius: 20px 20px 0 0;
            color: #FF6600;
            font-weight: 600;
        }
        #queryInput {
            width: calc(100% - 20px);
            padding: 10px;
            margin: 10px;
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            color: #E2E8F0;
            font-size: 14px;
        }
        #queryInput::placeholder {
            color: rgba(226, 232, 240, 0.6);
        }
        #queryBtn {
            padding: 10px 15px;
            cursor: pointer;
            margin: 0 10px 10px;
            background-color: #FF6600;
            color: #0F172A;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        #queryBtn:hover {
            opacity: 0.9;
            transform: translateY(-2px);
        }
        #closeBtn {
            background: none;
            color: #FF6600;
            border: none;
            cursor: pointer;
            font-size: 18px;
            padding: 5px;
        }
        #searchResults {
            margin: 10px;
            max-height: 200px;
            overflow-y: auto;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            padding-top: 10px;
            color: #E2E8F0;
        }
        #searchResults::-webkit-scrollbar {
            width: 8px;
        }
        #searchResults::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05);
        }
        #searchResults::-webkit-scrollbar-thumb {
            background-color: rgba(255, 255, 255, 0.2);
            border-radius: 4px;
        }
        /* Loading spinner */
        .loading-spinner {
            width: 40px;
            height: 40px;
            border: 5px solid rgba(255, 255, 255, 0.3);
            border-top: 5px solid #FF6600;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        /* Resizable handle at the lower-left corner */
        #resizeHandle {
            width: 20px;
            height: 20px;
            background: #FF6600;
            position: absolute;
            left: 0;
            bottom: 0;
            cursor: sw-resize; /* South-West resize cursor */
            border-bottom-left-radius: 20px;
        }
    </style>
    <div id="customSearchBarHeader">
        <span>Ragify Search</span>
        <button id="closeBtn">×</button>
    </div>
    <input type="text" id="queryInput" placeholder="Ask something...">
    <button id="queryBtn">Search</button>
    <div id="searchResults"></div>
    <div id="resizeHandle"></div> <!-- Resize handle for bottom-left corner -->
`;

document.body.appendChild(searchBarContainer);

// Close button functionality
document.getElementById('closeBtn').addEventListener('click', function() {
    document.getElementById('customSearchBarContainer').remove();
});



let isDragging = false;

const header = document.getElementById('customSearchBarHeader');
header.onmousedown = function(event) {
    event.preventDefault();
    isDragging = true;

    let shiftX = event.clientX - searchBarContainer.getBoundingClientRect().left;
    let shiftY = event.clientY - searchBarContainer.getBoundingClientRect().top;

    // Switch to absolute positioning for proper dragging
    searchBarContainer.style.position = 'absolute';

    function moveAt(pageX, pageY) {
        searchBarContainer.style.left = pageX - shiftX + 'px';
        searchBarContainer.style.top = pageY - shiftY + 'px';
    }

    function onMouseMove(event) {
        if (isDragging) {
            moveAt(event.pageX, event.pageY);
        }
    }

    document.addEventListener('mousemove', onMouseMove);

    // Stop dragging on mouse up
    document.onmouseup = function() {
        isDragging = false;
        document.removeEventListener('mousemove', onMouseMove);
        document.onmouseup = null;
    };
};

// Prevent default drag behavior
header.ondragstart = function() {
    return false;
};

// Add resize functionality (only bottom-left corner)
// Add resize functionality (bottom-left corner)
const resizeHandle = document.getElementById('resizeHandle');
let isResizing = false;

resizeHandle.onmousedown = function(event) {
    event.preventDefault();
    isResizing = true;

    const initialWidth = searchBarContainer.offsetWidth;
    const initialHeight = searchBarContainer.offsetHeight;
    const initialX = event.clientX;
    const initialY = event.clientY;
    const initialLeft = searchBarContainer.getBoundingClientRect().left;

    function onMouseMove(event) {
        if (isResizing) {
            const deltaX = initialX - event.clientX; // Difference in the X-axis
            const deltaY = event.clientY - initialY; // Difference in the Y-axis

            const newWidth = initialWidth + deltaX; // Resize leftward
            const newHeight = initialHeight + deltaY; // Resize downward
            const newLeft = initialLeft - deltaX; // Adjust left position

            // Ensure minimum width and height
            if (newWidth > 200) {
                searchBarContainer.style.width = newWidth + 'px';
                searchBarContainer.style.left = newLeft + 'px'; // Move left position
            }
            if (newHeight > 200) {
                searchBarContainer.style.height = newHeight + 'px';
            }
        }
    }

    document.addEventListener('mousemove', onMouseMove);

    // Stop resizing on mouse up
    document.onmouseup = function() {
        isResizing = false;
        document.removeEventListener('mousemove', onMouseMove);
        document.onmouseup = null;
    };
};

// Prevent default resize behavior
resizeHandle.ondragstart = function() {
    return false;
};



// Add event listener to capture query and show loading spinner
document.getElementById('queryBtn').addEventListener('click', function() {
    const query = document.getElementById('queryInput').value;
    const resultsContainer = document.getElementById('searchResults');
    const url = window.location.href;
    console.log("url::",url)
    if (query) {
        // Show the loading spinner
        resultsContainer.innerHTML = '<div class="loading-spinner"></div>';

        // Send query to your backend
        fetch('http://127.0.0.1:8008/query', {
            method: 'POST',
            body: JSON.stringify({ query: query , url: url}),
            headers: { 'Content-Type': 'application/json' }
        })
        .then(response => response.json())
        .then(data => {
            resultsContainer.innerHTML = ''; // Clear previous results
            
            // Display the new results
            if (data.results && data.results.length > 0) {
                console.log(data.results);
                resultsContainer.innerText = data.results;
            } else {
                resultsContainer.innerText = 'No results found.';
            }
            
            // Display clickable links
            if (data.links && data.links.length > 0) {
                const linksContainer = document.createElement('div');
                linksContainer.setAttribute('id', 'linksContainer');
                resultsContainer.appendChild(linksContainer);
                
                data.links.forEach(link => {
                    const linkElement = document.createElement('a');
                    linkElement.href = link;
                    linkElement.target = '_blank'; // Open link in a new tab
                    linkElement.innerText = link;
                    linkElement.style.display = 'block'; // Show each link on a new line
                    linkElement.style.color = "#FF6600";
                    linkElement.style.paddingTop = "10px";
                    linksContainer.appendChild(linkElement);
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            resultsContainer.innerText = 'Error fetching results.';
        });
    } else {
        alert('Please enter a query.');
    }
});
