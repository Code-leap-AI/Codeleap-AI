// background.js - Automated version with IndexedDB
// Import the database service using importScripts
importScripts('db-service.js');

// Create context menu on install
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "createFlashCards",
    title: "Create Flash Cards",
    contexts: ["selection"]
  });
  console.log("Flash Card Generator extension installed");
  
  // Initialize IndexedDB when extension is installed
  dbService.initDB().then(() => {
    console.log("IndexedDB initialized");
  }).catch(error => {
    console.error("Failed to initialize IndexedDB:", error);
  });
});

// Handle context menu click
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "createFlashCards" && info.selectionText) {
    console.log("Creating flash cards from selected text:", info.selectionText.substring(0, 50) + "...");
    
    // Get stored API key
    dbService.getSetting("geminiApiKey").then(async (apiKey) => {
      if (!apiKey) {
        // No API key stored, store the selected text and open popup to prompt for key
        await dbService.saveSetting("geminiInput", info.selectionText);
        await dbService.saveSetting("timestamp", new Date().toISOString());
        await dbService.saveSetting("pendingMessage", "Please enter your Gemini API key to create flash cards.");
        chrome.action.openPopup();
        return;
      }
      
      // Show notification in the page - WITH ERROR HANDLING
      try {
        // First check if tab exists
        const tabDetails = await chrome.tabs.get(tab.id);
        if (!tabDetails) {
          console.log("Tab no longer exists");
          return;
        }
        
        // Then safely send a message with a response checked
        chrome.tabs.sendMessage(tab.id, {
          action: "showNotification",
          message: "Creating flash cards...",
          type: "info"
        }, (response) => {
          // Check for error, which could be caused by receiving end not existing
          if (chrome.runtime.lastError) {
            console.warn("Could not send notification:", chrome.runtime.lastError.message);
            // Continue with the process even if notification failed
          } else {
            console.log("Notification shown successfully:", response);
          }
        });
      } catch (error) {
        console.warn("Error showing notification:", error);
        // Continue with the process even if notification failed
      }
      
      try {
        // Generate cards automatically
        const cards = await generateFlashCards(info.selectionText, apiKey);
        
        // Save cards to IndexedDB
        const cardCount = await dbService.saveFlashCards(cards);
        
        // Notify success - WITH ERROR HANDLING
        try {
          chrome.tabs.sendMessage(tab.id, {
            action: "showNotification",
            message: `Created ${cardCount} flash cards! Click extension icon to view.`,
            type: "success"
          }, () => {
            // Ignore response errors
            if (chrome.runtime.lastError) {
              console.warn("Could not send success notification:", chrome.runtime.lastError.message);
            }
          });
        } catch (error) {
          console.warn("Error showing success notification:", error);
          // Continue even if notification failed
        }
      } catch (error) {
        console.error("Error creating flash cards:", error);
        
        // Show error notification - WITH ERROR HANDLING
        try {
          chrome.tabs.sendMessage(tab.id, {
            action: "showNotification",
            message: "Error: " + error.message,
            type: "error"
          }, () => {
            // Ignore response errors
            if (chrome.runtime.lastError) {
              console.warn("Could not send error notification:", chrome.runtime.lastError.message);
            }
          });
        } catch (notifyError) {
          console.warn("Error showing error notification:", notifyError);
        }
        
        // Store the input and error to show in popup
        await dbService.saveSetting("geminiInput", info.selectionText);
        await dbService.saveSetting("timestamp", new Date().toISOString());
        await dbService.saveSetting("pendingMessage", "Error creating flash cards: " + error.message);
        chrome.action.openPopup();
      }
    }).catch(error => {
      console.error("Database error:", error);
    });
  }
});

// Function to generate flash cards with Gemini API
async function generateFlashCards(text, apiKey) {
  // Default prompt for flash card generation
  const prompt = `Create 3 flash cards from the following text. Each flash card should have:
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

  // Prepare the full prompt text
  const fullPrompt = `${prompt}\n\nText: ${text}`;

  // Call Gemini API
  const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      contents: [
        {
          parts: [{ text: fullPrompt }]
        }
      ]
    })
  });
  
  // Handle errors
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Gemini API Error (${response.status}): ${errorText}`);
  }
  
  // Parse response
  const data = await response.json();
  
  // Store complete response for debugging
  await dbService.saveSetting("lastGeminiResponse", data);
  await dbService.saveSetting("responseTimestamp", new Date().toISOString());
  
  // Extract content
  if (!data.candidates || !data.candidates[0] || !data.candidates[0].content || 
      !data.candidates[0].content.parts || !data.candidates[0].content.parts[0]) {
    throw new Error("Unexpected response format from Gemini");
  }
  
  const content = data.candidates[0].content.parts[0].text;
  
  // Parse the flash cards from the content
  return parseFlashCards(content, text);
}

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
    throw new Error("Failed to parse flash cards: " + error.message);
  }
}
