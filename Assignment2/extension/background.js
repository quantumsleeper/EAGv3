const SENSITIVE_KEYWORDS = [
  'chrome://', 'about:', 'chrome-extension://',
  'login', 'auth', 'checkout', 'bank', 'password', 'myaccount', 'admin'
];

function isSensitive(url) {
  if (!url) return true;
  const lowerUrl = url.toLowerCase();
  for (const keyword of SENSITIVE_KEYWORDS) {
    if (lowerUrl.includes(keyword)) {
      return true;
    }
  }
  return false;
}

const pendingCaptures = new Map();

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete') {
    if (isSensitive(tab.url)) {
      console.log(`Ignoring sensitive or restricted URL: ${tab.url}`);
      return;
    }

    if (pendingCaptures.has(tabId)) {
      clearTimeout(pendingCaptures.get(tabId));
    }

    const timerId = setTimeout(() => {
      captureAndIngest(tabId, tab.url, tab.title);
      pendingCaptures.delete(tabId);
    }, 5000);

    pendingCaptures.set(tabId, timerId);
  }
});

chrome.tabs.onRemoved.addListener((tabId) => {
  if (pendingCaptures.has(tabId)) {
    clearTimeout(pendingCaptures.get(tabId));
    pendingCaptures.delete(tabId);
  }
});

async function captureAndIngest(tabId, url, title) {
  try {
    const [{ result: textContent }] = await chrome.scripting.executeScript({
      target: { tabId: tabId },
      func: () => document.body.innerText
    });

    const tab = await chrome.tabs.get(tabId);
    // Only active tabs can be captured by captureVisibleTab
    if (!tab.active) {
      console.log(`Tab ${tabId} is not active, skipping capture to avoid errors.`);
      return;
    }

    const dataUrl = await chrome.tabs.captureVisibleTab(tab.windowId, { format: 'jpeg', quality: 30 });
    
    const response = await fetch('http://localhost:8000/ingest', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        url: url,
        title: title || '',
        text_content: textContent || '',
        base64_image: dataUrl
      })
    });
    
    const result = await response.json();
    console.log("Ingested successfully:", result);
  } catch (err) {
    console.error("Error during capture and ingest:", err);
  }
}
