// Server URL
const serverUrl = 'http://localhost:5000'; // Replace with actual server URL

// Upload File
document.getElementById('upload-button').addEventListener('click', function() {
  const fileInput = document.getElementById('file-input');
  const file = fileInput.files[0];
  if (file) {
    const formData = new FormData();
    formData.append('file', file);
    fetch(`${serverUrl}/upload`, {
      method: 'POST',
      body: formData
    }).then(response => response.json())
      .then(data => {
        document.getElementById('status').textContent = 'Upload successful. File ID: ' + data.file_id;
      }).catch(error => {
        document.getElementById('status').textContent = 'Upload failed: ' + error;
      });
  } else {
    document.getElementById('status').textContent = 'No file selected.';
  }
});

// Ask Question
document.getElementById('ask-button').addEventListener('click', function() {
  const questionInput = document.getElementById('question-input');
  const question = questionInput.value;
  if (question) {
    fetch(`${serverUrl}/ask-question`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ question: question })
    }).then(response => response.json())
      .then(data => {
        document.getElementById('status').innerHTML = 'Answer: ' + data.answer;
      }).catch(error => {
        document.getElementById('status').textContent = 'Error: ' + error;
      });
  } else {
    document.getElementById('status').textContent = 'Please enter a question.';
  }
});

// Get Chat History
document.getElementById('get-history-button').addEventListener('click', function() {
  chrome.storage.local.get(['user_id'], function(result) {
    if (result.user_id) {
      fetch(`${serverUrl}/get-chat-history`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'user_id': result.user_id // Assuming 'user_id' is sent as a header
        }
      }).then(response => response.json())
        .then(data => {
          document.getElementById('status').textContent = 'Chat History: ' + JSON.stringify(data);
        }).catch(error => {
          document.getElementById('status').textContent = 'Error retrieving history: ' + error;
        });
    } else {
      document.getElementById('status').textContent = 'No user_id found.';
    }
  });
});
