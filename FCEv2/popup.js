// popup.js - Updated with IndexedDB and export functionality
document.addEventListener('DOMContentLoaded', function() {
  // Get DOM elements
  const apiKeyInput = document.getElementById('apiKey');
  const saveKeyButton = document.getElementById('saveKey');
  const selectedTextArea = document.getElementById('selectedText');
  const promptTemplate = document.getElementById('prompt');
  const sendButton = document.getElementById('sendButton');
  const responseContainer = document.getElementById('responseContainer');
  const geminiResponse = document.getElementById('geminiResponse');
  const loadingIndicator = document.getElementById('loadingIndicator');
  const errorContainer = document.getElementById('errorContainer');
  const errorMessage = document.getElementById('errorMessage');
  const copyButton = document.getElementById('copyResponse');
  const flashCardsList = document.getElementById('flashCardsList');
  const tabButtons = document.querySelectorAll('.tab-button');
  const tabContents = document.querySelectorAll('.tab-content');
  const exportButton = document.getElementById('exportBtn'); // Add this for the export button
  
  // Make sure dbService is accessible
  if (!window.dbService) {
    // Include the database service if it's not already loaded
    const script = document.createElement('script');
    script.src = 'db-service.js';
    document.head.appendChild(script);
    
    script.onload = function() {
      console.log("Database service loaded");
      initializeApp();
    };
    
    script.onerror = function() {
      console.error("Failed to load database service");
      showError("Failed to load database service. Please reload the extension.");
    };
  } else {
    initializeApp();
  }
  
  function initializeApp() {
    // Initialize the database
    window.dbService.initDB().then(() => {
      // Set default flash card prompt
      promptTemplate.value = `Create 3 flash cards from the following text. Each flash card should have:
1. A concise question or concept on the front
2. A clear, comprehensive answer on the back
3. 2-3 relevant tags

Format each flash card like this:
CARD 1:
Front: [question/concept]
Back: [answer/explanation]
Tags: [tag1, tag2, tag3]

CARD 2:
Front: [question/concept]
Back: [answer/explanation]
Tags: [tag1, tag2, tag3]

CARD 3:
Front: [question/concept]
Back: [answer/explanation]
Tags: [tag1, tag2, tag3]

Make each flash card focus on a different important concept from the text.`;
  
      // Load settings
      loadSettings();
      
      // Load any pending text
      loadPendingText();
      
      // Initial load of flash cards if on cards tab
      if (document.querySelector('.tab-button[data-tab="cards-tab"].active')) {
        loadFlashCards();
      }
    }).catch(error => {
      console.error("Failed to initialize database:", error);
      showError("Failed to initialize database. Please reload the extension.");
    });
  }
  
  // Tab switching
  tabButtons.forEach(button => {
    button.addEventListener('click', () => {
      // Remove active class from all buttons and contents
      tabButtons.forEach(btn => btn.classList.remove('active'));
      tabContents.forEach(content => content.classList.remove('active'));
      
      // Add active class to clicked button and corresponding content
      button.classList.add('active');
      const tabId = button.getAttribute('data-tab');
      document.getElementById(tabId).classList.add('active');
      
      // If switching to cards tab, refresh the cards list
      if (tabId === 'cards-tab') {
        loadFlashCards();
      }
    });
  });
  
  // Save API key
  saveKeyButton.addEventListener('click', async () => {
    const apiKey = apiKeyInput.value.trim();
    if (apiKey) {
      try {
        await window.dbService.saveSetting("geminiApiKey", apiKey);
        showNotification("API key saved!");
      } catch (error) {
        alert("Error saving API key: " + error.message);
      }
    } else {
      alert("Please enter a valid API key.");
    }
  });
  
  // Load selected text
  async function loadPendingText() {
    try {
      const settings = await window.dbService.getMultipleSettings(["geminiInput", "timestamp", "pendingMessage"]);
      
      if (settings.geminiInput) {
        selectedTextArea.value = settings.geminiInput;
        
        // Add timestamp info if available
        if (settings.timestamp) {
          const date = new Date(settings.timestamp);
          const timeString = date.toLocaleTimeString();
          document.title = `Flash Cards - ${timeString}`;
        }
        
        // Show pending message if any
        if (settings.pendingMessage) {
          showNotification(settings.pendingMessage, "info", 5000);
          // Clear the pending message after showing
          await window.dbService.saveSetting("pendingMessage", null);
        }
      }
    } catch (error) {
      console.error("Error loading pending text:", error);
    }
  }
  
  // Send to Gemini
  sendButton.addEventListener('click', async () => {
    // Get API key and text
    const apiKey = apiKeyInput.value.trim();
    const text = selectedTextArea.value.trim();
    const customPrompt = promptTemplate.value.trim();
    
    // Validate inputs
    if (!apiKey) {
      showError("Please enter a Gemini API key.");
      return;
    }
    
    if (!text) {
      showError("No text selected.");
      return;
    }
    
    // Prepare for request
    hideError();
    showLoading();
    hideResponse();
    
    try {
      // Prepare the full prompt text
      const fullPrompt = `${customPrompt}\n\nText: ${text}`;
      
      // Call Gemini API using the exact format from the example
      const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          contents: [
            {
              parts: [
                { 
                  text: fullPrompt 
                }
              ]
            }
          ]
        })
      });
      
      // Parse response
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Gemini API Error (${response.status}): ${errorText}`);
      }
      
      const data = await response.json();
      
      // Log the complete response for debugging
      console.log("Full Gemini API response:", data);
      
      // Store complete response in IndexedDB for debugging
      await window.dbService.saveSetting("lastGeminiResponse", data);
      await window.dbService.saveSetting("responseTimestamp", new Date().toISOString());
      
      // Extract and display text
      if (data.candidates && data.candidates[0] && data.candidates[0].content && 
          data.candidates[0].content.parts && data.candidates[0].content.parts[0]) {
        const content = data.candidates[0].content.parts[0].text;
        showResponse(content);
        
        // Parse flash cards
        try {
          const cards = parseFlashCards(content, text);
          await window.dbService.saveFlashCards(cards);
          updateCardCount();
          showNotification(`Created ${cards.length} flash cards!`);
        } catch (parseError) {
          console.error("Error parsing flash cards:", parseError);
          showNotification("Error parsing cards, but response shown", "error");
        }
      } else {
        throw new Error("Unexpected response format from Gemini");
      }
    } catch (error) {
      showError(error.message);
      console.error("Gemini request error:", error);
    } finally {
      hideLoading();
    }
  });
  
  // Parse Gemini response into flash card objects
  function parseFlashCards(content, originalText) {
    try {
      const cards = [];
      const cardBlocks = content.split(/CARD \d+:/g).filter(block => block.trim().length > 0);
      
      // Manual parsing of the cards
      for (const block of cardBlocks) {
        // Extract front
        const frontMatch = block.match(/Front:\s*(.*?)(?=Back:|$)/s);
        // Extract back
        const backMatch = block.match(/Back:\s*(.*?)(?=Tags:|$)/s);
        // Extract tags
        const tagsMatch = block.match(/Tags:\s*(.*?)(?=CARD \d+:|$)/s);
        
        if (frontMatch && backMatch) {
          const front = frontMatch[1].trim();
          const back = backMatch[1].trim();
          
          // Parse tags or use default
          let tags = [];
          if (tagsMatch && tagsMatch[1]) {
            tags = tagsMatch[1].split(',').map(tag => tag.trim()).filter(tag => tag.length > 0);
          }
          
          // Create card object
          cards.push({
            id: Date.now() + cards.length, // Unique ID
            front: front,
            back: back,
            tags: tags,
            created: new Date().toISOString(),
            source: originalText.substring(0, 150) + (originalText.length > 150 ? "..." : ""),
            lastReviewed: null
          });
        }
      }
      
      // If we couldn't parse any cards, throw error
      if (cards.length === 0) {
        throw new Error("Could not parse any flash cards from the response");
      }
      
      return cards;
    } catch (error) {
      console.error("Error parsing flash cards:", error);
      throw error;
    }
  }
  
  // Load settings
  async function loadSettings() {
    try {
      // Load API key if stored
      const apiKey = await window.dbService.getSetting("geminiApiKey");
      if (apiKey) {
        apiKeyInput.value = apiKey;
      }
      
      // Update card count
      updateCardCount();
    } catch (error) {
      console.error("Error loading settings:", error);
    }
  }
  
  // Update card count in UI
  async function updateCardCount() {
    try {
      const cards = await window.dbService.getAllFlashCards();
      const cardCount = cards.length;
      const countElement = document.getElementById('cardCount');
      if (countElement) {
        countElement.textContent = cardCount;
      }
    } catch (error) {
      console.error("Error updating card count:", error);
    }
  }
  
  // Load and display flash cards
  async function loadFlashCards() {
    if (!flashCardsList) return;
    
    try {
      const cards = await window.dbService.getAllFlashCards();
      
      if (cards.length === 0) {
        flashCardsList.innerHTML = '<div class="no-cards">No flash cards yet. Create some by selecting text on a webpage.</div>';
        return;
      }
      
      // Sort by creation date (newest first)
      cards.sort((a, b) => new Date(b.created) - new Date(a.created));
      
      // Generate HTML for cards
      flashCardsList.innerHTML = '';
      
      cards.forEach((card, index) => {
        const cardDiv = document.createElement('div');
        cardDiv.className = 'card';
        cardDiv.setAttribute('data-id', card.id);
        
        cardDiv.innerHTML = `
          <div class="card-header">
            <div class="card-number">Card ${index + 1}</div>
            <button class="delete-card" data-id="${card.id}">Delete</button>
          </div>
          <label>Front:</label>
          <div class="response">${escapeHtml(card.front)}</div>
          <label>Back:</label>
          <div class="response">${escapeHtml(card.back)}</div>
          ${card.tags && card.tags.length > 0 ? `
            <label>Tags:</label>
            <div>${card.tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join(' ')}</div>
          ` : ''}
          <div style="font-size:12px; margin-top:10px; color:#666;">
            Created: ${new Date(card.created).toLocaleString()}
          </div>
        `;
        
        flashCardsList.appendChild(cardDiv);
      });
      
      // Add event listeners to delete buttons
      document.querySelectorAll('.delete-card').forEach(button => {
        button.addEventListener('click', async (event) => {
          const cardId = Number(event.target.getAttribute('data-id'));
          await deleteFlashCard(cardId);
        });
      });
    } catch (error) {
      console.error("Error loading flash cards:", error);
      flashCardsList.innerHTML = '<div class="error">Error loading flash cards. Please try again.</div>';
    }
  }
  
  // Delete a flash card
  async function deleteFlashCard(cardId) {
    if (confirm("Are you sure you want to delete this flash card?")) {
      try {
        await window.dbService.deleteFlashCard(cardId);
        loadFlashCards();
        updateCardCount();
        showNotification("Flash card deleted!");
      } catch (error) {
        console.error("Error deleting flash card:", error);
        showNotification("Error deleting flash card", "error");
      }
    }
  }
  
  // EXPORT FUNCTIONALITY - New code for exporting flash cards to JSON file
  async function exportFlashCards() {
    try {
      // Get all flash cards from IndexedDB
      const cards = await window.dbService.getAllFlashCards();
      
      if (cards.length === 0) {
        showNotification("No flash cards to export", "error");
        return;
      }
      
      // Convert to JSON string with pretty formatting
      const jsonData = JSON.stringify(cards, null, 2);
      
      // Create a blob and download link
      const blob = new Blob([jsonData], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      
      // Create and trigger download
      const a = document.createElement('a');
      a.href = url;
      a.download = 'flashcards.json';
      document.body.appendChild(a);
      a.click();
      
      // Clean up
      setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }, 100);
      
      showNotification(`Exported ${cards.length} flash cards successfully!`, "success");
    } catch (error) {
      console.error("Error exporting flash cards:", error);
      showNotification("Error exporting flash cards: " + error.message, "error");
    }
  }
  
  // Copy response to clipboard
  copyButton.addEventListener('click', () => {
    const responseText = geminiResponse.textContent;
    navigator.clipboard.writeText(responseText)
      .then(() => {
        showNotification("Copied to clipboard!");
      })
      .catch(err => {
        console.error("Copy failed:", err);
        showNotification("Failed to copy text", "error");
      });
  });
  
  // Add event listener for the export button if it exists
  if (exportButton) {
    exportButton.addEventListener('click', exportFlashCards);
  }
  
  // Helper functions
  function showLoading() {
    loadingIndicator.classList.remove('hidden');
  }
  
  function hideLoading() {
    loadingIndicator.classList.add('hidden');
  }
  
  function showResponse(text) {
    geminiResponse.textContent = text;
    responseContainer.classList.remove('hidden');
  }
  
  function hideResponse() {
    responseContainer.classList.add('hidden');
  }
  
  function showError(message) {
    errorMessage.textContent = message;
    errorContainer.classList.remove('hidden');
  }
  
  function hideError() {
    errorContainer.classList.add('hidden');
  }
  
  // Escape HTML to prevent XSS
  function escapeHtml(text) {
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
  
  // Show notification
  function showNotification(message, type = "success", duration = 3000) {
    // Create notification element
    const notification = document.createElement('div');
    notification.textContent = message;
    notification.className = 'notification';
    
    // Set color based on type
    if (type === "error") {
      notification.style.backgroundColor = "#F44336";
    } else if (type === "info") {
      notification.style.backgroundColor = "#2196F3";
    }
    
    // Add to DOM
    document.body.appendChild(notification);
    
    // Trigger animation
    setTimeout(() => {
      notification.classList.add('show');
      
      // Remove after delay
      setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
          if (document.body.contains(notification)) {
            document.body.removeChild(notification);
          }
        }, 300);
      }, duration);
    }, 10);
  }
});
