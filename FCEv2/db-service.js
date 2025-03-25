// db-service.js
// IndexedDB service for storing and retrieving flash cards

const DB_NAME = 'FlashCardDB';
const DB_VERSION = 1;
const CARDS_STORE = 'flashCards';
const SETTINGS_STORE = 'settings';

// Initialize the database
function initDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    
    request.onerror = (event) => {
      console.error('IndexedDB error:', event.target.error);
      reject('Could not open IndexedDB');
    };
    
    request.onsuccess = (event) => {
      console.log('IndexedDB initialized successfully');
      resolve(event.target.result);
    };
    
    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      console.log('Creating object stores');
      
      // Create flash cards store with 'id' as key path
      if (!db.objectStoreNames.contains(CARDS_STORE)) {
        const cardsStore = db.createObjectStore(CARDS_STORE, { keyPath: 'id' });
        // Create indexes for searching
        cardsStore.createIndex('created', 'created', { unique: false });
        cardsStore.createIndex('tags', 'tags', { unique: false, multiEntry: true });
      }
      
      // Create settings store with 'key' as key path
      if (!db.objectStoreNames.contains(SETTINGS_STORE)) {
        db.createObjectStore(SETTINGS_STORE, { keyPath: 'key' });
      }
    };
  });
}

// Get a reference to the database
function getDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    
    request.onerror = (event) => {
      console.error('IndexedDB error:', event.target.error);
      reject('Could not open IndexedDB');
    };
    
    request.onsuccess = (event) => {
      resolve(event.target.result);
    };
  });
}

// Save flash cards to IndexedDB
async function saveFlashCards(newCards) {
  try {
    const db = await getDB();
    const transaction = db.transaction([CARDS_STORE], 'readwrite');
    const store = transaction.objectStore(CARDS_STORE);
    
    // Add each card to the store
    for (const card of newCards) {
      store.add(card);
    }
    
    return new Promise((resolve, reject) => {
      transaction.oncomplete = () => {
        console.log(`Added ${newCards.length} cards to IndexedDB`);
        // Update card count in badge
        getAllFlashCards().then(allCards => {
          chrome.action.setBadgeText({ text: allCards.length.toString() });
          chrome.action.setBadgeBackgroundColor({ color: "#4285f4" });
          resolve(newCards.length);
        });
      };
      
      transaction.onerror = (event) => {
        console.error('Transaction error:', event.target.error);
        reject('Error saving cards to IndexedDB');
      };
    });
  } catch (error) {
    console.error('Database error:', error);
    throw new Error('Failed to save flash cards to IndexedDB');
  }
}

// Get all flash cards from IndexedDB
async function getAllFlashCards() {
  try {
    const db = await getDB();
    const transaction = db.transaction([CARDS_STORE], 'readonly');
    const store = transaction.objectStore(CARDS_STORE);
    const request = store.getAll();
    
    return new Promise((resolve, reject) => {
      request.onsuccess = (event) => {
        resolve(event.target.result);
      };
      
      request.onerror = (event) => {
        console.error('Request error:', event.target.error);
        reject('Error retrieving cards from IndexedDB');
      };
    });
  } catch (error) {
    console.error('Database error:', error);
    throw new Error('Failed to retrieve flash cards from IndexedDB');
  }
}

// Delete a flash card by ID
async function deleteFlashCard(cardId) {
  try {
    const db = await getDB();
    const transaction = db.transaction([CARDS_STORE], 'readwrite');
    const store = transaction.objectStore(CARDS_STORE);
    const request = store.delete(cardId);
    
    return new Promise((resolve, reject) => {
      transaction.oncomplete = () => {
        console.log(`Deleted card ${cardId} from IndexedDB`);
        // Update card count in badge
        getAllFlashCards().then(allCards => {
          chrome.action.setBadgeText({ text: allCards.length.toString() });
          chrome.action.setBadgeBackgroundColor({ color: "#4285f4" });
          resolve(true);
        });
      };
      
      transaction.onerror = (event) => {
        console.error('Transaction error:', event.target.error);
        reject('Error deleting card from IndexedDB');
      };
    });
  } catch (error) {
    console.error('Database error:', error);
    throw new Error('Failed to delete flash card from IndexedDB');
  }
}

// Update flash card in IndexedDB
async function updateFlashCard(card) {
  try {
    const db = await getDB();
    const transaction = db.transaction([CARDS_STORE], 'readwrite');
    const store = transaction.objectStore(CARDS_STORE);
    const request = store.put(card);
    
    return new Promise((resolve, reject) => {
      transaction.oncomplete = () => {
        console.log(`Updated card ${card.id} in IndexedDB`);
        resolve(true);
      };
      
      transaction.onerror = (event) => {
        console.error('Transaction error:', event.target.error);
        reject('Error updating card in IndexedDB');
      };
    });
  } catch (error) {
    console.error('Database error:', error);
    throw new Error('Failed to update flash card in IndexedDB');
  }
}

// Save a setting to IndexedDB
async function saveSetting(key, value) {
  try {
    const db = await getDB();
    const transaction = db.transaction([SETTINGS_STORE], 'readwrite');
    const store = transaction.objectStore(SETTINGS_STORE);
    const request = store.put({ key, value });
    
    return new Promise((resolve, reject) => {
      transaction.oncomplete = () => {
        console.log(`Saved setting ${key} to IndexedDB`);
        resolve(true);
      };
      
      transaction.onerror = (event) => {
        console.error('Transaction error:', event.target.error);
        reject('Error saving setting to IndexedDB');
      };
    });
  } catch (error) {
    console.error('Database error:', error);
    throw new Error('Failed to save setting to IndexedDB');
  }
}

// Get a setting from IndexedDB
async function getSetting(key) {
  try {
    const db = await getDB();
    const transaction = db.transaction([SETTINGS_STORE], 'readonly');
    const store = transaction.objectStore(SETTINGS_STORE);
    const request = store.get(key);
    
    return new Promise((resolve, reject) => {
      request.onsuccess = (event) => {
        const result = event.target.result;
        resolve(result ? result.value : null);
      };
      
      request.onerror = (event) => {
        console.error('Request error:', event.target.error);
        reject('Error retrieving setting from IndexedDB');
      };
    });
  } catch (error) {
    console.error('Database error:', error);
    throw new Error('Failed to retrieve setting from IndexedDB');
  }
}

// Get multiple settings from IndexedDB
async function getMultipleSettings(keys) {
  try {
    const db = await getDB();
    const transaction = db.transaction([SETTINGS_STORE], 'readonly');
    const store = transaction.objectStore(SETTINGS_STORE);
    
    const promises = keys.map(key => {
      return new Promise((resolve, reject) => {
        const request = store.get(key);
        request.onsuccess = (event) => {
          const result = event.target.result;
          resolve({ [key]: result ? result.value : null });
        };
        request.onerror = (event) => {
          console.error('Request error:', event.target.error);
          reject('Error retrieving setting from IndexedDB');
        };
      });
    });
    
    const results = await Promise.all(promises);
    return results.reduce((acc, val) => ({ ...acc, ...val }), {});
  } catch (error) {
    console.error('Database error:', error);
    throw new Error('Failed to retrieve settings from IndexedDB');
  }
}

// Create the service object
const dbService = {
  initDB,
  saveFlashCards,
  getAllFlashCards,
  deleteFlashCard,
  updateFlashCard,
  saveSetting,
  getSetting,
  getMultipleSettings
};

// Make it globally available
this.dbService = dbService;
