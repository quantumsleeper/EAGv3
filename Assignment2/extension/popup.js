document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('searchInput');
  const searchBtn = document.getElementById('searchBtn');
  const resultsContainer = document.getElementById('resultsContainer');
  const loader = document.getElementById('loader');

  async function performSearch() {
    const query = searchInput.value.trim();
    if (!query) return;

    resultsContainer.innerHTML = '';
    loader.style.display = 'block';

    try {
      const res = await fetch(`http://localhost:8000/search?q=${encodeURIComponent(query)}&limit=5`);
      const data = await res.json();
      
      loader.style.display = 'none';
      
      if (data.results && data.results.length > 0) {
        data.results.forEach(item => {
          const card = document.createElement('div');
          card.className = 'result-card';
          card.onclick = () => chrome.tabs.create({ url: item.url });

          let dateStr = 'Unknown date';
          if (item.timestamp) {
            dateStr = new Date(item.timestamp).toLocaleString();
          }

          card.innerHTML = `
            <img src="${item.screenshot}" alt="Screenshot" class="thumb">
            <div class="result-info">
              <h3>${item.title || item.url}</h3>
              <a href="#" class="url">${item.url}</a>
              <p class="summary">${item.summary || 'No summary...'}</p>
              <span class="timestamp">${dateStr}</span>
            </div>
          `;
          resultsContainer.appendChild(card);
        });
      } else {
        resultsContainer.innerHTML = '<p class="no-results">No matches found.</p>';
      }
    } catch (e) {
      loader.style.display = 'none';
      resultsContainer.innerHTML = `<p class="error">Error: Could not connect to local backend.</p>`;
    }
  }

  searchBtn.addEventListener('click', performSearch);
  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') performSearch();
  });
});
