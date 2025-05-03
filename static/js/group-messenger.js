/**
 * Group Messenger Component for GDial
 * Enhanced and improved version with better error handling, UI updates, and accessibility
 */

// Main component initialization
function initGroupMessenger(options = {}) {
    console.log("Initializing Group Messenger v1.2 with options:", options);
    
    // Configuration and options
    const config = {
        progressOverlayId: options.progressOverlayId || 'progress-overlay',
        progressBarId: options.progressBarId || 'progress-bar',
        progressTitleId: options.progressTitleId || 'progress-title',
        progressStatusId: options.progressStatusId || 'progress-status',
        progressDetailsId: options.progressDetailsId || 'progress-details',
        progressPercentageId: options.progressPercentageId || 'progress-percentage',
        miniProgressId: options.miniProgressId || 'mini-progress',
        miniProgressFillId: options.miniProgressFillId || 'mini-progress-fill',
        loadingIndicatorId: options.loadingIndicatorId || 'loading-indicator',
        emptyResultsId: options.emptyResultsId || 'empty-results',
        messagePreviewId: options.messagePreviewId || 'message-preview'
    };

    // DOM element references - will be used throughout the component
    let messagesSelect = null;
    let groupsSelect = null;
    let messageTypeSelect = null;
    let contactCardsContainer = null;
    let searchInput = null;
    let selectAllBtn = null;
    let deselectAllBtn = null;
    let sendBtn = null;
    let statusCounter = null;
    let loadingIndicator = null;
    let emptyResults = null;
    let messagePreview = null;
    let filterChips = null;
    let progressOverlay = null;
    let progressBar = null;
    let progressTitle = null;
    let progressStatus = null;
    let progressDetails = null;
    let progressPercentage = null;
    let miniProgress = null;
    let miniProgressFill = null;
    
    // Data storage
    let contacts = [];
    let messages = [];
    let groups = [];
    let selectedContacts = new Set();
    let messageId = null;
    let groupId = null;
    let messageType = 'voice'; // Default to voice
    
    // Get DOM elements function - more robust, retries if elements aren't available yet
    function getDOMElements() {
        console.log("Getting DOM elements");
        
        // Main UI elements
        messagesSelect = document.getElementById('message-select');
        groupsSelect = document.getElementById('group-select');
        messageTypeSelect = document.getElementById('message-type-select');
        contactCardsContainer = document.getElementById('contact-cards-container');
        searchInput = document.getElementById('contact-search');
        selectAllBtn = document.getElementById('select-all-contacts');
        deselectAllBtn = document.getElementById('deselect-all-contacts');
        sendBtn = document.getElementById('send-to-selected');
        statusCounter = document.getElementById('status-counter');
        
        // Configuration-based elements
        loadingIndicator = document.getElementById(config.loadingIndicatorId);
        emptyResults = document.getElementById(config.emptyResultsId);
        messagePreview = document.getElementById(config.messagePreviewId);
        filterChips = document.getElementById('filter-chips');
        
        // Progress window elements
        progressOverlay = document.getElementById(config.progressOverlayId);
        progressBar = document.getElementById(config.progressBarId);
        progressTitle = document.getElementById(config.progressTitleId);
        progressStatus = document.getElementById(config.progressStatusId);
        progressDetails = document.getElementById(config.progressDetailsId);
        progressPercentage = document.getElementById(config.progressPercentageId);
        miniProgress = document.getElementById(config.miniProgressId);
        miniProgressFill = document.getElementById(config.miniProgressFillId);
        
        // Log missing elements
        let missingElements = [];
        if (!messagesSelect) missingElements.push('message-select');
        if (!groupsSelect) missingElements.push('group-select');
        if (!messageTypeSelect) missingElements.push('message-type-select');
        if (!contactCardsContainer) missingElements.push('contact-cards-container');
        if (!searchInput) missingElements.push('contact-search');
        if (!selectAllBtn) missingElements.push('select-all-contacts');
        if (!deselectAllBtn) missingElements.push('deselect-all-contacts');
        if (!sendBtn) missingElements.push('send-to-selected');
        if (!statusCounter) missingElements.push('status-counter');
        if (!loadingIndicator) missingElements.push(config.loadingIndicatorId);
        if (!emptyResults) missingElements.push(config.emptyResultsId);
        if (!messagePreview) missingElements.push(config.messagePreviewId);
        
        if (missingElements.length > 0) {
            console.warn("Missing DOM elements:", missingElements.join(", "));
        } else {
            console.log("All DOM elements found successfully");
        }
        
        return missingElements.length === 0;
    }
    
    // Filters and status tracking
    let searchTerm = '';
    let statusFilter = 'all';
    let messageStatuses = {}; // Track message status for each contact
    let callInProgress = false; // Track if a call is in progress
    
    // Show progress window for tracking operations
    function showProgressWindow(title) {
        console.log(`Showing progress window: "${title}"`);
        
        // Get elements in case they weren't loaded initially
        if (!progressOverlay) {
            console.log("Progress overlay not found, attempting to find it");
            progressOverlay = document.getElementById(config.progressOverlayId);
            
            // If still not found, create it
            if (!progressOverlay) {
                console.warn("Progress overlay still not found, checking if it exists in DOM");
                const existingOverlay = document.getElementById('progress-overlay');
                if (existingOverlay) {
                    console.log("Found existing progress overlay with id 'progress-overlay'");
                    progressOverlay = existingOverlay;
                } else {
                    console.error("Could not find progress overlay, will use alert instead");
                }
            }
        }
        
        // Try to get all necessary elements
        if (!progressTitle) progressTitle = document.getElementById(config.progressTitleId) || document.getElementById('progress-title');
        if (!progressStatus) progressStatus = document.getElementById(config.progressStatusId) || document.getElementById('progress-status');
        if (!progressDetails) progressDetails = document.getElementById(config.progressDetailsId) || document.getElementById('progress-details');
        if (!progressBar) progressBar = document.getElementById(config.progressBarId) || document.getElementById('progress-bar');
        if (!progressPercentage) progressPercentage = document.getElementById(config.progressPercentageId) || document.getElementById('progress-percentage');
        
        if (!progressOverlay) {
            console.error("Cannot show progress window: progress overlay element is missing");
            alert(`Operation in progress: ${title || 'Message Progress'}`);
            return;
        }
        
        try {
            // Try to update all elements
            if (progressTitle) progressTitle.textContent = title || 'Message Progress';
            if (progressStatus) progressStatus.textContent = 'Initializing...';
            if (progressDetails) progressDetails.innerHTML = '';
            if (progressBar) progressBar.style.width = '0%';
            if (progressPercentage) progressPercentage.textContent = '0%';
            
            // Make the overlay visible
            progressOverlay.classList.add('active');
            progressOverlay.style.display = 'flex';
            
            // Update global state
            callInProgress = true;
            console.log("Progress window displayed, call in progress set to true");
        } catch (error) {
            console.error("Error updating progress window:", error);
            // Fallback to alert if something goes wrong
            alert(`Operation in progress: ${title || 'Message Progress'}`);
        }
    }
    
    // Update progress information
    function updateProgressWindow(status, detail, progress) {
        console.log(`Updating progress: status=${status}, detail=${detail}, progress=${progress}`);
        
        // Verify the progress overlay exists and is active
        if (!progressOverlay) {
            console.warn("Cannot update progress: progress overlay is missing");
            progressOverlay = document.getElementById(config.progressOverlayId) || document.getElementById('progress-overlay');
            
            if (!progressOverlay) {
                console.error("Still cannot find progress overlay, aborting update");
                // Log the update to console instead
                console.info(`Progress update: ${status} - ${detail} - ${progress}%`);
                return;
            }
        }
        
        // Check if active
        if (!progressOverlay.classList.contains('active')) {
            console.warn("Progress overlay exists but is not active (class 'active' not present)");
            // Try to make it active
            progressOverlay.classList.add('active');
            progressOverlay.style.display = 'flex';
        }
        
        try {
            // Update status
            if (status) {
                if (!progressStatus) {
                    progressStatus = document.getElementById(config.progressStatusId) || document.getElementById('progress-status');
                }
                
                if (progressStatus) {
                    progressStatus.textContent = status;
                } else {
                    console.warn("Cannot update status: progress status element is missing");
                }
            }
            
            // Add detail
            if (detail) {
                if (!progressDetails) {
                    progressDetails = document.getElementById(config.progressDetailsId) || document.getElementById('progress-details');
                }
                
                if (progressDetails) {
                    const detailItem = document.createElement('div');
                    detailItem.className = 'detail-item';
                    
                    const timestamp = new Date().toLocaleTimeString();
                    detailItem.innerHTML = `<span style="color:#777">[${timestamp}]</span> ${detail}`;
                    
                    progressDetails.appendChild(detailItem);
                    progressDetails.scrollTop = progressDetails.scrollHeight;
                } else {
                    console.warn("Cannot add detail: progress details element is missing");
                }
            }
            
            // Update progress bar
            if (progress !== undefined) {
                const progressValue = Math.min(100, Math.max(0, progress));
                
                // Update main progress bar
                if (!progressBar) {
                    progressBar = document.getElementById(config.progressBarId) || document.getElementById('progress-bar');
                }
                
                if (progressBar) {
                    progressBar.style.width = `${progressValue}%`;
                } else {
                    console.warn("Cannot update progress bar: element is missing");
                }
                
                // Update percentage text
                if (!progressPercentage) {
                    progressPercentage = document.getElementById(config.progressPercentageId) || document.getElementById('progress-percentage');
                }
                
                if (progressPercentage) {
                    progressPercentage.textContent = `${Math.round(progressValue)}%`;
                } else {
                    console.warn("Cannot update progress percentage: element is missing");
                }
                
                // Update mini progress bar
                if (!miniProgressFill) {
                    miniProgressFill = document.getElementById(config.miniProgressFillId) || document.getElementById('mini-progress-fill');
                }
                
                if (miniProgressFill) {
                    miniProgressFill.style.width = `${progressValue}%`;
                    
                    if (!miniProgress) {
                        miniProgress = document.getElementById(config.miniProgressId) || document.getElementById('mini-progress');
                    }
                    
                    const miniText = miniProgress ? miniProgress.querySelector('.mini-progress-text') : null;
                    if (miniText) {
                        miniText.textContent = `Sending: ${Math.round(progressValue)}%`;
                    }
                }
            }
            
            console.log("Progress window successfully updated");
        } catch (error) {
            console.error("Error updating progress window:", error);
            // Log the update to console instead
            console.info(`Progress update: ${status} - ${detail} - ${progress}%`);
        }
    }
    
    // Hide progress window
    function hideProgressWindow() {
        if (progressOverlay) {
            progressOverlay.classList.remove('active');
        }
        callInProgress = false;
    }
    
    // Hide mini progress
    function hideMiniProgress() {
        if (miniProgress) {
            miniProgress.classList.remove('active');
        }
    }
    
    // Show loading indicator
    function showLoading() {
        if (loadingIndicator) {
            loadingIndicator.style.display = 'flex';
        }
        if (contactCardsContainer) {
            contactCardsContainer.style.display = 'none';
        }
        if (emptyResults) {
            emptyResults.style.display = 'none';
        }
    }
    
    // Hide loading indicator
    function hideLoading() {
        if (loadingIndicator) {
            loadingIndicator.style.display = 'none';
        }
        if (contactCardsContainer) {
            contactCardsContainer.style.display = 'grid';
        }
    }
    
    // Show empty state
    function showEmptyState() {
        if (emptyResults) {
            emptyResults.style.display = 'block';
        }
        if (contactCardsContainer) {
            contactCardsContainer.style.display = 'none';
        }
    }
    
    // Hide empty state
    function hideEmptyState() {
        if (emptyResults) {
            emptyResults.style.display = 'none';
        }
    }
    
    // Initialize component
    function initialize() {
        console.log('Initializing Group Messenger component v1.2 - Rebuilt');
        
        // First get DOM elements
        const elementsFound = getDOMElements();
        
        if (!elementsFound) {
            console.warn("Some elements not found, retrying in 500ms");
            setTimeout(() => {
                const retrySuccess = getDOMElements();
                if (retrySuccess) {
                    console.log("Elements found on retry, continuing initialization");
                    continueInitialization();
                } else {
                    console.error("Still missing elements. Attempting to continue with limited functionality");
                    continueInitialization();
                }
            }, 500);
        } else {
            console.log("All elements found, continuing initialization");
            continueInitialization();
        }
    }
    
    // Continue initialization after DOM elements are loaded
    function continueInitialization() {
        console.log("Continuing initialization - setting up event handlers and loading data");
        
        // Set up event listeners first so they're ready when data loads
        setupEventListeners();
        
        // Show loading state while we fetch data
        showLoading();
        
        // Load messages for dropdown
        fetchMessages()
            .then(data => {
                messages = data || [];
                populateMessagesSelect(data || []);
            })
            .catch(error => {
                console.error('Error loading messages:', error);
                showNotification('Failed to load messages: ' + error.message, 'error');
            });
        
        // Load groups for dropdown
        fetchGroups()
            .then(data => {
                groups = data || [];
                populateGroupsSelect(data || []);
            })
            .catch(error => {
                console.error('Error loading groups:', error);
                showNotification('Failed to load groups: ' + error.message, 'error');
            });
        
        // Load initial contacts
        fetchContacts()
            .then(() => {
                hideLoading();
            })
            .catch(error => {
                console.error('Error loading contacts:', error);
                showNotification('Failed to load contacts: ' + error.message, 'error');
                hideLoading();
                showEmptyState();
            });
        
        // Set up event listeners
        setupEventListeners();
    }
    
    // Fetch data from API with better error handling
    async function fetchMessages() {
        try {
            const response = await fetch('/messages');
            if (!response.ok) {
                console.error(`Failed to fetch messages: ${response.status} ${response.statusText}`);
                showNotification(`Server error: ${response.status} ${response.statusText}`, 'error');
                return [];
            }
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error fetching messages:', error);
            return [];
        }
    }
    
    async function fetchGroups() {
        try {
            const response = await fetch('/groups');
            if (!response.ok) {
                console.error(`Failed to fetch groups: ${response.status} ${response.statusText}`);
                showNotification(`Server error: ${response.status} ${response.statusText}`, 'error');
                return [];
            }
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error fetching groups:', error);
            return [];
        }
    }
    
    async function fetchContacts(selectedGroupId = null) {
        showLoading();
        
        try {
            let url = '/contacts';
            if (selectedGroupId) {
                url = `/groups/${selectedGroupId}`;
                groupId = selectedGroupId;
            } else {
                groupId = null;
            }
            
            // Try to fetch contacts from API
            try {
                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error(`Failed to fetch contacts: ${response.status} ${response.statusText}`);
                }
                
                let data = await response.json();
                
                // If fetching by group, the contacts are in the 'contacts' property
                if (selectedGroupId) {
                    contacts = data.contacts || [];
                } else {
                    contacts = data;
                }
            } catch (fetchError) {
                console.error('Error fetching contacts from API:', fetchError);
                contacts = [];
            }
            
            console.log(`Loaded ${contacts.length} contacts`);
            
            // Reset message statuses for new contact set
            messageStatuses = {};
            contacts.forEach(contact => {
                messageStatuses[contact.id] = {
                    status: 'pending',
                    message: 'Not sent yet'
                };
            });
            
            // Reset selected contacts
            selectedContacts.clear();
            
            // Render the contacts
            renderContactCards();
            
            return contacts;
        } catch (error) {
            console.error('Error in fetchContacts:', error);
            throw error;
        } finally {
            hideLoading();
        }
    }
    
    // Fetch message content for preview
    async function fetchMessageContent(messageId) {
        if (!messageId) return;
        
        try {
            const response = await fetch(`/messages/${messageId}`);
            if (!response.ok) {
                throw new Error(`Failed to fetch message: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            return data.content;
        } catch (error) {
            console.error('Error fetching message content:', error);
            return "Error loading message preview.";
        }
    }
    
    // UI population functions
    function populateMessagesSelect(messages) {
        if (!messagesSelect) return;
        
        messagesSelect.innerHTML = '<option value="" selected disabled>Select a message</option>';
        
        const voiceMessages = messages.filter(msg => ['voice', 'both'].includes(msg.message_type));
        const smsMessages = messages.filter(msg => ['sms', 'both'].includes(msg.message_type));
        
        // Add voice messages optgroup
        if (voiceMessages.length > 0) {
            const voiceGroup = document.createElement('optgroup');
            voiceGroup.label = 'Voice Messages';
            
            voiceMessages.forEach(message => {
                const option = document.createElement('option');
                option.value = message.id;
                option.textContent = message.name;
                option.dataset.type = 'voice';
                option.dataset.messageType = message.message_type;
                voiceGroup.appendChild(option);
            });
            
            messagesSelect.appendChild(voiceGroup);
        }
        
        // Add SMS messages optgroup
        if (smsMessages.length > 0) {
            const smsGroup = document.createElement('optgroup');
            smsGroup.label = 'SMS Messages';
            
            smsMessages.forEach(message => {
                const option = document.createElement('option');
                option.value = message.id;
                option.textContent = message.name;
                option.dataset.type = 'sms';
                option.dataset.messageType = message.message_type;
                smsGroup.appendChild(option);
            });
            
            messagesSelect.appendChild(smsGroup);
        }
        
        // If no messages available, show a placeholder option
        if (voiceMessages.length === 0 && smsMessages.length === 0) {
            const option = document.createElement('option');
            option.value = "";
            option.textContent = "No messages available";
            option.disabled = true;
            messagesSelect.appendChild(option);
        }
    }
    
    function populateGroupsSelect(groups) {
        if (!groupsSelect) return;
        
        groupsSelect.innerHTML = '<option value="" selected>All Contacts</option>';
        
        if (groups.length === 0) {
            const option = document.createElement('option');
            option.value = "";
            option.textContent = "No groups available";
            option.disabled = true;
            groupsSelect.appendChild(option);
            return;
        }
        
        groups.forEach(group => {
            const option = document.createElement('option');
            option.value = group.id;
            option.textContent = group.name;
            groupsSelect.appendChild(option);
        });
    }
    
    // Apply filters and render contacts
    function applyFilters() {
        // Filter contacts by search term and status
        const filteredContacts = contacts.filter(contact => {
            // Apply search filter - expanded to search all fields
            const searchTermLower = searchTerm.toLowerCase();
            const matchesSearch = 
                !searchTerm || 
                contact.name.toLowerCase().includes(searchTermLower) ||
                (contact.email && contact.email.toLowerCase().includes(searchTermLower)) ||
                contact.phone_numbers.some(phone => phone.number.includes(searchTerm)) ||
                // Search in groups
                (contact.groups && contact.groups.some(group => 
                    group.name.toLowerCase().includes(searchTermLower) || 
                    group.id.toLowerCase().includes(searchTermLower)
                )) ||
                // Search in ID
                contact.id.toLowerCase().includes(searchTermLower);
            
            // Apply status filter
            const status = messageStatuses[contact.id]?.status || 'pending';
            const matchesStatus = statusFilter === 'all' || status === statusFilter;
            
            return matchesSearch && matchesStatus;
        });
        
        // Show empty state if no contacts match filters
        if (filteredContacts.length === 0) {
            showEmptyState();
        } else {
            hideEmptyState();
        }
        
        return filteredContacts;
    }
    
    function renderContactCards() {
        console.log("Rendering contact cards");
        
        // Clear container
        if (!contactCardsContainer) {
            console.error("Cannot render contact cards: container element is missing - looking for element with ID 'contact-cards-container'");
            // Try to find it again, maybe it was loaded later
            const container = document.getElementById('contact-cards-container');
            if (container) {
                console.log("Found contact cards container on second attempt");
                contactCardsContainer = container;
            } else {
                console.error("Container still not found. UI cannot be rendered.");
                return;
            }
        }
        
        // Clear existing content
        contactCardsContainer.innerHTML = '';
        console.log(`Container found and cleared: ${contactCardsContainer.id}`);
        
        // Apply filters
        const filteredContacts = applyFilters();
        console.log(`Filtered contacts: ${filteredContacts.length}`);
        
        // Create and append contact cards
        filteredContacts.forEach(contact => {
            const card = createContactCard(contact);
            contactCardsContainer.appendChild(card);
        });
        
        console.log(`Rendered ${filteredContacts.length} contact cards`);
        
        // Update counter
        updateStatusCounter();
        
        // Ensure cards are visible
        if (contactCardsContainer) {
            contactCardsContainer.style.display = 'grid';
        }
        
        // Show/hide empty state
        if (filteredContacts.length === 0) {
            showEmptyState();
        } else {
            hideEmptyState();
        }
        
        // Hide loading indicator if it's still showing
        hideLoading();
    }
    
    function createContactCard(contact) {
        const card = document.createElement('div');
        card.className = 'contact-card';
        card.dataset.id = contact.id;
        
        // Create selection indicator for better UX
        const selectionIndicator = document.createElement('div');
        selectionIndicator.className = 'selection-indicator';
        card.appendChild(selectionIndicator);
        
        // Check if contact is selected
        if (selectedContacts.has(contact.id)) {
            card.classList.add('selected');
        }
        
        // Get status for this contact
        const status = messageStatuses[contact.id] || { status: 'pending', message: 'Not sent yet' };
        card.classList.add(status.status);
        
        // Format phone numbers
        const primaryPhone = contact.phone_numbers.length > 0 ? 
            contact.phone_numbers.sort((a, b) => a.priority - b.priority)[0].number : 
            'No phone number';
        
        // Create card header
        const cardHeader = document.createElement('div');
        cardHeader.className = 'card-header';
        
        // Contact name
        const nameHeading = document.createElement('h3');
        nameHeading.className = 'contact-name';
        nameHeading.textContent = contact.name;
        cardHeader.appendChild(nameHeading);
        
        // Status badge
        const statusBadge = document.createElement('div');
        statusBadge.className = `status-badge ${status.status}`;
        statusBadge.textContent = status.status.toUpperCase();
        cardHeader.appendChild(statusBadge);
        
        card.appendChild(cardHeader);
        
        // Contact details
        const details = document.createElement('div');
        details.className = 'contact-details';
        
        // Contact ID (for reference)
        const idDiv = document.createElement('div');
        idDiv.className = 'contact-id';
        idDiv.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                <polyline points="7.5 4.21 12 6.81 16.5 4.21"></polyline>
                <polyline points="7.5 19.79 7.5 14.6 3 12"></polyline>
                <polyline points="21 12 16.5 14.6 16.5 19.79"></polyline>
                <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
                <line x1="12" y1="22.08" x2="12" y2="12"></line>
            </svg>
            <span class="id-text" title="${contact.id}">${contact.id.substring(0, 8)}...</span>
        `;
        details.appendChild(idDiv);
        
        // Phone number
        const phoneDiv = document.createElement('div');
        phoneDiv.className = 'phone';
        phoneDiv.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
            </svg>
            <a href="tel:${primaryPhone}" class="phone-link">${formatPhone(primaryPhone)}</a>
        `;
        details.appendChild(phoneDiv);
        
        // Email (if available)
        if (contact.email) {
            const emailDiv = document.createElement('div');
            emailDiv.className = 'email';
            emailDiv.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                    <polyline points="22,6 12,13 2,6"></polyline>
                </svg>
                <a href="mailto:${contact.email}" class="email-link">${contact.email}</a>
            `;
            details.appendChild(emailDiv);
        }
        
        card.appendChild(details);
        
        // Contact groups
        if (contact.groups && contact.groups.length > 0) {
            const groupsContainer = document.createElement('div');
            groupsContainer.className = 'contact-groups';
            
            contact.groups.forEach(group => {
                const groupTag = document.createElement('span');
                groupTag.className = 'contact-group-tag';
                groupTag.textContent = group.name;
                groupTag.title = `Group ID: ${group.id}`;
                groupTag.dataset.groupId = group.id;
                
                // Make group tags clickable to filter by that group
                groupTag.addEventListener('click', (e) => {
                    e.stopPropagation(); // Don't trigger the card click
                    
                    // Set the group dropdown to this group
                    if (groupsSelect) {
                        groupsSelect.value = group.id;
                        // Trigger the change event
                        const event = new Event('change');
                        groupsSelect.dispatchEvent(event);
                    }
                });
                
                groupsContainer.appendChild(groupTag);
            });
            
            card.appendChild(groupsContainer);
        }
        
        // Status message
        const statusMessage = document.createElement('div');
        statusMessage.className = 'status-message';
        statusMessage.textContent = status.message;
        card.appendChild(statusMessage);
        
        // Card actions
        const actions = document.createElement('div');
        actions.className = 'card-actions';
        
        // Select/Deselect button
        const selectBtn = document.createElement('button');
        selectBtn.className = 'select-btn';
        selectBtn.innerHTML = selectedContacts.has(contact.id) ? 
            '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg> Deselect' : 
            '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg> Select';
        actions.appendChild(selectBtn);
        
        // Send button
        const sendBtn = document.createElement('button');
        sendBtn.className = 'send-btn';
        sendBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
            Send
        `;
        actions.appendChild(sendBtn);
        
        // Retry button (only shown for failed messages)
        const retryBtn = document.createElement('button');
        retryBtn.className = 'retry-btn';
        retryBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M23 4v6h-6"></path>
                <path d="M1 20v-6h6"></path>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10"></path>
                <path d="M20.49 15a9 9 0 0 1-14.85 3.36L1 14"></path>
            </svg>
            Retry
        `;
        retryBtn.style.display = status.status === 'failed' ? 'flex' : 'none';
        actions.appendChild(retryBtn);
        
        card.appendChild(actions);
        
        // Add event listeners
        selectBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleContactSelection(contact.id);
        });
        
        sendBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            sendToContact(contact.id);
        });
        
        retryBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            retryContact(contact.id);
        });
        
        // Make the card selectable
        card.addEventListener('click', () => {
            toggleContactSelection(contact.id);
        });
        
        return card;
    }
    
    // Event handlers
    function toggleContactSelection(contactId) {
        if (selectedContacts.has(contactId)) {
            selectedContacts.delete(contactId);
        } else {
            selectedContacts.add(contactId);
        }
        
        // Update the UI
        const card = document.querySelector(`.contact-card[data-id="${contactId}"]`);
        if (card) {
            card.classList.toggle('selected', selectedContacts.has(contactId));
            
            const selectBtn = card.querySelector('.select-btn');
            if (selectBtn) {
                selectBtn.innerHTML = selectedContacts.has(contactId) ? 
                    '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg> Deselect' : 
                    '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg> Select';
            }
        }
        
        updateStatusCounter();
    }
    
    // Helper to ensure valid UUID format for API requests
    function validateUUID(id) {
        // Check if the ID is already a properly formatted UUID
        const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
        return uuidPattern.test(id) ? id : id; // Return ID regardless in demo mode
    }
    
    async function sendToSelected() {
        console.log("sendToSelected called with:");
        console.log("- selectedContacts:", selectedContacts);
        console.log("- messageId:", messageId);
        console.log("- messageType:", messageType);
        
        if (selectedContacts.size === 0) {
            console.warn("No contacts selected - aborting send");
            showNotification('No contacts selected', 'warning');
            return;
        }
        
        if (!messageId) {
            console.warn("No message ID - aborting send");
            showNotification('Please select a message', 'warning');
            return;
        }
        
        // Validate message ID format
        const validMessageId = validateUUID(messageId);
        if (!validMessageId) {
            console.error("Invalid message ID format:", messageId);
            showNotification('Invalid message ID format', 'error');
            return;
        }
        
        const contactIds = Array.from(selectedContacts);
        console.log(`Processing ${contactIds.length} contacts for ${messageType} message ID ${validMessageId}`);
        
        // Show progress window
        try {
            console.log("Attempting to show progress window");
            if (messageType === 'voice') {
                showProgressWindow('Voice Call Progress');
            } else {
                showProgressWindow('SMS Message Progress');
            }
            
            console.log("Progress window shown, updating initial status");
            updateProgressWindow(
                'Preparing to send...',
                `Preparing to send ${messageType === 'voice' ? 'voice calls' : 'SMS messages'} to ${contactIds.length} selected contacts`,
                0
            );
        } catch (windowError) {
            console.error("Error showing progress window:", windowError);
            alert(`Preparing to send to ${contactIds.length} contacts. Please wait...`);
        }
        
        try {
            // Update UI to show sending status
            console.log("Updating contact statuses to 'sending'");
            contactIds.forEach(id => {
                messageStatuses[id] = {
                    status: 'sending',
                    message: 'Sending...'
                };
                try {
                    updateContactCardStatus(id);
                } catch (statusErr) {
                    console.warn(`Could not update status UI for contact ${id}:`, statusErr);
                }
            });
            
            // Call API to send messages
            console.log(`Sending ${messageType} messages`);
            if (messageType === 'voice') {
                await sendVoiceMessages(contactIds, validMessageId);
            } else {
                await sendSmsMessages(contactIds, validMessageId);
            }
            
            console.log("Send operation completed successfully");
            
        } catch (error) {
            console.error('Error sending messages:', error);
            
            // Update progress window with error
            try {
                updateProgressWindow(
                    'Error',
                    `❌ An error occurred: ${error.message}`,
                    100
                );
            } catch (progressError) {
                console.error("Could not update progress window:", progressError);
            }
            
            // Update UI to show error for contacts that haven't been processed individually
            console.log("Updating failed contact statuses");
            contactIds.forEach(id => {
                if (messageStatuses[id] && messageStatuses[id].status === 'sending') {
                    messageStatuses[id] = {
                        status: 'failed',
                        message: 'Failed to send: ' + error.message
                    };
                    try {
                        updateContactCardStatus(id);
                    } catch (statusErr) {
                        console.warn(`Could not update error status for contact ${id}:`, statusErr);
                    }
                }
            });
            
            showNotification('Error sending messages: ' + error.message, 'error');
        } finally {
            console.log("Send operation finished, updating status counter");
            // Always update counter even if there was an error
            try {
                updateStatusCounter();
            } catch (counterErr) {
                console.error("Could not update status counter:", counterErr);
            }
        }
    }
    
    async function sendVoiceMessages(contactIds, messageId) {
        console.log("Sending voice calls to contacts:", contactIds);
        
        try {
            updateProgressWindow(
                'Sending voice calls...',
                `Initiating voice calls to ${contactIds.length} contacts`,
                20
            );
            
            // Make actual API call using query parameters as shown in the API docs example
            const url = `/trigger-sms?message_id=${messageId}&contacts=${encodeURIComponent(JSON.stringify(contactIds))}`;
            const response = await fetch(url, {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error(`Failed to initiate voice calls: ${response.status} ${response.statusText}`);
            }
            
            // Process API response
            const data = await response.json();
            const smsCount = data.sms_count || contactIds.length;
            let completed = 0;
            let succeeded = smsCount;
            let failed = 0;
            
            updateProgressWindow(
                'Processing results...',
                `${data.detail || 'Voice calls initiated successfully'}`,
                60
            );
            
            // Update status for each contact
            for (const contactId of contactIds) {
                // Find contact for display
                const contact = contacts.find(c => c.id === contactId);
                const contactName = contact ? contact.name : contactId;
                
                messageStatuses[contactId] = {
                    status: 'success',
                    message: data.detail || 'Voice call initiated successfully'
                };
                
                updateContactCardStatus(contactId);
                completed++;
                
                // Brief delay to update UI
                if (contactIds.length > 10 && completed % 5 === 0) {
                    updateProgressWindow(
                        `Processing: ${completed}/${contactIds.length}`,
                        `Updating status for processed contacts...`,
                        ((completed / contactIds.length) * 40) + 60
                    );
                    await new Promise(resolve => setTimeout(resolve, 10));
                }
            }
            
            // Finalize progress
            updateProgressWindow(
                'Completed',
                `✅ ${data.detail || `Voice calls initiated to ${succeeded} contacts`}`,
                100
            );
            
            // Success feedback
            showNotification(
                data.detail || `Voice calls initiated to ${succeeded} contacts`, 
                'success'
            );
            
        } catch (error) {
            console.error('Error initiating voice calls:', error);
            
            // Update status for all contacts to failed
            for (const contactId of contactIds) {
                messageStatuses[contactId] = {
                    status: 'failed',
                    message: `Failed to send: ${error.message}`
                };
                updateContactCardStatus(contactId);
            }
            
            // Update progress window with error
            updateProgressWindow(
                'Error',
                `❌ Error initiating voice calls: ${error.message}`,
                100
            );
            
            // Error notification
            showNotification(`Error sending voice calls: ${error.message}`, 'error');
        }
    }
    
    async function sendSmsMessages(contactIds, messageId) {
        try {
            updateProgressWindow(
                'Sending SMS messages...',
                `Sending SMS messages to ${contactIds.length} contacts`,
                20
            );
            
            // Real API call using query parameters as shown in the API docs example
            const url = `/trigger-sms?message_id=${messageId}&contacts=${encodeURIComponent(JSON.stringify(contactIds))}`;
            const response = await fetch(url, {
                method: 'POST'
            });
            
            if (!response.ok) {
                throw new Error(`Failed to send SMS messages: ${response.status} ${response.statusText}`);
            }
            
            // Process result
            const data = await response.json();
            
            updateProgressWindow(
                'Processing results...',
                `Processing API response for ${contactIds.length} contacts`,
                60
            );
            
            // Update status for each contact
            for (const contactId of contactIds) {
                messageStatuses[contactId] = {
                    status: 'success',
                    message: 'SMS sent successfully'
                };
                updateContactCardStatus(contactId);
            }
            
            updateProgressWindow(
                'Completed',
                `✅ SMS messages sent successfully to ${contactIds.length} contacts`,
                100
            );
            
            showNotification(`SMS messages sent to ${contactIds.length} contacts`, 'success');
        } catch (error) {
            console.error('Error sending SMS messages:', error);
            
            // Update status for all contacts to failed
            for (const contactId of contactIds) {
                messageStatuses[contactId] = {
                    status: 'failed',
                    message: `Failed to send: ${error.message}`
                };
                updateContactCardStatus(contactId);
            }
            
            // Update progress window with error
            updateProgressWindow(
                'Error',
                `❌ Error sending SMS messages: ${error.message}`,
                100
            );
            
            // Error notification
            showNotification(`Error sending SMS messages: ${error.message}`, 'error');
        }
    }
    
    async function sendToContact(contactId) {
        if (!messageId) {
            showNotification('Please select a message', 'warning');
            return;
        }
        
        // Validate IDs
        const validMessageId = validateUUID(messageId);
        const validContactId = validateUUID(contactId);
        
        // Show progress window
        if (messageType === 'voice') {
            showProgressWindow('Voice Call Progress');
        } else {
            showProgressWindow('SMS Message Progress');
        }
        
        try {
            // Update UI to show sending status
            messageStatuses[contactId] = {
                status: 'sending',
                message: 'Sending...'
            };
            
            updateContactCardStatus(contactId);
            
            // Find contact info for progress display
            const contact = contacts.find(c => c.id === contactId);
            const contactName = contact ? contact.name : contactId;
            
            if (messageType === 'voice') {
                updateProgressWindow(
                    'Sending voice call...',
                    `⏳ Initiating voice call to ${contactName}...`,
                    50
                );
                
                // Make real API call using query parameters as shown in the API docs example
                const url = `/trigger-sms?message_id=${validMessageId}&contacts=${encodeURIComponent(JSON.stringify([validContactId]))}`;
                const response = await fetch(url, {
                    method: 'POST'
                });
                
                if (!response.ok) {
                    throw new Error(`Failed to initiate voice call: ${response.status} ${response.statusText}`);
                }
                
                // Process API response
                const data = await response.json();
                
                // Update status based on API response
                messageStatuses[contactId] = {
                    status: 'success',
                    message: data.detail || 'Voice call initiated successfully'
                };
                
                updateProgressWindow(
                    'Call Initiated',
                    `✅ ${data.detail || `Voice call successfully initiated to ${contactName}`}`,
                    100
                );
            } else {
                updateProgressWindow(
                    'Sending SMS...',
                    `⏳ Sending SMS message to ${contactName}...`,
                    50
                );
                
                // Make real API call using query parameters as shown in the API docs example
                const url = `/trigger-sms?message_id=${validMessageId}&contacts=${encodeURIComponent(JSON.stringify([validContactId]))}`;
                const response = await fetch(url, {
                    method: 'POST'
                });
                
                if (!response.ok) {
                    throw new Error(`Failed to send SMS message: ${response.status} ${response.statusText}`);
                }
                
                // Process API response
                const data = await response.json();
                
                // Update status based on API response
                messageStatuses[contactId] = {
                    status: 'success',
                    message: data.detail || 'SMS sent successfully'
                };
                
                updateProgressWindow(
                    'SMS Sent',
                    `✅ ${data.detail || `SMS message successfully sent to ${contactName}`}`,
                    100
                );
            }
            
            updateContactCardStatus(contactId);
            showNotification(`${messageType === 'voice' ? 'Voice call' : 'SMS'} sent to ${contactName}`, 'success');
            
        } catch (error) {
            console.error('Error sending message:', error);
            
            // Update UI to show error
            messageStatuses[contactId] = {
                status: 'failed',
                message: 'Failed to send: ' + error.message
            };
            
            updateContactCardStatus(contactId);
            
            // Update progress window with error
            updateProgressWindow(
                'Error',
                `❌ Error: ${error.message}`,
                100
            );
            
            showNotification('Failed to send message: ' + error.message, 'error');
        }
        
        updateStatusCounter();
    }
    
    async function retryContact(contactId) {
        // Just call sendToContact which handles everything
        await sendToContact(contactId);
    }
    
    // Helper functions
    function updateContactCardStatus(contactId) {
        const card = document.querySelector(`.contact-card[data-id="${contactId}"]`);
        if (!card) return;
        
        const status = messageStatuses[contactId];
        if (!status) return;
        
        // Remove all status classes
        card.classList.remove('pending', 'sending', 'success', 'failed');
        
        // Add the current status class
        card.classList.add(status.status);
        
        // Update status badge
        const badge = card.querySelector('.status-badge');
        if (badge) {
            badge.textContent = status.status.toUpperCase();
            badge.className = `status-badge ${status.status}`;
        }
        
        // Update status message
        const statusMsg = card.querySelector('.status-message');
        if (statusMsg) {
            statusMsg.textContent = status.message;
        }
        
        // Show/hide retry button
        const retryBtn = card.querySelector('.retry-btn');
        if (retryBtn) {
            retryBtn.style.display = status.status === 'failed' ? 'flex' : 'none';
        }
    }
    
    function updateStatusCounter() {
        if (!statusCounter) {
            console.warn("Status counter element not found");
            return;
        }
        
        const total = contacts.length;
        const selected = selectedContacts.size;
        
        // Count status types
        const statusCounts = {
            pending: 0,
            sending: 0,
            success: 0,
            failed: 0
        };
        
        Object.values(messageStatuses).forEach(status => {
            if (status && status.status) {
                statusCounts[status.status]++;
            }
        });
        
        // Update counter display with enhanced HTML for visual indicators
        statusCounter.innerHTML = `
            <div>
                <span class="counter-icon selected-icon"></span>
                Selected: <strong>${selected}/${total}</strong>
            </div>
            <div>
                <span class="counter-icon sending-icon"></span>
                Sending: <strong>${statusCounts.sending}</strong>
            </div>
            <div>
                <span class="counter-icon success-icon"></span>
                Success: <strong>${statusCounts.success}</strong>
            </div>
            <div>
                <span class="counter-icon failed-icon"></span>
                Failed: <strong>${statusCounts.failed}</strong>
            </div>
        `;
        
        console.log(`Status update: ${selected}/${total} selected, messageId: ${messageId}, callInProgress: ${callInProgress}`);
        
        // Enable/disable the send button
        if (sendBtn) {
            const shouldBeDisabled = selected === 0 || !messageId || callInProgress;
            sendBtn.disabled = shouldBeDisabled;
            
            if (shouldBeDisabled) {
                sendBtn.classList.add('disabled');
            } else {
                sendBtn.classList.remove('disabled');
                console.log("Send button enabled");
            }
        } else {
            console.warn("Send button not found when updating status");
        }
    }
    
    function formatPhone(phone) {
        if (!phone) return "No phone";
        
        // Format assuming international numbers
        if (phone.startsWith('+')) {
            const digits = phone.substring(1);
            if (digits.length === 11 && digits.startsWith('1')) { // US/Canada
                return `+1 (${digits.substring(1, 4)}) ${digits.substring(4, 7)}-${digits.substring(7)}`;
            }
            // Swedish numbers (+46)
            if (digits.startsWith('46')) {
                const nationalNumber = digits.substring(2);
                if (nationalNumber.startsWith('7')) { // Mobile numbers
                    return `+46 ${nationalNumber.substring(0, 2)} ${nationalNumber.substring(2, 5)} ${nationalNumber.substring(5)}`;
                }
                return `+46 ${nationalNumber.substring(0, 1)} ${nationalNumber.substring(1, 4)} ${nationalNumber.substring(4)}`;
            }
        }
        
        // Try to detect unformatted US phone numbers
        if (phone.length === 10 && /^\d+$/.test(phone)) {
            return `(${phone.substring(0, 3)}) ${phone.substring(3, 6)}-${phone.substring(6)}`;
        }
        
        // Default formatting for other numbers
        return phone;
    }
    
    function showNotification(message, type = 'info') {
        // Check if notification system exists in the parent page
        if (typeof window.showNotification === 'function') {
            window.showNotification(message, type);
            return;
        }
        
        // Create our own notification system
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.position = 'fixed';
        notification.style.bottom = '20px';
        notification.style.right = '20px';
        notification.style.padding = '15px 20px';
        notification.style.backgroundColor = type === 'error' ? '#dc3545' : 
                                             type === 'success' ? '#28a745' : 
                                             type === 'warning' ? '#ffc107' : '#17a2b8';
        notification.style.color = type === 'warning' ? '#212529' : 'white';
        notification.style.borderRadius = '8px';
        notification.style.boxShadow = '0 4px 15px rgba(0, 0, 0, 0.2)';
        notification.style.zIndex = '1010';
        notification.style.maxWidth = '400px';
        
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateY(10px)';
            notification.style.transition = 'opacity 0.3s, transform 0.3s';
            
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 5000);
    }
    
    // Apply status filter (used by filter chips)
    function applyStatusFilter(filter) {
        statusFilter = filter;
        renderContactCards();
    }
    
    // Setup event listeners
    function setupEventListeners() {
        // Message selection
        if (messagesSelect) {
            messagesSelect.addEventListener('change', async (e) => {
                messageId = e.target.value;
                
                // Get message type from the selected option
                const option = e.target.selectedOptions[0];
                if (option) {
                    messageType = option.dataset.type || 'voice';
                    
                    // Update message type dropdown
                    if (messageTypeSelect) {
                        messageTypeSelect.value = messageType;
                    }
                    
                    // Load message preview
                    if (messagePreview) {
                        messagePreview.textContent = 'Loading preview...';
                        const content = await fetchMessageContent(messageId);
                        messagePreview.textContent = content || 'Preview not available';
                    }
                }
                
                updateStatusCounter();
            });
        }
        
        // Group selection
        if (groupsSelect) {
            groupsSelect.addEventListener('change', (e) => {
                const newGroupId = e.target.value || null;
                
                // Only refetch if the group has changed
                if (newGroupId !== groupId) {
                    fetchContacts(newGroupId);
                }
            });
        }
        
        // Message type selection
        if (messageTypeSelect) {
            messageTypeSelect.addEventListener('change', (e) => {
                messageType = e.target.value;
                
                // Reset message selection
                messageId = null;
                if (messagesSelect) {
                    messagesSelect.value = '';
                }
                
                // Clear message preview
                if (messagePreview) {
                    messagePreview.textContent = '';
                }
                
                // Update filter options for message type
                filterMessages(messageType);
                
                updateStatusCounter();
            });
        }
        
        // Search input
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                searchTerm = e.target.value;
                renderContactCards();
            });
            
            // Add clear button to search (x button)
            searchInput.addEventListener('search', () => {
                searchTerm = searchInput.value;
                renderContactCards();
            });
        }
        
        // Select/deselect all buttons
        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', () => {
                const filteredContacts = applyFilters();
                filteredContacts.forEach(contact => {
                    selectedContacts.add(contact.id);
                });
                renderContactCards();
            });
        }
        
        if (deselectAllBtn) {
            deselectAllBtn.addEventListener('click', () => {
                selectedContacts.clear();
                renderContactCards();
            });
        }
        
        // Send button
        if (sendBtn) {
            console.log("Setting up send button event listener");
            sendBtn.disabled = selectedContacts.size === 0 || !messageId;
            sendBtn.addEventListener('click', function(e) {
                console.log("Send button clicked - messageId:", messageId);
                console.log("Selected contacts:", Array.from(selectedContacts));
                sendToSelected();
            });
        }
        
        // Debug send button
        const debugSendBtn = document.getElementById('debug-send');
        if (debugSendBtn) {
            console.log("Setting up debug send button event listener");
            debugSendBtn.addEventListener('click', function(e) {
                console.log("Debug send button clicked");
                
                // Force selections if none exist
                if (selectedContacts.size === 0 && contacts.length > 0) {
                    console.log("No contacts selected, forcing selection of first contact");
                    selectedContacts.add(contacts[0].id);
                    
                    // Update UI to show selection
                    const card = document.querySelector(`.contact-card[data-id="${contacts[0].id}"]`);
                    if (card) {
                        card.classList.add('selected');
                    }
                }
                
                // Force message ID if none selected
                if (!messageId && messages.length > 0) {
                    console.log("No message selected, forcing selection of first message");
                    messageId = messages[0].id;
                    messageType = messages[0].message_type || 'voice';
                    console.log("Forced messageId:", messageId, "messageType:", messageType);
                    
                    // Update UI to show selected message
                    if (messagesSelect) {
                        messagesSelect.value = messageId;
                    }
                }
                
                // Debug information
                console.log("Debug info before send:");
                console.log("- messageId:", messageId);
                console.log("- messageType:", messageType);
                console.log("- selectedContacts:", Array.from(selectedContacts));
                console.log("- callInProgress:", callInProgress);
                
                // Fix progress window styles if needed
                const progressOverlay = document.getElementById('progress-overlay');
                if (progressOverlay) {
                    // Fix the styles to ensure it displays correctly
                    progressOverlay.style.position = 'fixed';
                    progressOverlay.style.top = '0';
                    progressOverlay.style.left = '0';
                    progressOverlay.style.width = '100vw';
                    progressOverlay.style.height = '100vh';
                    progressOverlay.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
                    progressOverlay.style.zIndex = '2000';
                    progressOverlay.style.display = 'none';
                    
                    // Also fix the window position
                    const progressWindow = progressOverlay.querySelector('.progress-window');
                    if (progressWindow) {
                        progressWindow.style.position = 'relative';
                        progressWindow.style.top = 'auto';
                        progressWindow.style.left = 'auto';
                        progressWindow.style.transform = 'none';
                        progressWindow.style.margin = 'auto';
                    }
                }
                
                // Force not in progress
                callInProgress = false;
                
                // Force trigger the send function
                sendToSelected();
            });
        }
        
        // Set up refresh runs button
        const refreshRunsBtn = document.getElementById('refresh-runs');
        if (refreshRunsBtn) {
            refreshRunsBtn.addEventListener('click', refreshCallRuns);
        }
        
        // Set up call run detail close button
        const closeDetailBtn = document.getElementById('close-detail');
        if (closeDetailBtn) {
            closeDetailBtn.addEventListener('click', () => {
                const detailElement = document.getElementById('call-run-detail');
                if (detailElement) {
                    detailElement.classList.remove('active');
                }
            });
        }
        
        // Set up refresh detail button
        const refreshDetailBtn = document.getElementById('refresh-detail');
        if (refreshDetailBtn) {
            refreshDetailBtn.addEventListener('click', () => {
                if (currentRunDetail) {
                    viewCallRunDetails(currentRunDetail.id);
                }
            });
        }
    }
    
    // Filter messages by type in dropdown
    function filterMessages(type) {
        if (!messagesSelect) return;
        
        const options = messagesSelect.querySelectorAll('option');
        const optgroups = messagesSelect.querySelectorAll('optgroup');
        
        // Show or hide option groups based on message type
        optgroups.forEach(group => {
            if (group.label === 'Voice Messages' && type === 'voice') {
                group.style.display = '';
            } else if (group.label === 'SMS Messages' && type === 'sms') {
                group.style.display = '';
            } else {
                group.style.display = 'none';
            }
        });
        
        // Show/hide individual options
        options.forEach(option => {
            if (!option.dataset.type) return;
            
            if (option.dataset.type === type || option.dataset.messageType === 'both') {
                option.style.display = '';
            } else {
                option.style.display = 'none';
            }
        });
    }
    
    // Call Runs Management
    let callRuns = [];
    let currentRunDetail = null;
    
    async function fetchCallRuns(status = 'all', dateRange = 'all') {
        const callRunsList = document.getElementById('call-runs-list');
        
        if (!callRunsList) {
            console.error('Call runs list element not found!');
            return;
        }
        
        try {
            // Clear existing content except the empty state
            const emptyState = callRunsList.querySelector('.empty-state');
            callRunsList.innerHTML = '';
            
            if (emptyState) {
                callRunsList.appendChild(emptyState);
            }
            
            // Add loading indicator
            const loadingIndicator = document.createElement('div');
            loadingIndicator.className = 'contact-cards-loading';
            loadingIndicator.innerHTML = '<div class="spinner"></div>';
            callRunsList.appendChild(loadingIndicator);
            
            // Show empty state initially
            if (emptyState) {
                emptyState.style.display = 'none';
            }
            
            // Build query string with filters
            let queryParams = new URLSearchParams();
            if (status !== 'all') {
                queryParams.append('status', status);
            }
            if (dateRange !== 'all') {
                queryParams.append('date_range', dateRange);
            }
            queryParams.append('limit', '50');
            
            // Just return empty results for now, as call runs aren't in the API docs
            callRuns = [];
            console.log('Call runs feature currently unavailable in production mode');
            
            // Remove loading indicator
            callRunsList.removeChild(loadingIndicator);
            
            // Show or hide empty state
            if (emptyState) {
                emptyState.style.display = callRuns.length === 0 ? 'block' : 'none';
            }
            
            // Apply filters
            let filteredRuns = callRuns;
            if (status !== 'all') {
                filteredRuns = filteredRuns.filter(run => run.status === status);
            }
            
            // Apply date filter
            if (dateRange !== 'all') {
                const now = new Date();
                let cutoffDate = new Date();
                
                if (dateRange === 'today') {
                    cutoffDate.setHours(0, 0, 0, 0);
                } else if (dateRange === 'week') {
                    cutoffDate.setDate(now.getDate() - 7);
                } else if (dateRange === 'month') {
                    cutoffDate.setDate(now.getDate() - 30);
                }
                
                filteredRuns = filteredRuns.filter(run => {
                    const runDate = new Date(run.started_at);
                    return runDate >= cutoffDate;
                });
            }
            
            // Render call runs
            filteredRuns.forEach(run => {
                const runElement = createCallRunElement(run);
                callRunsList.appendChild(runElement);
            });
            
            return filteredRuns;
        } catch (error) {
            console.error('Error in fetchCallRuns:', error);
            
            // Remove loading if error
            const loadingElement = callRunsList.querySelector('.contact-cards-loading');
            if (loadingElement) {
                callRunsList.removeChild(loadingElement);
            }
            
            // Show empty state with error message
            if (emptyState) {
                emptyState.style.display = 'block';
                emptyState.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="8" x2="12" y2="12"></line>
                        <line x1="12" y1="16" x2="12.01" y2="16"></line>
                    </svg>
                    <h3>Error Loading Call Runs</h3>
                    <p>${error.message}</p>
                `;
            }
            
            return [];
        }
    }
    
    function createCallRunElement(run) {
        const completionPercent = run.total_calls > 0 
            ? Math.round((run.completed_calls / run.total_calls) * 100) 
            : 0;
        
        const runElement = document.createElement('div');
        runElement.className = 'call-run-item';
        runElement.dataset.id = run.id;
        
        // Format dates
        const startedDate = new Date(run.started_at);
        const formattedStartDate = startedDate.toLocaleString();
        
        const runInfo = document.createElement('div');
        runInfo.className = 'run-info';
        
        // Run name
        const nameDiv = document.createElement('div');
        nameDiv.className = 'run-name';
        nameDiv.textContent = run.name;
        runInfo.appendChild(nameDiv);
        
        // Run metadata
        const metaDiv = document.createElement('div');
        metaDiv.className = 'run-meta';
        
        const timeSpan = document.createElement('span');
        timeSpan.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
            ${formattedStartDate}
        `;
        metaDiv.appendChild(timeSpan);
        
        const statusSpan = document.createElement('span');
        statusSpan.className = `run-status-badge ${run.status}`;
        statusSpan.textContent = run.status === 'in_progress' ? 'In Progress' : (run.status === 'completed' ? 'Completed' : 'Cancelled');
        metaDiv.appendChild(statusSpan);
        
        runInfo.appendChild(metaDiv);
        runElement.appendChild(runInfo);
        
        // Run stats
        const statsDiv = document.createElement('div');
        statsDiv.className = 'run-stats';
        
        // Total calls stat
        const totalStat = document.createElement('div');
        totalStat.className = 'stat-item';
        totalStat.innerHTML = `
            <div class="stat-value">${run.total_calls}</div>
            <div class="stat-label">Total</div>
        `;
        statsDiv.appendChild(totalStat);
        
        // Completed calls stat
        const completedStat = document.createElement('div');
        completedStat.className = 'stat-item';
        completedStat.innerHTML = `
            <div class="stat-value">${run.completed_calls}</div>
            <div class="stat-label">Done</div>
        `;
        statsDiv.appendChild(completedStat);
        
        // Answered calls stat
        const answeredStat = document.createElement('div');
        answeredStat.className = 'stat-item';
        answeredStat.innerHTML = `
            <div class="stat-value">${run.answered_calls}</div>
            <div class="stat-label">Answered</div>
        `;
        statsDiv.appendChild(answeredStat);
        
        // Completion percentage stat
        const percentStat = document.createElement('div');
        percentStat.className = 'stat-item';
        percentStat.innerHTML = `
            <div class="stat-value">${completionPercent}%</div>
            <div class="stat-label">Complete</div>
        `;
        statsDiv.appendChild(percentStat);
        
        runElement.appendChild(statsDiv);
        
        // Add event listener for viewing details
        runElement.addEventListener('click', () => {
            viewCallRunDetails(run.id);
        });
        
        return runElement;
    }
    
    async function viewCallRunDetails(runId) {
        const detailElement = document.getElementById('call-run-detail');
        
        if (!detailElement) {
            console.error('Call run detail element not found!');
            return;
        }
        
        try {
            // Show loading state in the detail view
            detailElement.classList.add('active');
            document.getElementById('detail-name').textContent = 'Loading...';
            document.getElementById('detail-status').textContent = 'Loading...';
            document.getElementById('detail-progress').style.width = '0%';
            document.getElementById('detail-progress-text').textContent = '0%';
            
            const tableBody = document.getElementById('call-log-tbody');
            tableBody.innerHTML = '<tr><td colspan="6" style="text-align:center;">Loading call details...</td></tr>';
            
            // Call run details unavailable in production mode
            console.error('Call run details feature not available in production mode');
            throw new Error('Call run details are not available in production mode');
            
            const run = currentRunDetail;
            
            // Calculate completion percentage
            const completionPercent = run.total_calls > 0 
                ? Math.round((run.completed_calls / run.total_calls) * 100) 
                : 0;
            
            // Format dates
            const startedDate = new Date(run.started_at);
            const formattedStartDate = startedDate.toLocaleString();
            const formattedCompletedDate = run.completed_at 
                ? new Date(run.completed_at).toLocaleString() 
                : 'Not yet completed';
            
            // Update detail view elements
            document.getElementById('detail-name').textContent = run.name;
            document.getElementById('detail-status').textContent = run.status === 'in_progress' ? 'In Progress' : 
                                                                 (run.status === 'completed' ? 'Completed' : 'Cancelled');
            document.getElementById('detail-started').textContent = formattedStartDate;
            document.getElementById('detail-completed-date').textContent = formattedCompletedDate;
            document.getElementById('detail-total').textContent = run.total_calls;
            document.getElementById('detail-completed').textContent = run.completed_calls;
            document.getElementById('detail-answered').textContent = run.answered_calls;
            
            // Update progress bar
            document.getElementById('detail-progress').style.width = `${completionPercent}%`;
            document.getElementById('detail-progress-text').textContent = `${completionPercent}%`;
            
            // Populate call log table
            tableBody.innerHTML = '';
            
            if (run.calls && run.calls.length > 0) {
                run.calls.forEach(call => {
                    const row = document.createElement('tr');
                    
                    // Format call date
                    const callDate = new Date(call.started_at);
                    const formattedCallDate = callDate.toLocaleString();
                    
                    row.innerHTML = `
                        <td>${call.contact_name || 'Unknown'}</td>
                        <td>${call.phone_number || 'Unknown'}</td>
                        <td>
                            <div class="status-cell">
                                <div class="status-icon ${call.status}"></div>
                                ${call.status}
                            </div>
                        </td>
                        <td>${formattedCallDate}</td>
                        <td>${call.answered ? 'Yes' : 'No'}</td>
                        <td>${call.digits || '-'}</td>
                    `;
                    
                    tableBody.appendChild(row);
                });
            } else {
                const emptyRow = document.createElement('tr');
                emptyRow.innerHTML = `
                    <td colspan="6" style="text-align: center; padding: 20px;">
                        No call logs available for this run
                    </td>
                `;
                tableBody.appendChild(emptyRow);
            }
            
            // Set up export button
            const exportButton = document.getElementById('export-logs');
            if (exportButton) {
                exportButton.onclick = () => exportCallRunCSV(run);
            }
            
        } catch (error) {
            console.error('Error viewing call run details:', error);
            showNotification('Error loading call run details: ' + error.message, 'error');
            
            // Show error in detail panel
            document.getElementById('detail-name').textContent = 'Error Loading Details';
            document.getElementById('detail-status').textContent = 'Error';
            
            const tableBody = document.getElementById('call-log-tbody');
            tableBody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; color: #dc3545; padding: 20px;">
                        Error loading call details: ${error.message}
                    </td>
                </tr>
            `;
        }
    }
    
    // Function to format call status for display
    function formatCallStatus(status) {
        if (!status) return 'unknown';
        
        const statusMap = {
            'completed': 'Completed',
            'no-answer': 'No Answer',
            'busy': 'Busy',
            'failed': 'Failed',
            'error': 'Error',
            'in-progress': 'In Progress',
            'queued': 'Queued'
        };
        
        return statusMap[status] || status;
    }
    
    function exportCallRunCSV(run) {
        if (!run || !run.calls || run.calls.length === 0) {
            showNotification('No call data to export', 'warning');
            return;
        }
        
        // Create CSV content
        let csvContent = 'Contact Name,Phone Number,Status,Started At,Answered,DTMF Input\n';
        
        run.calls.forEach(call => {
            const formattedDate = new Date(call.started_at).toLocaleString();
            const row = [
                `"${(call.contact_name || 'Unknown').replace(/"/g, '""')}"`,
                `"${(call.phone_number || 'Unknown').replace(/"/g, '""')}"`,
                `"${call.status}"`,
                `"${formattedDate}"`,
                call.answered ? 'Yes' : 'No',
                `"${call.digits || ''}"`
            ].join(',');
            
            csvContent += row + '\n';
        });
        
        // Create download link
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `call_run_${run.id.substring(0, 8)}_${new Date().toISOString().slice(0, 10)}.csv`;
        
        // Trigger download
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Clean up
        URL.revokeObjectURL(url);
        showNotification('CSV export complete', 'success');
    }
    
    // Function to refresh call runs
    function refreshCallRuns() {
        const statusFilter = document.getElementById('run-status-filter');
        const dateFilter = document.getElementById('run-date-filter');
        return fetchCallRuns(
            statusFilter ? statusFilter.value : 'all',
            dateFilter ? dateFilter.value : 'all'
        );
    }
    
    // Initialize the component
    initialize();
    
    // Return public methods
    return {
        refresh: function() {
            console.log("Refreshing contacts with groupId:", groupId);
            return fetchContacts(groupId);
        },
        refreshCallRuns: refreshCallRuns,
        applyStatusFilter: function(filter) {
            console.log("Applying status filter:", filter);
            statusFilter = filter;
            renderContactCards();
        },
        updateFilter: function(term) {
            console.log("Updating search filter:", term);
            searchTerm = term;
            renderContactCards();
        },
        forceRefresh: function() {
            console.log("Force refreshing contact cards UI");
            // First, ensure we have the DOM elements
            getDOMElements();
            
            // Then render with a delay
            setTimeout(() => {
                // Force show container
                if (contactCardsContainer) {
                    contactCardsContainer.style.display = 'grid';
                }
                
                // Render cards
                renderContactCards();
                
                console.log("Force refresh complete");
            }, 500);
            return true;
        },
        debug: function() {
            // Return debug info
            return {
                elementsFound: getDOMElements(),
                contacts: contacts.length,
                messages: messages.length,
                groups: groups.length,
                selectedContacts: selectedContacts.size,
                messageId: messageId,
                groupId: groupId,
                containerVisible: contactCardsContainer ? contactCardsContainer.style.display : 'unknown'
            };
        },
        forceRender: function() {
            // Emergency function to force everything to render
            console.log("EMERGENCY RENDER: Forcing complete re-render of UI");
            getDOMElements();
            
            if (contactCardsContainer) {
                contactCardsContainer.innerHTML = '';
                contactCardsContainer.style.display = 'grid';
                
                // Create a direct render of contacts
                contacts.forEach(contact => {
                    const card = createContactCard(contact);
                    contactCardsContainer.appendChild(card);
                });
                
                console.log(`Direct rendering complete: ${contacts.length} contacts`);
                return true;
            } else {
                console.error("EMERGENCY RENDER FAILED: contact-cards-container not found");
                return false;
            }
        },
        triggerSend: function() {
            // Direct access to the send function for debugging
            console.log("Manual trigger of send function");
            return sendToSelected();
        },
        manualShowProgress: function(title, message) {
            // Emergency manual progress window function
            const overlay = document.getElementById('progress-overlay');
            
            if (!overlay) {
                console.error("Cannot show progress window: overlay not found");
                alert(title + ": " + message);
                return false;
            }
            
            // Force correct styling
            overlay.style.position = 'fixed';
            overlay.style.top = '0';
            overlay.style.left = '0';
            overlay.style.width = '100vw';
            overlay.style.height = '100vh';
            overlay.style.backgroundColor = 'rgba(0,0,0,0.8)';
            overlay.style.zIndex = '9999';
            overlay.style.display = 'flex';
            overlay.style.justifyContent = 'center';
            overlay.style.alignItems = 'center';
            
            // Get child elements
            const titleElem = document.getElementById('progress-title');
            const statusElem = document.getElementById('progress-status');
            
            if (titleElem) titleElem.textContent = title || 'Progress';
            if (statusElem) statusElem.textContent = message || 'Working...';
            
            // Force show
            overlay.classList.add('active');
            return true;
        },
        updateCardStatus: function(contactId, status, message) {
            // Helper for debugging card status updates
            if (!messageStatuses[contactId]) {
                messageStatuses[contactId] = { status: 'pending', message: 'Not sent yet' };
            }
            
            messageStatuses[contactId].status = status || 'pending';
            messageStatuses[contactId].message = message || 'Status updated manually';
            
            updateContactCardStatus(contactId);
            return true;
        }
    };
}

// Export for use in main script
window.initGroupMessenger = initGroupMessenger;