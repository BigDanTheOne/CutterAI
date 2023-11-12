chrome.runtime.onInstalled.addListener(function() {
  fetch('http://localhost:5000/', { // Replace with actual server URL
    method: 'GET'
  }).then(response => response.text())
    .then(user_id => {
      chrome.storage.local.set({ user_id: user_id });
    });
});
