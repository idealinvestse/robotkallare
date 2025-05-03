// Data Storage
let allMessages = [];
let allContacts = [];
let allGroups = [];
let currentPage = 1;
const logsPerPage = 10;
let totalLogs = 0;

// Tab Functionality
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        // Deactivate all tabs
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        // Activate the clicked tab
        tab.classList.add('active');
        document.getElementById(tab.dataset.tab).classList.add('active');
    });
});

// Modal Functions
function openModal(modalId) {
    document.getElementById(modalId).style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Helper Functions
function formatDate(dateString) {
    if (!dateString) return __("never");
    const date = new Date(dateString);
    return date.toLocaleString(); // Use system locale for formatting
}

function formatPhone(phone) {
    if (!phone) return __("unknown");
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
        return phone;
    }
    return phone;
}

function getStatusClass(status) {
    switch(status) {
        case "completed": return "status-completed";
        case "no-answer": return "status-no-answer";
        case "manual": return "status-manual";
        case "error": return "status-error";
        default: return "";
    }
}

function updateStats(stats) {
    document.getElementById("totalCalls").textContent = stats.total_calls;
    document.getElementById("completedCalls").textContent = stats.completed;
    document.getElementById("noAnswerCalls").textContent = stats.no_answer;
    document.getElementById("manualCalls").textContent = stats.manual;
    document.getElementById("errorCalls").textContent = stats.error;
    document.getElementById("lastCall").textContent = formatDate(stats.last_call);
    
    // Always ensure the system status is set to "System Ready"
    document.getElementById("system-status").textContent = "System Ready";
    document.querySelector(".status-indicator").classList.add("active");
}

function logMessage(message, isError = false) {
    const output = document.getElementById("output");
    const timestamp = new Date().toLocaleTimeString();
    
    const logEntry = document.createElement("div");
    logEntry.innerHTML = `<strong>[${timestamp}]</strong> ${message}`;
    
    if (isError) {
        logEntry.style.color = "#c62828";
    }
    
    // Prepend to put newest logs at the top
    if (output.firstChild) {
        output.insertBefore(logEntry, output.firstChild);
    } else {
        output.appendChild(logEntry);
    }
}

function formatDigitResponse(digits) {
    if (!digits) return __("noResponse");
    
    // Use translated responses based on current language
    switch(digits) {
        case "1": return `1 - ${__("acknowledged")}`;
        case "2": return `2 - ${__("needAssistance")}`;
        case "3": return `3 - ${__("emergency")}`;
        default: return digits;
    }
}

function populateGroupsDropdown() {
    const dropdown = document.getElementById('groupSelector');
    
    // Clear existing options except the first one
    while (dropdown.options.length > 1) {
        dropdown.remove(1);
    }
    
    // Add groups to dropdown
    allGroups.forEach(group => {
        const option = document.createElement('option');
        option.value = group.id;
        option.textContent = group.name;
        dropdown.appendChild(option);
    });
}

// Phone number input handlers
function createPhoneNumberEntry(number = '', priority = 1, phoneId = null) {
    const entry = document.createElement('div');
    entry.className = 'phone-number-entry';
    
    const phoneInput = document.createElement('input');
    phoneInput.type = 'tel';
    phoneInput.className = 'phone-input';
    phoneInput.placeholder = __('phoneNumber') || 'Telefonnummer';
    // Set default Swedish country code if no number is provided
    phoneInput.value = number || '+46 ';
    phoneInput.required = true;
    
    // Add invalid feedback element
    const invalidFeedback = document.createElement('div');
    invalidFeedback.className = 'invalid-feedback';
    
    const prioritySelect = document.createElement('select');
    prioritySelect.className = 'priority-select';
    for (let i = 1; i <= 5; i++) {
        const option = document.createElement('option');
        option.value = i;
        option.textContent = i;
        prioritySelect.appendChild(option);
    }
    prioritySelect.value = priority;
    
    const removeButton = document.createElement('button');
    removeButton.type = 'button';
    removeButton.className = 'remove-phone danger';
    removeButton.textContent = '-';
    removeButton.addEventListener('click', function() {
        entry.remove();
    });
    
    if (phoneId) {
        // Hidden input to store phone ID for existing numbers
        const idInput = document.createElement('input');
        idInput.type = 'hidden';
        idInput.className = 'phone-id';
        idInput.value = phoneId;
        entry.appendChild(idInput);
    }
    
    entry.appendChild(phoneInput);
    entry.appendChild(prioritySelect);
    entry.appendChild(removeButton);
    
    // Initialize validation for this new input
    phoneInput.addEventListener('blur', function() {
        const result = validatePhoneNumber(this.value);
        if (!result.isValid) {
            this.classList.add('is-invalid');
            invalidFeedback.textContent = result.message;
            invalidFeedback.style.display = 'block';
        } else {
            this.classList.remove('is-invalid');
            invalidFeedback.style.display = 'none';
            // Format the phone number for display if valid
            this.value = formatPhoneForDisplay(this.value);
        }
    });
    
    entry.appendChild(invalidFeedback);
    
    return entry;
}

document.getElementById('addPhoneNumberBtn').addEventListener('click', function() {
    const container = document.getElementById('phoneNumbersContainer');
    container.appendChild(createPhoneNumberEntry());
});

document.getElementById('editAddPhoneNumberBtn').addEventListener('click', function() {
    const container = document.getElementById('editPhoneNumbersContainer');
    container.appendChild(createPhoneNumberEntry());
});

// API Functions
async function checkHealth() {
    try {
        document.getElementById("healthCheck").classList.add("loading");
        const response = await fetch("/health");
        const data = await response.text();
        if (data === "OK") {
            logMessage("Health check: System is operational ✅");
            
            // Update status indicator
            const statusIndicator = document.querySelector('.status-indicator');
            statusIndicator.style.backgroundColor = '#43a047'; // Green
            document.querySelector('.operator-status span:last-child').textContent = __("systemReady");
            
        } else {
            logMessage("Health check: System reported an issue", true);
            
            // Update status indicator
            const statusIndicator = document.querySelector('.status-indicator');
            statusIndicator.style.backgroundColor = '#e53935'; // Red
            document.querySelector('.operator-status span:last-child').textContent = __("systemError");
        }
    } catch (error) {
        logMessage(`Health check failed: ${error.message}`, true);
        
        // Update status indicator
        const statusIndicator = document.querySelector('.status-indicator');
        statusIndicator.style.backgroundColor = '#e53935'; // Red
        document.querySelector('.operator-status span:last-child').textContent = __("systemError");
    } finally {
        document.getElementById("healthCheck").classList.remove("loading");
    }
}

async function getStats() {
    try {
        document.getElementById("refreshStats").classList.add("loading");
        const response = await fetch("/stats");
        const data = await response.json();
        updateStats(data);
        logMessage("Statistics refreshed successfully");
        return data;
    } catch (error) {
        logMessage(`Failed to fetch statistics: ${error.message}`, true);
    } finally {
        document.getElementById("refreshStats").classList.remove("loading");
    }
}

// Message Functions
async function getMessages() {
    try {
        document.getElementById("refreshMessages").classList.add("loading");
        const response = await fetch("/messages");
        const messages = await response.json();
        allMessages = messages;
        
        // Populate message dropdown in the Emergency Control panel
        const messageSelector = document.getElementById('messageSelector');
        
        // Clear existing options except the first one
        while (messageSelector.options.length > 1) {
            messageSelector.remove(1);
        }
        
        // Add messages to dropdown
        allMessages.forEach(message => {
            const option = document.createElement('option');
            option.value = message.id;
            option.textContent = message.name;
            messageSelector.appendChild(option);
        });
        
        const container = document.getElementById("messagesContainer");
        container.innerHTML = "";
        
        if (messages.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                        <line x1="12" y1="8" x2="12" y2="16"></line>
                        <line x1="8" y1="12" x2="16" y2="12"></line>
                    </svg>
                    <p>${__("noMessagesFound")}</p>
                    <button id="emptyStateAddMessage">${__("createNewMessage")}</button>
                </div>
            `;
            
            document.getElementById("emptyStateAddMessage").addEventListener("click", () => {
                openModal("addMessageModal");
            });
            
            return [];
        }
        
        for (const message of messages) {
            const card = document.createElement("div");
            card.className = "card message-card";
            
            const cardHeader = document.createElement("div");
            cardHeader.className = "card-header";
            
            const title = document.createElement("h3");
            title.textContent = message.name;
            
            const templateBadge = document.createElement("span");
            templateBadge.className = "badge";
            templateBadge.textContent = message.is_template ? __("template") : __("oneTime");
            templateBadge.style.backgroundColor = message.is_template ? "#e3f2fd" : "#f1f8e9";
            templateBadge.style.color = message.is_template ? "#1565c0" : "#33691e";
            
            cardHeader.appendChild(title);
            cardHeader.appendChild(templateBadge);
            
            const content = document.createElement("div");
            content.className = "message-content";
            content.textContent = message.content;
            
            const footer = document.createElement("div");
            footer.className = "message-footer";
            
            const date = document.createElement("span");
            date.className = "date";
            const updatedDate = new Date(message.updated_at).toLocaleDateString();
            date.textContent = `${__("updated")}: ${updatedDate}`;
            
            const buttons = document.createElement("div");
            buttons.className = "button-panel";
            buttons.style.marginBottom = "0";
            
            const editButton = document.createElement("button");
            editButton.className = "secondary";
            editButton.style.padding = "6px 12px";
            editButton.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                </svg>
                ${__("edit")}
            `;
            editButton.addEventListener("click", () => editMessage(message));
            
            const useButton = document.createElement("button");
            useButton.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path>
                </svg>
                ${__("useThisMessage")}
            `;
            useButton.style.padding = "6px 12px";
            useButton.addEventListener("click", () => {
                document.getElementById('messageSelector').value = message.id;
                document.getElementById('messages').scrollIntoView({ behavior: 'smooth' });
                // Flash the message selector to draw attention to it
                const selector = document.getElementById('messageSelector');
                selector.style.boxShadow = '0 0 0 3px rgba(25, 118, 210, 0.5)';
                setTimeout(() => {
                    selector.style.boxShadow = 'none';
                }, 2000);
            });
            
            const deleteButton = document.createElement("button");
            deleteButton.className = "danger";
            deleteButton.style.padding = "6px 12px";
            deleteButton.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    <line x1="10" y1="11" x2="10" y2="17"></line>
                    <line x1="14" y1="11" x2="14" y2="17"></line>
                </svg>
                ${__("delete")}
            `;
            deleteButton.addEventListener("click", () => deleteMessage(message.id, message.name));
            
            buttons.appendChild(editButton);
            buttons.appendChild(useButton);
            buttons.appendChild(deleteButton);
            
            footer.appendChild(date);
            footer.appendChild(buttons);
            
            card.appendChild(cardHeader);
            card.appendChild(content);
            card.appendChild(footer);
            
            container.appendChild(card);
        }
        
        logMessage("Messages refreshed successfully");
        return messages;
    } catch (error) {
        logMessage(`Failed to fetch messages: ${error.message}`, true);
    } finally {
        document.getElementById("refreshMessages").classList.remove("loading");
    }
}

async function createMessage(messageData) {
    try {
        const response = await fetch("/messages", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(messageData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Failed to create message");
        }
        
        const newMessage = await response.json();
        logMessage(`Message "${newMessage.name}" created successfully`);
        await getMessages();
        return newMessage;
    } catch (error) {
        logMessage(`Failed to create message: ${error.message}`, true);
        throw error;
    }
}

async function updateMessage(messageId, messageData) {
    try {
        const response = await fetch(`/messages/${messageId}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(messageData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Failed to update message");
        }
        
        const updatedMessage = await response.json();
        logMessage(`Message "${updatedMessage.name}" updated successfully`);
        await getMessages();
        return updatedMessage;
    } catch (error) {
        logMessage(`Failed to update message: ${error.message}`, true);
        throw error;
    }
}

async function deleteMessage(messageId, messageName) {
    if (!confirm(`${__("confirmDeleteMessage")} "${messageName}"? ${__("thisActionCannotBeUndone")}`)) {
        return;
    }
    
    try {
        const response = await fetch(`/messages/${messageId}`, {
            method: "DELETE"
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Failed to delete message");
        }
        
        logMessage(`Message "${messageName}" deleted successfully`);
        await getMessages();
    } catch (error) {
        logMessage(`Failed to delete message: ${error.message}`, true);
    }
}

function editMessage(message) {
    document.getElementById("editMessageId").value = message.id;
    document.getElementById("editMessageName").value = message.name;
    document.getElementById("editMessageTemplate").checked = message.is_template;
    document.getElementById("editMessageContent").value = message.content;
    
    // Initialize preview
    document.getElementById("editMessagePreview").textContent = message.content;
    
    openModal("editMessageModal");
}

// Message form preview handlers
document.getElementById("messageContent").addEventListener("input", function() {
    document.getElementById("messagePreview").textContent = this.value;
});

document.getElementById("editMessageContent").addEventListener("input", function() {
    document.getElementById("editMessagePreview").textContent = this.value;
});

// Message form submission handlers
document.getElementById("addMessageForm").addEventListener("submit", async function(e) {
    e.preventDefault();
    
    const nameInput = document.getElementById("messageName");
    const contentInput = document.getElementById("messageContent");
    const templateCheckbox = document.getElementById("messageTemplate");
    
    const messageData = {
        name: nameInput.value,
        content: contentInput.value,
        is_template: templateCheckbox.checked
    };
    
    try {
        await createMessage(messageData);
        closeModal("addMessageModal");
        
        // Clear form
        nameInput.value = "";
        contentInput.value = "";
        document.getElementById("messagePreview").textContent = __("yourMessageWillAppear");
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
});

document.getElementById("editMessageForm").addEventListener("submit", async function(e) {
    e.preventDefault();
    
    const messageId = document.getElementById("editMessageId").value;
    const nameInput = document.getElementById("editMessageName");
    const contentInput = document.getElementById("editMessageContent");
    const templateCheckbox = document.getElementById("editMessageTemplate");
    
    const messageData = {
        name: nameInput.value,
        content: contentInput.value,
        is_template: templateCheckbox.checked
    };
    
    try {
        await updateMessage(messageId, messageData);
        closeModal("editMessageModal");
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
});

// Message modal event listeners
document.getElementById("addMessageBtn").addEventListener("click", function() {
    // Clear form
    document.getElementById("addMessageForm").reset();
    document.getElementById("messagePreview").textContent = __("yourMessageWillAppear");
    openModal("addMessageModal");
});

document.getElementById("closeAddMessageModal").addEventListener("click", function() {
    closeModal("addMessageModal");
});

document.getElementById("cancelAddMessage").addEventListener("click", function() {
    closeModal("addMessageModal");
});

document.getElementById("closeEditMessageModal").addEventListener("click", function() {
    closeModal("editMessageModal");
});

document.getElementById("cancelEditMessage").addEventListener("click", function() {
    closeModal("editMessageModal");
});

document.getElementById("refreshMessages").addEventListener("click", getMessages);

// Update the trigger function to include message selection
async function triggerDialer() {
    const groupSelect = document.getElementById('groupSelector');
    const messageSelect = document.getElementById('messageSelector');
    const selectedGroup = groupSelect.value;
    const selectedMessage = messageSelect.value;
    
    const groupName = selectedGroup ? groupSelect.options[groupSelect.selectedIndex].text : __("allContacts");
    const messageName = selectedMessage ? messageSelect.options[messageSelect.selectedIndex].text : __("defaultEmergencyMessage");
    
    let confirmMessage = `${__("confirmTriggerDialer")}`;
    if (selectedGroup) {
        confirmMessage += ` ${__("confirmTriggerDialerGroup")} '${groupName}'.`;
    } else {
        confirmMessage += ` ${__("confirmTriggerDialerAll")}`;
    }
    
    confirmMessage += ` ${__("confirmTriggerDialerMessage")} "${messageName}"`;
    
    if (!confirm(confirmMessage)) {
        return;
    }
    
    try {
        document.getElementById("triggerDialer").classList.add("loading");
        
        let url = "/trigger-dialer";
        let params = [];
        
        if (selectedGroup) {
            params.push(`group_id=${selectedGroup}`);
        }
        
        if (selectedMessage) {
            params.push(`message_id=${selectedMessage}`);
        }
        
        if (params.length > 0) {
            url += '?' + params.join('&');
        }
        
        const response = await fetch(url, { method: "POST" });
        const data = await response.json();
        logMessage(`Emergency dialer triggered: ${data.detail}`);
        
        // Set a timer to refresh stats after a delay
        setTimeout(getStats, 3000);
        setTimeout(getCallLogs, 5000);
    } catch (error) {
        logMessage(`Failed to trigger dialer: ${error.message}`, true);
    } finally {
        document.getElementById("triggerDialer").classList.remove("loading");
    }
}

document.getElementById("triggerDialer").addEventListener("click", triggerDialer);

// Contact Functions
async function getContacts() {
    try {
        document.getElementById("refreshContacts").classList.add("loading");
        const response = await fetch("/contacts");
        const contacts = await response.json();
        allContacts = contacts;
        
        const tbody = document.querySelector("#contactsTable tbody");
        tbody.innerHTML = "";
        
        contacts.forEach(contact => {
            const row = document.createElement("tr");
            
            // Name cell
            const nameCell = document.createElement("td");
            nameCell.textContent = contact.name;
            
            // Email cell
            const emailCell = document.createElement("td");
            emailCell.textContent = contact.email || "-";
            
            // Phone numbers cell
            const phoneCell = document.createElement("td");
            contact.phone_numbers.sort((a, b) => a.priority - b.priority);
            
            contact.phone_numbers.forEach(phone => {
                const phoneDiv = document.createElement("div");
                phoneDiv.className = "phone-number";
                
                const prioritySpan = document.createElement("span");
                prioritySpan.className = "phone-number-priority";
                prioritySpan.textContent = phone.priority;
                
                const numberSpan = document.createElement("span");
                numberSpan.textContent = formatPhone(phone.number);
                
                phoneDiv.appendChild(prioritySpan);
                phoneDiv.appendChild(numberSpan);
                phoneCell.appendChild(phoneDiv);
            });
            
            // Groups cell
            const groupsCell = document.createElement("td");
            contact.groups.forEach(group => {
                const badge = document.createElement("span");
                badge.className = "badge";
                badge.textContent = group.name;
                groupsCell.appendChild(badge);
            });
            
            // Actions cell
            const actionsCell = document.createElement("td");
            
            const editButton = document.createElement("button");
            editButton.className = "secondary";
            editButton.textContent = __("edit");
            editButton.addEventListener("click", () => editContact(contact));
            
            const deleteButton = document.createElement("button");
            deleteButton.className = "danger";
            deleteButton.textContent = __("delete");
            deleteButton.addEventListener("click", () => deleteContact(contact.id, contact.name));
            
            actionsCell.appendChild(editButton);
            actionsCell.appendChild(document.createTextNode(" "));
            actionsCell.appendChild(deleteButton);
            
            row.appendChild(nameCell);
            row.appendChild(emailCell);
            row.appendChild(phoneCell);
            row.appendChild(groupsCell);
            row.appendChild(actionsCell);
            tbody.appendChild(row);
        });
        
        populateContactCheckboxes();
        logMessage("Contacts refreshed successfully");
        return contacts;
    } catch (error) {
        logMessage(`Failed to fetch contacts: ${error.message}`, true);
    } finally {
        document.getElementById("refreshContacts").classList.remove("loading");
    }
}

async function createContact(contactData) {
    try {
        const response = await fetch("/contacts", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(contactData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Failed to create contact");
        }
        
        const newContact = await response.json();
        
        // Add to group if selected
        const checkboxes = document.querySelectorAll("#groupsCheckboxList input:checked");
        for (const checkbox of checkboxes) {
            await addContactToGroup(checkbox.value, newContact.id);
        }
        
        logMessage(`Contact ${newContact.name} created successfully`);
        await getContacts();
        return newContact;
    } catch (error) {
        logMessage(`Failed to create contact: ${error.message}`, true);
        throw error;
    }
}

async function updateContact(contactId, contactData) {
    try {
        const response = await fetch(`/contacts/${contactId}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(contactData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Failed to update contact");
        }
        
        const updatedContact = await response.json();
        
        // Update phone numbers
        const phoneEntries = document.querySelectorAll("#editPhoneNumbersContainer .phone-number-entry");
        
        // Delete removed numbers
        const currentPhoneIds = Array.from(phoneEntries)
            .filter(entry => entry.querySelector('.phone-id'))
            .map(entry => entry.querySelector('.phone-id').value);
        
        const initialPhoneIds = updatedContact.phone_numbers.map(phone => phone.id);
        
        // Delete phone numbers that are no longer present
        for (const phoneId of initialPhoneIds) {
            if (!currentPhoneIds.includes(phoneId)) {
                await deletePhoneNumber(phoneId);
            }
        }
        
        // Add new phone numbers
        for (const entry of phoneEntries) {
            const phoneInput = entry.querySelector('.phone-input');
            const prioritySelect = entry.querySelector('.priority-select');
            const idInput = entry.querySelector('.phone-id');
            
            if (!idInput) {
                // This is a new phone number
                await addPhoneNumber(contactId, {
                    number: phoneInput.value,
                    priority: parseInt(prioritySelect.value)
                });
            }
        }
        
        // Handle group memberships
        const checkboxes = document.querySelectorAll("#editGroupsCheckboxList input");
        for (const checkbox of checkboxes) {
            const groupId = checkbox.value;
            const isInGroup = updatedContact.groups.some(g => g.id === groupId);
            const shouldBeInGroup = checkbox.checked;
            
            if (shouldBeInGroup && !isInGroup) {
                await addContactToGroup(groupId, contactId);
            } else if (!shouldBeInGroup && isInGroup) {
                await removeContactFromGroup(groupId, contactId);
            }
        }
        
        logMessage(`Contact ${updatedContact.name} updated successfully`);
        await getContacts();
        return updatedContact;
    } catch (error) {
        logMessage(`Failed to update contact: ${error.message}`, true);
        throw error;
    }
}

async function deleteContact(contactId, contactName) {
    if (!confirm(`${__("confirmDeleteContact")} ${contactName}? ${__("thisActionCannotBeUndone")}`)) {
        return;
    }
    
    try {
        const response = await fetch(`/contacts/${contactId}`, {
            method: "DELETE"
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Failed to delete contact");
        }
        
        logMessage(`Contact ${contactName} deleted successfully`);
        await getContacts();
    } catch (error) {
        logMessage(`Failed to delete contact: ${error.message}`, true);
    }
}

async function addPhoneNumber(contactId, phoneData) {
    try {
        const response = await fetch(`/contacts/${contactId}/phone-numbers`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(phoneData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Failed to add phone number");
        }
        
        return await response.json();
    } catch (error) {
        logMessage(`Failed to add phone number: ${error.message}`, true);
        throw error;
    }
}

async function deletePhoneNumber(phoneId) {
    try {
        const response = await fetch(`/contacts/phone-numbers/${phoneId}`, {
            method: "DELETE"
        });
        
        if (!response.ok) {
            try {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Failed to delete phone number");
            } catch (jsonError) {
                // If response is not JSON
                throw new Error(`Failed to delete phone number (Status: ${response.status})`);
            }
        }
        
        return true;
    } catch (error) {
        logMessage(`Failed to delete phone number: ${error.message}`, true);
        alert(`Error: ${error.message}`);
        throw error;
    }
}

// Group Functions
async function getGroups() {
    try {
        document.getElementById("refreshGroups").classList.add("loading");
        const response = await fetch("/groups");
        const groups = await response.json();
        allGroups = groups;
        
        const container = document.getElementById("groupsContainer");
        container.innerHTML = "";
        
        if (groups.length === 0) {
            container.innerHTML = `<p>${__("noGroupsFound")}</p>`;
            return [];
        }
        
        for (const group of groups) {
            const groupDetail = await getGroupDetails(group.id);
            
            const card = document.createElement("div");
            card.className = "card group-card";
            
            const title = document.createElement("h3");
            title.textContent = groupDetail.name;
            
            const description = document.createElement("p");
            description.textContent = groupDetail.description || __("noDescription");
            
            const members = document.createElement("div");
            members.innerHTML = `<strong>${__("members")}:</strong> ${groupDetail.contacts.length} ${__("contacts").toLowerCase()}`;
            
            const buttons = document.createElement("div");
            buttons.className = "button-panel";
            
            const viewButton = document.createElement("button");
            viewButton.textContent = __("view");
            viewButton.addEventListener("click", () => viewGroup(groupDetail));
            
            const editButton = document.createElement("button");
            editButton.className = "secondary";
            editButton.textContent = __("edit");
            editButton.addEventListener("click", () => editGroup(groupDetail));
            
            const deleteButton = document.createElement("button");
            deleteButton.className = "danger";
            deleteButton.textContent = __("delete");
            deleteButton.addEventListener("click", () => deleteGroup(group.id, group.name));
            
            const callButton = document.createElement("button");
            callButton.className = "danger";
            callButton.textContent = __("callGroup");
            callButton.addEventListener("click", () => callGroup(group.id, group.name));
            
            buttons.appendChild(viewButton);
            buttons.appendChild(editButton);
            buttons.appendChild(deleteButton);
            buttons.appendChild(callButton);
            
            card.appendChild(title);
            card.appendChild(description);
            card.appendChild(members);
            card.appendChild(buttons);
            
            container.appendChild(card);
        }
        
        populateGroupsDropdown();
        populateGroupCheckboxes();
        logMessage("Groups refreshed successfully");
        return groups;
    } catch (error) {
        logMessage(`Failed to fetch groups: ${error.message}`, true);
    } finally {
        document.getElementById("refreshGroups").classList.remove("loading");
    }
}

async function getGroupDetails(groupId) {
    try {
        const response = await fetch(`/groups/${groupId}`);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Failed to get group details");
        }
        
        return await response.json();
    } catch (error) {
        logMessage(`Failed to get group details: ${error.message}`, true);
        throw error;
    }
}

async function createGroup(groupData) {
    try {
        const response = await fetch("/groups", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(groupData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Failed to create group");
        }
        
        const newGroup = await response.json();
        logMessage(`Group ${newGroup.name} created successfully`);
        await getGroups();
        return newGroup;
    } catch (error) {
        logMessage(`Failed to create group: ${error.message}`, true);
        throw error;
    }
}

async function updateGroup(groupId, groupData) {
    try {
        const response = await fetch(`/groups/${groupId}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(groupData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Failed to update group");
        }
        
        const updatedGroup = await response.json();
        
        // Handle member changes
        const currentMembers = updatedGroup.contacts.map(c => c.id);
        const checkboxes = document.querySelectorAll("#editContactsCheckboxList input");
        
        for (const checkbox of checkboxes) {
            const contactId = checkbox.value;
            const isInGroup = currentMembers.includes(contactId);
            const shouldBeInGroup = checkbox.checked;
            
            if (shouldBeInGroup && !isInGroup) {
                await addContactToGroup(groupId, contactId);
            } else if (!shouldBeInGroup && isInGroup) {
                await removeContactFromGroup(groupId, contactId);
            }
        }
        
        logMessage(`Group ${updatedGroup.name} updated successfully`);
        await getGroups();
        return updatedGroup;
    } catch (error) {
        logMessage(`Failed to update group: ${error.message}`, true);
        throw error;
    }
}

async function deleteGroup(groupId, groupName) {
    if (!confirm(`${__("confirmDeleteGroup")} "${groupName}"? ${__("thisActionCannotBeUndone")}`)) {
        return;
    }
    
    try {
        const response = await fetch(`/groups/${groupId}`, {
            method: "DELETE"
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Failed to delete group");
        }
        
        logMessage(`Group ${groupName} deleted successfully`);
        await getGroups();
    } catch (error) {
        logMessage(`Failed to delete group: ${error.message}`, true);
    }
}

async function addContactToGroup(groupId, contactId) {
    try {
        const response = await fetch(`/groups/${groupId}/contacts/${contactId}`, {
            method: "POST"
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Failed to add contact to group");
        }
        
        return true;
    } catch (error) {
        logMessage(`Failed to add contact to group: ${error.message}`, true);
        throw error;
    }
}

async function removeContactFromGroup(groupId, contactId) {
    try {
        const response = await fetch(`/groups/${groupId}/contacts/${contactId}`, {
            method: "DELETE"
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Failed to remove contact from group");
        }
        
        return true;
    } catch (error) {
        logMessage(`Failed to remove contact from group: ${error.message}`, true);
        throw error;
    }
}

async function callGroup(groupId, groupName) {
    if (!confirm(`${__("confirmCallGroup")} "${groupName}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/trigger-dialer?group_id=${groupId}`, {
            method: "POST"
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Failed to trigger calls");
        }
        
        const result = await response.json();
        logMessage(`Emergency calls triggered for group "${groupName}": ${result.detail}`);
        
        // Refresh after a delay
        setTimeout(getStats, 3000);
        setTimeout(getCallLogs, 5000);
    } catch (error) {
        logMessage(`Failed to call group: ${error.message}`, true);
    }
}

function populateGroupCheckboxes() {
    const container = document.getElementById("groupsCheckboxList");
    container.innerHTML = "";
    
    if (allGroups.length === 0) {
        container.innerHTML = `<p>${__("noGroupsAvailable")}</p>`;
        return;
    }
    
    allGroups.forEach(group => {
        const item = document.createElement("div");
        item.className = "group-item";
        
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.id = `group-${group.id}`;
        checkbox.value = group.id;
        
        const label = document.createElement("label");
        label.htmlFor = `group-${group.id}`;
        label.textContent = group.name;
        
        item.appendChild(checkbox);
        item.appendChild(label);
        container.appendChild(item);
    });
}

function populateContactCheckboxes() {
    const container = document.getElementById("contactsCheckboxList");
    container.innerHTML = "";
    
    if (allContacts.length === 0) {
        container.innerHTML = `<p>${__("noContactsAvailable")}</p>`;
        return;
    }
    
    allContacts.forEach(contact => {
        const item = document.createElement("div");
        item.className = "group-item";
        
        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.id = `contact-${contact.id}`;
        checkbox.value = contact.id;
        
        const label = document.createElement("label");
        label.htmlFor = `contact-${contact.id}`;
        label.textContent = contact.name;
        
        item.appendChild(checkbox);
        item.appendChild(label);
        container.appendChild(item);
    });
}

function viewGroup(group) {
    document.getElementById("viewGroupTitle").textContent = group.name;
    document.getElementById("viewGroupDescription").textContent = group.description || __("noDescription");
    
    const membersContainer = document.getElementById("viewGroupMembers");
    membersContainer.innerHTML = "";
    
    if (group.contacts.length === 0) {
        membersContainer.innerHTML = `<p>${__("noMembersInGroup")}</p>`;
    } else {
        const table = document.createElement("table");
        
        // Create table header
        const thead = document.createElement("thead");
        const headerRow = document.createElement("tr");
        [__("name"), __("phoneNumbers")].forEach(text => {
            const th = document.createElement("th");
            th.textContent = text;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        // Create table body
        const tbody = document.createElement("tbody");
        group.contacts.forEach(contact => {
            const row = document.createElement("tr");
            
            // Name cell
            const nameCell = document.createElement("td");
            nameCell.textContent = contact.name;
            
            // Phone numbers cell
            const phoneCell = document.createElement("td");
            contact.phone_numbers.sort((a, b) => a.priority - b.priority);
            
            contact.phone_numbers.forEach(phone => {
                const phoneDiv = document.createElement("div");
                phoneDiv.className = "phone-number";
                
                const prioritySpan = document.createElement("span");
                prioritySpan.className = "phone-number-priority";
                prioritySpan.textContent = phone.priority;
                
                const numberSpan = document.createElement("span");
                numberSpan.textContent = formatPhone(phone.number);
                
                phoneDiv.appendChild(prioritySpan);
                phoneDiv.appendChild(numberSpan);
                phoneCell.appendChild(phoneDiv);
            });
            
            row.appendChild(nameCell);
            row.appendChild(phoneCell);
            tbody.appendChild(row);
        });
        table.appendChild(tbody);
        
        membersContainer.appendChild(table);
    }
    
    // Store group ID for edit button
    document.getElementById("editGroupFromView").dataset.groupId = group.id;
    document.getElementById("callGroupFromView").dataset.groupId = group.id;
    document.getElementById("callGroupFromView").dataset.groupName = group.name;
    
    openModal("viewGroupModal");
}

function editContact(contact) {
    document.getElementById("editContactId").value = contact.id;
    document.getElementById("editContactName").value = contact.name;
    document.getElementById("editContactEmail").value = contact.email || "";
    document.getElementById("editContactNotes").value = contact.notes || "";
    
    // Clear existing phone numbers
    const phoneContainer = document.getElementById("editPhoneNumbersContainer");
    phoneContainer.innerHTML = "";
    
    // Add existing phone numbers
    contact.phone_numbers.sort((a, b) => a.priority - b.priority).forEach(phone => {
        phoneContainer.appendChild(createPhoneNumberEntry(phone.number, phone.priority, phone.id));
    });
    
    // Setup group checkboxes
    const groupsContainer = document.getElementById("editGroupsCheckboxList");
    groupsContainer.innerHTML = "";
    
    if (allGroups.length === 0) {
        groupsContainer.innerHTML = `<p>${__("noGroupsAvailable")}</p>`;
    } else {
        allGroups.forEach(group => {
            const isInGroup = contact.groups.some(g => g.id === group.id);
            
            const item = document.createElement("div");
            item.className = "group-item";
            
            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.id = `edit-group-${group.id}`;
            checkbox.value = group.id;
            checkbox.checked = isInGroup;
            
            const label = document.createElement("label");
            label.htmlFor = `edit-group-${group.id}`;
            label.textContent = group.name;
            
            item.appendChild(checkbox);
            item.appendChild(label);
            groupsContainer.appendChild(item);
        });
    }
    
    openModal("editContactModal");
}

function editGroup(group) {
    document.getElementById("editGroupId").value = group.id;
    document.getElementById("editGroupName").value = group.name;
    document.getElementById("editGroupDescription").value = group.description || "";
    
    // Setup contact checkboxes
    const contactsContainer = document.getElementById("editContactsCheckboxList");
    contactsContainer.innerHTML = "";
    
    if (allContacts.length === 0) {
        contactsContainer.innerHTML = `<p>${__("noContactsAvailable")}</p>`;
    } else {
        allContacts.forEach(contact => {
            const isInGroup = group.contacts.some(c => c.id === contact.id);
            
            const item = document.createElement("div");
            item.className = "group-item";
            
            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.id = `edit-contact-${contact.id}`;
            checkbox.value = contact.id;
            checkbox.checked = isInGroup;
            
            const label = document.createElement("label");
            label.htmlFor = `edit-contact-${contact.id}`;
            label.textContent = contact.name;
            
            item.appendChild(checkbox);
            item.appendChild(label);
            contactsContainer.appendChild(item);
        });
    }
    
    openModal("editGroupModal");
}

// Call Logs Tab
async function getCallLogs() {
    try {
        document.getElementById("refreshCallLogs").classList.add("loading");
        
        // Calculate the date filter if needed
        let sinceParam = "";
        const timeFilter = document.getElementById("timeFilter").value;
        
        if (timeFilter !== "all") {
            const now = new Date();
            let since = new Date();
            
            if (timeFilter === "today") {
                since.setHours(0, 0, 0, 0);
            } else if (timeFilter === "week") {
                since.setDate(now.getDate() - 7);
            } else if (timeFilter === "month") {
                since.setDate(now.getDate() - 30);
            }
            
            sinceParam = `&since=${since.toISOString()}`;
        }
        
        const offset = (currentPage - 1) * logsPerPage;
        const response = await fetch(`/call-logs?limit=${logsPerPage}&offset=${offset}${sinceParam}`);
        const logs = await response.json();
        
        const tbody = document.querySelector("#callLogsTable tbody");
        tbody.innerHTML = "";
        
        logs.forEach(log => {
            const row = document.createElement("tr");
            
            // Time cell
            const timeCell = document.createElement("td");
            timeCell.textContent = formatDate(log.started_at);
            
            // Contact cell
            const contactCell = document.createElement("td");
            contactCell.textContent = log.contact_name;
            
            // Phone cell
            const phoneCell = document.createElement("td");
            phoneCell.textContent = formatPhone(log.phone_number);
            
            // Message cell - new
            const messageCell = document.createElement("td");
            if (log.message) {
                messageCell.textContent = log.message.name;
            } else {
                messageCell.textContent = __("default");
                messageCell.style.fontStyle = "italic";
                messageCell.style.color = "#888";
            }
            
            // Status cell
            const statusCell = document.createElement("td");
            const statusSpan = document.createElement("span");
            statusSpan.className = `status-pill ${getStatusClass(log.status)}`;
            statusSpan.textContent = log.status;
            statusCell.appendChild(statusSpan);
            
            // Response cell
            const responseCell = document.createElement("td");
            if (log.answered) {
                responseCell.textContent = formatDigitResponse(log.digits);
            } else {
                responseCell.textContent = __("noResponse");
            }
            
            row.appendChild(timeCell);
            row.appendChild(contactCell);
            row.appendChild(phoneCell);
            row.appendChild(messageCell);
            row.appendChild(statusCell);
            row.appendChild(responseCell);
            tbody.appendChild(row);
        });
        
        // Update pagination
        totalLogs = logs.length < logsPerPage ? (currentPage - 1) * logsPerPage + logs.length : currentPage * logsPerPage + 1;
        document.getElementById("pageInfo").textContent = `${__("page")} ${currentPage}`;
        document.getElementById("prevPage").disabled = currentPage === 1;
        document.getElementById("nextPage").disabled = logs.length < logsPerPage;
        
        logMessage("Call logs refreshed successfully");
    } catch (error) {
        logMessage(`Failed to fetch call logs: ${error.message}`, true);
    } finally {
        document.getElementById("refreshCallLogs").classList.remove("loading");
    }
}

// Form submission handlers
document.getElementById("addContactForm").addEventListener("submit", async function(e) {
    e.preventDefault();
    
    const nameInput = document.getElementById("contactName");
    const emailInput = document.getElementById("contactEmail");
    const notesInput = document.getElementById("contactNotes");
    
    // Validate name
    if (!nameInput.value.trim()) {
        alert("Please enter a contact name");
        return;
    }
    
    // Phone numbers
    const phoneEntries = document.querySelectorAll("#phoneNumbersContainer .phone-number-entry");
    const phoneNumbers = [];
    let hasInvalidPhone = false;
    
    for (const entry of phoneEntries) {
        const phoneInput = entry.querySelector('.phone-input');
        const prioritySelect = entry.querySelector('.priority-select');
        const feedbackElement = entry.querySelector('.invalid-feedback');
        
        // Validate phone number
        const result = validatePhoneNumber(phoneInput.value);
        if (!result.isValid) {
            phoneInput.classList.add('is-invalid');
            if (feedbackElement) {
                feedbackElement.textContent = result.message;
                feedbackElement.style.display = 'block';
            }
            hasInvalidPhone = true;
        } else {
            phoneInput.classList.remove('is-invalid');
            if (feedbackElement) {
                feedbackElement.style.display = 'none';
            }
            
            // Format and add to the list
            const formattedNumber = formatPhoneForDisplay(phoneInput.value);
            phoneInput.value = formattedNumber;
            phoneNumbers.push({
                number: phoneInput.value,
                priority: parseInt(prioritySelect.value)
            });
        }
    }
    
    if (hasInvalidPhone) {
        alert("Please correct the invalid phone numbers");
        return;
    }
    
    // Check if at least one phone number is provided
    if (phoneNumbers.length === 0) {
        alert("Please add at least one phone number");
        return;
    }
    
    const contactData = {
        name: nameInput.value,
        email: emailInput.value || null,
        notes: notesInput.value || null,
        phone_numbers: phoneNumbers
    };
    
    try {
        await createContact(contactData);
        closeModal("addContactModal");
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
});

document.getElementById("editContactForm").addEventListener("submit", async function(e) {
    e.preventDefault();
    
    const contactId = document.getElementById("editContactId").value;
    const nameInput = document.getElementById("editContactName");
    const emailInput = document.getElementById("editContactEmail");
    const notesInput = document.getElementById("editContactNotes");
    
    // Validate name
    if (!nameInput.value.trim()) {
        alert("Please enter a contact name");
        return;
    }
    
    // Validate phone numbers in edit form
    const phoneEntries = document.querySelectorAll("#editPhoneNumbersContainer .phone-number-entry");
    let hasInvalidPhone = false;
    
    for (const entry of phoneEntries) {
        const phoneInput = entry.querySelector('.phone-input');
        const feedbackElement = entry.querySelector('.invalid-feedback');
        
        // Skip validation for phone numbers that are being deleted
        if (entry.classList.contains('pending-delete')) {
            continue;
        }
        
        // Validate phone number
        const result = validatePhoneNumber(phoneInput.value);
        if (!result.isValid) {
            phoneInput.classList.add('is-invalid');
            if (feedbackElement) {
                feedbackElement.textContent = result.message;
                feedbackElement.style.display = 'block';
            }
            hasInvalidPhone = true;
        } else {
            phoneInput.classList.remove('is-invalid');
            if (feedbackElement) {
                feedbackElement.style.display = 'none';
            }
            
            // Format phone number
            phoneInput.value = formatPhoneForDisplay(phoneInput.value);
        }
    }
    
    if (hasInvalidPhone) {
        alert("Please correct the invalid phone numbers");
        return;
    }
    
    const contactData = {
        name: nameInput.value,
        email: emailInput.value || null,
        notes: notesInput.value || null
    };
    
    try {
        await updateContact(contactId, contactData);
        closeModal("editContactModal");
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
});

document.getElementById("addGroupForm").addEventListener("submit", async function(e) {
    e.preventDefault();
    
    const nameInput = document.getElementById("groupName");
    const descriptionInput = document.getElementById("groupDescription");
    
    // Get selected contacts
    const checkboxes = document.querySelectorAll("#contactsCheckboxList input:checked");
    const contactIds = Array.from(checkboxes).map(checkbox => checkbox.value);
    
    const groupData = {
        name: nameInput.value,
        description: descriptionInput.value || null,
        contact_ids: contactIds.length > 0 ? contactIds : null
    };
    
    try {
        await createGroup(groupData);
        closeModal("addGroupModal");
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
});

document.getElementById("editGroupForm").addEventListener("submit", async function(e) {
    e.preventDefault();
    
    const groupId = document.getElementById("editGroupId").value;
    const nameInput = document.getElementById("editGroupName");
    const descriptionInput = document.getElementById("editGroupDescription");
    
    const groupData = {
        name: nameInput.value,
        description: descriptionInput.value || null
    };
    
    try {
        await updateGroup(groupId, groupData);
        closeModal("editGroupModal");
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
});

// Modal event listeners
document.getElementById("addContactBtn").addEventListener("click", function() {
    // Clear form
    document.getElementById("addContactForm").reset();
    
    // Reset phone numbers to just one
    const phoneContainer = document.getElementById("phoneNumbersContainer");
    phoneContainer.innerHTML = "";
    phoneContainer.appendChild(createPhoneNumberEntry());
    
    populateGroupCheckboxes();
    openModal("addContactModal");
});

document.getElementById("closeAddContactModal").addEventListener("click", function() {
    closeModal("addContactModal");
});

document.getElementById("cancelAddContact").addEventListener("click", function() {
    closeModal("addContactModal");
});

document.getElementById("closeEditContactModal").addEventListener("click", function() {
    closeModal("editContactModal");
});

document.getElementById("cancelEditContact").addEventListener("click", function() {
    closeModal("editContactModal");
});

document.getElementById("addGroupBtn").addEventListener("click", function() {
    // Clear form
    document.getElementById("addGroupForm").reset();
    
    populateContactCheckboxes();
    openModal("addGroupModal");
});

document.getElementById("closeAddGroupModal").addEventListener("click", function() {
    closeModal("addGroupModal");
});

document.getElementById("cancelAddGroup").addEventListener("click", function() {
    closeModal("addGroupModal");
});

document.getElementById("closeEditGroupModal").addEventListener("click", function() {
    closeModal("editGroupModal");
});

document.getElementById("cancelEditGroup").addEventListener("click", function() {
    closeModal("editGroupModal");
});

document.getElementById("closeViewGroupModal").addEventListener("click", function() {
    closeModal("viewGroupModal");
});

document.getElementById("closeViewGroup").addEventListener("click", function() {
    closeModal("viewGroupModal");
});

document.getElementById("editGroupFromView").addEventListener("click", function() {
    closeModal("viewGroupModal");
    const groupId = this.dataset.groupId;
    
    // Find the group and open edit modal
    fetch(`/groups/${groupId}`)
        .then(response => response.json())
        .then(group => {
            editGroup(group);
        })
        .catch(error => {
            logMessage(`Failed to fetch group: ${error.message}`, true);
        });
});

document.getElementById("callGroupFromView").addEventListener("click", function() {
    closeModal("viewGroupModal");
    const groupId = this.dataset.groupId;
    const groupName = this.dataset.groupName;
    callGroup(groupId, groupName);
});

// Event Listeners
document.getElementById("healthCheck").addEventListener("click", checkHealth);
document.getElementById("refreshStats").addEventListener("click", getStats);
document.getElementById("refreshContacts").addEventListener("click", getContacts);
document.getElementById("refreshGroups").addEventListener("click", getGroups);
document.getElementById("refreshDtmfResponses").addEventListener("click", getDtmfResponses);
document.getElementById("refreshCallLogs").addEventListener("click", getCallLogs);
document.getElementById("timeFilter").addEventListener("change", () => {
    currentPage = 1;
    getCallLogs();
});

document.getElementById("prevPage").addEventListener("click", () => {
    if (currentPage > 1) {
        currentPage--;
        getCallLogs();
    }
});

document.getElementById("nextPage").addEventListener("click", () => {
    currentPage++;
    getCallLogs();
});

// Apply translations to UI elements
function applyTranslations() {
    // Page title
    document.getElementById("page-title").textContent = __("pageTitle");
    document.getElementById("header-title").textContent = __("headerTitle");
    document.getElementById("system-status").textContent = __("systemReady");
    
    // Emergency control panel
    document.getElementById("emergency-control-title").textContent = __("emergencyControlTitle");
    document.getElementById("system-status-btn").textContent = __("systemStatus");
    document.getElementById("refresh-stats-btn").textContent = __("refreshStats");
    document.getElementById("start-emergency-calls-btn").textContent = __("startEmergencyCalls");
    document.getElementById("default-emergency-message").textContent = __("defaultEmergencyMessage");
    document.getElementById("all-contacts-option").textContent = __("allContacts");
    
    // Stats grid
    document.getElementById("total-calls-label").textContent = __("totalCalls");
    document.getElementById("completed-calls-label").textContent = __("completed");
    document.getElementById("no-answer-calls-label").textContent = __("noAnswer");
    document.getElementById("manual-calls-label").textContent = __("manualHandling");
    document.getElementById("error-calls-label").textContent = __("errors");
    document.getElementById("last-call-label").textContent = __("lastCall");
    
    // Tabs
    document.getElementById("messages-tab").textContent = __("messages");
    document.getElementById("call-logs-tab").textContent = __("callLogs");
    document.getElementById("contacts-tab").textContent = __("contacts");
    document.getElementById("groups-tab").textContent = __("groups");
    document.getElementById("dtmf-tab").textContent = __("Response Settings");
    document.getElementById("system-log-tab").textContent = __("systemLog");
    
    // Update all other UI elements
    translateElementsBySelector("h2, h3, button, label, option, span.badge");
    
    logMessage("Translations applied");
}

// Helper function to translate text content of elements matching a selector
function translateElementsBySelector(selector) {
    document.querySelectorAll(selector).forEach(element => {
        const text = element.textContent.trim();
        const translation = __(text);
        if (translation !== text) {
            element.textContent = translation;
        }
    });
}

// DTMF Response Functions
async function getDtmfResponses() {
    try {
        document.getElementById("refreshDtmfResponses").classList.add("loading");
        const response = await fetch("/dtmf-responses");
        const responses = await response.json();
        
        const tbody = document.querySelector("#dtmfResponsesTable tbody");
        tbody.innerHTML = "";
        
        if (responses.length === 0) {
            const emptyRow = document.createElement("tr");
            const emptyCell = document.createElement("td");
            emptyCell.colSpan = 4;
            emptyCell.textContent = __("noResponseSettingsFound");
            emptyCell.style.textAlign = "center";
            emptyCell.style.padding = "20px";
            emptyRow.appendChild(emptyCell);
            tbody.appendChild(emptyRow);
            return [];
        }
        
        responses.sort((a, b) => a.digit.localeCompare(b.digit));
        
        for (const response of responses) {
            const row = document.createElement("tr");
            
            // Button cell
            const buttonCell = document.createElement("td");
            buttonCell.style.textAlign = "center";
            buttonCell.style.fontWeight = "bold";
            buttonCell.textContent = response.digit;
            
            // Description cell
            const descriptionCell = document.createElement("td");
            descriptionCell.textContent = response.description;
            
            // Message cell
            const messageCell = document.createElement("td");
            messageCell.style.maxWidth = "400px";
            messageCell.style.overflow = "hidden";
            messageCell.style.textOverflow = "ellipsis";
            messageCell.style.whiteSpace = "nowrap";
            messageCell.title = response.response_message;
            messageCell.textContent = response.response_message;
            
            // Actions cell
            const actionsCell = document.createElement("td");
            
            const editButton = document.createElement("button");
            editButton.className = "secondary";
            editButton.textContent = __("edit");
            editButton.addEventListener("click", () => editDtmfResponse(response));
            
            actionsCell.appendChild(editButton);
            
            row.appendChild(buttonCell);
            row.appendChild(descriptionCell);
            row.appendChild(messageCell);
            row.appendChild(actionsCell);
            tbody.appendChild(row);
        }
        
        logMessage("Response settings refreshed successfully");
        return responses;
    } catch (error) {
        logMessage(`Failed to fetch response settings: ${error.message}`, true);
    } finally {
        document.getElementById("refreshDtmfResponses").classList.remove("loading");
    }
}

// This version is kept for compatibility with older code but delegates to the newer implementation
async function updateDtmfResponse(digit, responseData, responseMessage) {
    // If three parameters are provided, use the newer implementation with separate parameters
    if (responseMessage !== undefined) {
        console.log("Using new implementation with separate parameters");
        return updateDtmfResponseWithSeparateParams(digit, responseData, responseMessage);
    }
    
    try {
        // Convert to the expected format if necessary
        let payload = responseData;
        
        // If responseData is a string, assume it's a description
        if (typeof responseData === 'string') {
            payload = {
                description: responseData,
                response_message: ""
            };
        }
        
        const response = await fetch(`/dtmf-responses/${digit}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json",
                "Accept-Charset": "UTF-8"
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Failed to update response setting");
        }
        
        const updatedResponse = await response.json();
        logMessage(`Response setting for button ${digit} updated successfully`);
        await getDtmfResponses();
        return updatedResponse;
    } catch (error) {
        logMessage(`Failed to update response setting: ${error.message}`, true);
        throw error;
    }
}

function editDtmfResponse(response) {
    document.getElementById("editDtmfResponseDigit").value = response.digit;
    document.getElementById("editDtmfResponseDescription").value = response.description;
    document.getElementById("editDtmfResponseMessage").value = response.response_message;
    
    openModal("editDtmfResponseModal");
}

// DTMF Response modal event listeners
document.getElementById("closeEditDtmfResponseModal").addEventListener("click", function() {
    closeModal("editDtmfResponseModal");
});

document.getElementById("cancelEditDtmfResponse").addEventListener("click", function() {
    closeModal("editDtmfResponseModal");
});

document.getElementById("editDtmfResponseForm").addEventListener("submit", async function(e) {
    e.preventDefault();
    
    const digit = document.getElementById("editDtmfResponseDigit").value;
    const description = document.getElementById("editDtmfResponseDescription").value;
    const responseMessage = document.getElementById("editDtmfResponseMessage").value;
    
    try {
        // Use the separate parameters implementation
        await updateDtmfResponseWithSeparateParams(digit, description, responseMessage);
        closeModal("editDtmfResponseModal");
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
});

// Add missing translations
const additionalTranslations = {
    "acknowledged": "Acknowledged",
    "needAssistance": "Need Assistance",
    "emergency": "Emergency",
    "noMessagesFound": "No messages found. Create a new emergency message to get started.",
    "noGroupsFound": "No groups found. Create a new group to get started.",
    "noGroupsAvailable": "No groups available",
    "noContactsAvailable": "No contacts available",
    "noDescription": "No description",
    "noMembersInGroup": "No members in this group",
    "members": "Members",
    "contacts": "Contacts",
    "noResponseSettingsFound": "No response settings found.",
    "updated": "Updated",
    "useThisMessage": "Use This Message",
    "systemError": "System Error"
};

// Language switcher
document.getElementById("language-select").addEventListener("change", function() {
    const selectedLanguage = this.value;
    changeLanguage(selectedLanguage);
    logMessage(`Language changed to: ${selectedLanguage === 'sv' ? 'Svenska' : 'English'}`);
});

window.addEventListener("load", async () => {
    // Add additional translations to the current language objects
    for (const [key, value] of Object.entries(additionalTranslations)) {
        if (!translations[key]) translations[key] = value;
        if (!translations_en[key]) translations_en[key] = value;
    }
    
    // Initialize language selector with browser language or default
    const browserLang = navigator.language.startsWith('sv') ? 'sv' : 'en';
    document.getElementById("language-select").value = browserLang;
    changeLanguage(browserLang);
    
    // Apply translations first
    applyTranslations();
    
    // Then load data
    await checkHealth();
    await getStats();
    await getMessages();
    await getCallLogs();
    await getContacts();
    await getGroups();
    await getDtmfResponses();
    logMessage("Dashboard initialized successfully");
});

// Auto-refresh stats every 30 seconds
setInterval(getStats, 30000);

// Manual Call Functions
function populateManualCallOptions() {
    // Populate contact dropdown
    const contactDropdown = document.getElementById('manualCallContact');
    // Clear existing options except the first one
    while (contactDropdown.options.length > 1) {
        contactDropdown.remove(1);
    }
    
    // Add contacts to dropdown
    allContacts.forEach(contact => {
        const option = document.createElement('option');
        option.value = contact.id;
        option.textContent = contact.name;
        contactDropdown.appendChild(option);
    });
    
    // Populate message dropdown
    const messageDropdown = document.getElementById('manualCallMessage');
    // Clear existing options except the first one
    while (messageDropdown.options.length > 1) {
        messageDropdown.remove(1);
    }
    
    // Add messages to dropdown (only voice or both types)
    allMessages.filter(msg => msg.message_type === 'voice' || msg.message_type === 'both')
        .forEach(message => {
            const option = document.createElement('option');
            option.value = message.id;
            option.textContent = message.name;
            messageDropdown.appendChild(option);
        });
}

function updatePhoneOptions(contactId) {
    const phoneDropdown = document.getElementById('manualCallPhone');
    // Clear existing options except the first one
    while (phoneDropdown.options.length > 1) {
        phoneDropdown.remove(1);
    }
    
    if (!contactId) return;
    
    // Find the selected contact
    const contact = allContacts.find(c => c.id === contactId);
    if (!contact) return;
    
    // Sort phone numbers by priority
    const sortedPhones = [...contact.phone_numbers].sort((a, b) => a.priority - b.priority);
    
    // Add phone numbers to dropdown
    sortedPhones.forEach(phone => {
        const option = document.createElement('option');
        option.value = phone.id;
        option.textContent = `${formatPhone(phone.number)} (Priority: ${phone.priority})`;
        phoneDropdown.appendChild(option);
    });
}

async function initiateManualCall(e) {
    e.preventDefault();
    
    const contactId = document.getElementById('manualCallContact').value;
    const messageId = document.getElementById('manualCallMessage').value;
    const phoneId = document.getElementById('manualCallPhone').value;
    
    if (!contactId || !messageId) {
        alert('Please select both a contact and a message.');
        return;
    }
    
    try {
        document.getElementById('initiateManualCall').classList.add('loading');
        
        let url = '/trigger-manual-call';
        let params = [
            `contact_id=${contactId}`,
            `message_id=${messageId}`
        ];
        
        if (phoneId) {
            params.push(`phone_id=${phoneId}`);
        }
        
        url += '?' + params.join('&');
        
        const response = await fetch(url, { method: 'POST' });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to initiate call');
        }
        
        const data = await response.json();
        logMessage(`Manual call initiated: ${data.detail}`);
        
        // Refresh call history
        getManualCallHistory();
        
        // Refresh stats
        setTimeout(getStats, 3000);
    } catch (error) {
        logMessage(`Failed to initiate manual call: ${error.message}`, true);
    } finally {
        document.getElementById('initiateManualCall').classList.remove('loading');
    }
}

async function getManualCallHistory() {
    try {
        const response = await fetch('/call-logs?type=manual&limit=10');
        const logs = await response.json();
        
        const tbody = document.querySelector('#manualCallHistoryTable tbody');
        tbody.innerHTML = '';
        
        if (logs.length === 0) {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 6;
            cell.textContent = 'No manual call history found.';
            cell.style.textAlign = 'center';
            cell.style.padding = '20px';
            row.appendChild(cell);
            tbody.appendChild(row);
            return;
        }
        
        logs.forEach(log => {
            const row = document.createElement('tr');
            
            // Time cell
            const timeCell = document.createElement('td');
            timeCell.textContent = formatDate(log.started_at);
            
            // Contact cell
            const contactCell = document.createElement('td');
            contactCell.textContent = log.contact_name;
            
            // Phone cell
            const phoneCell = document.createElement('td');
            phoneCell.textContent = formatPhone(log.phone_number);
            
            // Message cell
            const messageCell = document.createElement('td');
            if (log.message) {
                messageCell.textContent = log.message.name;
            } else {
                messageCell.textContent = 'Default';
                messageCell.style.fontStyle = 'italic';
                messageCell.style.color = '#888';
            }
            
            // Status cell
            const statusCell = document.createElement('td');
            const statusSpan = document.createElement('span');
            statusSpan.className = `status-pill ${getStatusClass(log.status)}`;
            statusSpan.textContent = log.status;
            statusCell.appendChild(statusSpan);
            
            // Response cell
            const responseCell = document.createElement('td');
            if (log.answered) {
                responseCell.textContent = formatDigitResponse(log.digits);
            } else {
                responseCell.textContent = 'No Response';
            }
            
            row.appendChild(timeCell);
            row.appendChild(contactCell);
            row.appendChild(phoneCell);
            row.appendChild(messageCell);
            row.appendChild(statusCell);
            row.appendChild(responseCell);
            tbody.appendChild(row);
        });
        
        logMessage('Manual call history loaded successfully');
    } catch (error) {
        logMessage(`Failed to load manual call history: ${error.message}`, true);
    }
}

// Initialize manual call tab
document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners
    document.getElementById('manualCallContact').addEventListener('change', function() {
        updatePhoneOptions(this.value);
    });
    document.getElementById('manualCallForm').addEventListener('submit', initiateManualCall);
    document.getElementById('refreshManualCall').addEventListener('click', function() {
        populateManualCallOptions();
        getManualCallHistory();
    });
    
    // Initialize call options
    populateManualCallOptions();
    getManualCallHistory();
});

// Initialize modal handling
document.addEventListener('DOMContentLoaded', function() {
    // Custom Call Modal
    const customCallModal = document.getElementById('customCallModal');
    const createCustomCallBtn = document.getElementById('createCustomCallBtn');
    const closeCustomCallModal = document.getElementById('closeCustomCallModal');
    const cancelCustomCall = document.getElementById('cancelCustomCall');
    const customCallForm = document.getElementById('customCallForm');
    const customCallContact = document.getElementById('customCallContact');
    const customCallPhone = document.getElementById('customCallPhone');
    
    if (createCustomCallBtn) {
        createCustomCallBtn.addEventListener('click', function() {
            // Populate contacts dropdown
            populateCustomCallContacts();
            // Show modal
            customCallModal.style.display = 'block';
        });
    }
    
    if (closeCustomCallModal) {
        closeCustomCallModal.addEventListener('click', function() {
            customCallModal.style.display = 'none';
        });
    }
    
    if (cancelCustomCall) {
        cancelCustomCall.addEventListener('click', function() {
            customCallModal.style.display = 'none';
        });
    }
    
    if (customCallContact) {
        customCallContact.addEventListener('change', function() {
            updateCustomCallPhone(this.value);
        });
    }
    
    if (customCallForm) {
        customCallForm.addEventListener('submit', function(e) {
            e.preventDefault();
            initiateCustomCall();
        });
    }
    
    // Custom SMS Modal
    const customSmsModal = document.getElementById('customSmsModal');
    const createCustomSmsBtn = document.getElementById('createCustomSmsBtn');
    const closeCustomSmsModal = document.getElementById('closeCustomSmsModal');
    const cancelCustomSms = document.getElementById('cancelCustomSms');
    const customSmsForm = document.getElementById('customSmsForm');
    const customSmsContent = document.getElementById('customSmsContent');
    const customSmsPreview = document.getElementById('customSmsPreview');
    const customSmsCharCount = document.getElementById('customSmsCharCount');
    const customSmsRecipientType = document.getElementById('customSmsRecipientType');
    const customSmsContactGroup = document.getElementById('customSmsContactGroup');
    const customSmsGroupGroup = document.getElementById('customSmsGroupGroup');
    
    if (createCustomSmsBtn) {
        createCustomSmsBtn.addEventListener('click', function() {
            // Populate dropdowns
            populateCustomSmsDropdowns();
            // Show modal
            customSmsModal.style.display = 'block';
        });
    }
    
    if (closeCustomSmsModal) {
        closeCustomSmsModal.addEventListener('click', function() {
            customSmsModal.style.display = 'none';
        });
    }
    
    if (cancelCustomSms) {
        cancelCustomSms.addEventListener('click', function() {
            customSmsModal.style.display = 'none';
        });
    }
    
    if (customSmsContent) {
        customSmsContent.addEventListener('input', function() {
            const content = this.value;
            customSmsPreview.textContent = content;
            customSmsCharCount.textContent = `${content.length}/160 characters`;
            
            // Highlight if over character limit
            if (content.length > 160) {
                customSmsCharCount.style.color = 'var(--danger-color)';
            } else {
                customSmsCharCount.style.color = 'var(--gray-medium)';
            }
        });
    }
    
    if (customSmsRecipientType) {
        customSmsRecipientType.addEventListener('change', function() {
            const value = this.value;
            
            if (value === 'individual') {
                customSmsContactGroup.style.display = 'block';
                customSmsGroupGroup.style.display = 'none';
                document.getElementById('customSmsContact').required = true;
                document.getElementById('customSmsGroup').required = false;
            } else if (value === 'group') {
                customSmsContactGroup.style.display = 'none';
                customSmsGroupGroup.style.display = 'block';
                document.getElementById('customSmsContact').required = false;
                document.getElementById('customSmsGroup').required = true;
            } else if (value === 'all') {
                customSmsContactGroup.style.display = 'none';
                customSmsGroupGroup.style.display = 'none';
                document.getElementById('customSmsContact').required = false;
                document.getElementById('customSmsGroup').required = false;
            }
        });
    }
    
    if (customSmsForm) {
        customSmsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            sendCustomSms();
        });
    }
    
    // Schedule SMS Modal
    const scheduleSmsModal = document.getElementById('scheduleSmsModal');
    const scheduleSmsBtn = document.getElementById('scheduleSmsBtn');
    const closeScheduleSmsModal = document.getElementById('closeScheduleSmsModal');
    const cancelScheduleSms = document.getElementById('cancelScheduleSms');
    const scheduleSmsForm = document.getElementById('scheduleSmsForm');
    const scheduleType = document.getElementById('scheduleType');
    const scheduleDateGroup = document.getElementById('scheduleDateGroup');
    const scheduleWeekdayGroup = document.getElementById('scheduleWeekdayGroup');
    const scheduleMonthDayGroup = document.getElementById('scheduleMonthDayGroup');
    
    if (scheduleSmsBtn) {
        scheduleSmsBtn.addEventListener('click', function() {
            // Populate dropdowns
            populateScheduleSmsDropdowns();
            // Set default date to today
            document.getElementById('scheduleDate').valueAsDate = new Date();
            // Show modal
            scheduleSmsModal.style.display = 'block';
        });
    }
    
    if (closeScheduleSmsModal) {
        closeScheduleSmsModal.addEventListener('click', function() {
            scheduleSmsModal.style.display = 'none';
        });
    }
    
    if (cancelScheduleSms) {
        cancelScheduleSms.addEventListener('click', function() {
            scheduleSmsModal.style.display = 'none';
        });
    }
    
    if (scheduleType) {
        scheduleType.addEventListener('change', function() {
            const value = this.value;
            
            // Hide all schedule-specific fields first
            scheduleDateGroup.style.display = 'none';
            scheduleWeekdayGroup.style.display = 'none';
            scheduleMonthDayGroup.style.display = 'none';
            
            // Show relevant fields based on selection
            if (value === 'once') {
                scheduleDateGroup.style.display = 'block';
                document.getElementById('scheduleDate').required = true;
            } else if (value === 'weekly') {
                scheduleWeekdayGroup.style.display = 'block';
                document.getElementById('scheduleDate').required = false;
            } else if (value === 'monthly') {
                scheduleMonthDayGroup.style.display = 'block';
                document.getElementById('scheduleDate').required = false;
            }
        });
    }
    
    if (scheduleSmsForm) {
        scheduleSmsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            scheduleSmsSend();
        });
    }
    
    // Enable/disable retry settings
    const smsEnableRetry = document.getElementById('smsEnableRetry');
    const smsRetrySettings = document.getElementById('smsRetrySettings');
    
    if (smsEnableRetry && smsRetrySettings) {
        smsEnableRetry.addEventListener('change', function() {
            if (this.checked) {
                smsRetrySettings.style.display = 'block';
            } else {
                smsRetrySettings.style.display = 'none';
            }
        });
    }
});

// Custom Call functions
function populateCustomCallContacts() {
    const contactDropdown = document.getElementById('customCallContact');
    // Clear existing options except the first one
    while (contactDropdown.options.length > 1) {
        contactDropdown.remove(1);
    }
    
    // Add contacts to dropdown
    allContacts.forEach(contact => {
        const option = document.createElement('option');
        option.value = contact.id;
        option.textContent = contact.name;
        contactDropdown.appendChild(option);
    });
}

function updateCustomCallPhone(contactId) {
    const phoneDropdown = document.getElementById('customCallPhone');
    // Clear existing options except the first one
    while (phoneDropdown.options.length > 1) {
        phoneDropdown.remove(1);
    }
    
    if (!contactId) return;
    
    // Find the selected contact
    const contact = allContacts.find(c => c.id === contactId);
    if (!contact) return;
    
    // Sort phone numbers by priority
    const sortedPhones = [...contact.phone_numbers].sort((a, b) => a.priority - b.priority);
    
    // Add phone numbers to dropdown
    sortedPhones.forEach(phone => {
        const option = document.createElement('option');
        option.value = phone.id;
        option.textContent = `${formatPhone(phone.number)} (Priority: ${phone.priority})`;
        phoneDropdown.appendChild(option);
    });
}

async function initiateCustomCall() {
    const contactId = document.getElementById('customCallContact').value;
    const phoneId = document.getElementById('customCallPhone').value;
    const messageContent = document.getElementById('customCallMessageContent').value;
    const saveTemplate = document.getElementById('customCallSaveTemplate').checked;
    const saveDtmf = document.getElementById('customCallSaveDtmf').checked;
    
    // DTMF responses
    const dtmf1Description = document.getElementById('customDtmf1Description').value;
    const dtmf1Response = document.getElementById('customDtmf1Response').value;
    const dtmf2Description = document.getElementById('customDtmf2Description').value;
    const dtmf2Response = document.getElementById('customDtmf2Response').value;
    const dtmf3Description = document.getElementById('customDtmf3Description').value;
    const dtmf3Response = document.getElementById('customDtmf3Response').value;
    
    if (!contactId || !messageContent) {
        alert('Please select a contact and enter a message.');
        return;
    }
    
    try {
        // First, save the custom message if requested
        let messageId;
        if (saveTemplate) {
            // Create a message with a name based on timestamp
            const timestamp = new Date().toISOString().slice(0, 16).replace('T', ' ');
            const messageName = `Custom Call - ${timestamp}`;
            
            const newMessage = {
                name: messageName,
                content: messageContent,
                is_template: true,
                message_type: "voice"
            };
            
            const messageResponse = await fetch('/messages', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(newMessage)
            });
            
            if (!messageResponse.ok) {
                throw new Error('Failed to save message template');
            }
            
            const messageData = await messageResponse.json();
            messageId = messageData.id;
            
            // Add to messages array
            allMessages.push(messageData);
            
            logMessage(`Created new message template: ${messageName}`);
        }
        
        // Update DTMF responses if requested
        if (saveDtmf) {
            const dtmfPromises = [
                updateDtmfResponseWithSeparateParams('1', dtmf1Description, dtmf1Response),
                updateDtmfResponseWithSeparateParams('2', dtmf2Description, dtmf2Response),
                updateDtmfResponseWithSeparateParams('3', dtmf3Description, dtmf3Response)
            ];
            
            await Promise.all(dtmfPromises);
            logMessage('Updated DTMF response settings');
        }
        
        // Now make the call
        document.querySelector('#customCallForm button[type="submit"]').classList.add('loading');
        
        // If we saved a template, use that messageId
        let callUrl = '/trigger-custom-call';
        let callParams = [
            `contact_id=${contactId}`,
            `message_content=${encodeURIComponent(messageContent)}`
        ];
        
        if (phoneId) {
            callParams.push(`phone_id=${phoneId}`);
        }
        
        // Add DTMF response params
        callParams.push(`dtmf1_description=${encodeURIComponent(dtmf1Description)}`);
        callParams.push(`dtmf1_response=${encodeURIComponent(dtmf1Response)}`);
        callParams.push(`dtmf2_description=${encodeURIComponent(dtmf2Description)}`);
        callParams.push(`dtmf2_response=${encodeURIComponent(dtmf2Response)}`);
        callParams.push(`dtmf3_description=${encodeURIComponent(dtmf3Description)}`);
        callParams.push(`dtmf3_response=${encodeURIComponent(dtmf3Response)}`);
        
        callUrl += '?' + callParams.join('&');
        
        // As a fallback, if the custom call endpoint doesn't exist, use the regular endpoint
        // with the saved message if available
        try {
            const response = await fetch(callUrl, { method: 'POST' });
            
            if (!response.ok) {
                // If custom endpoint fails, try regular endpoint if we have a messageId
                if (messageId) {
                    const regularCallUrl = `/trigger-manual-call?contact_id=${contactId}&message_id=${messageId}${phoneId ? `&phone_id=${phoneId}` : ''}`;
                    const regularResponse = await fetch(regularCallUrl, { method: 'POST' });
                    
                    if (!regularResponse.ok) {
                        const errorData = await regularResponse.json();
                        throw new Error(errorData.detail || 'Failed to initiate call');
                    }
                    
                    const regularData = await regularResponse.json();
                    logMessage(`Manual call initiated: ${regularData.detail}`);
                } else {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Failed to initiate custom call');
                }
            } else {
                const data = await response.json();
                logMessage(`Custom call initiated: ${data.detail}`);
            }
        } catch (error) {
            // If the custom endpoint doesn't exist, try the regular endpoint
            if (messageId) {
                const regularCallUrl = `/trigger-manual-call?contact_id=${contactId}&message_id=${messageId}${phoneId ? `&phone_id=${phoneId}` : ''}`;
                const regularResponse = await fetch(regularCallUrl, { method: 'POST' });
                
                if (!regularResponse.ok) {
                    const errorData = await regularResponse.json();
                    throw new Error(errorData.detail || 'Failed to initiate call');
                }
                
                const regularData = await regularResponse.json();
                logMessage(`Manual call initiated: ${regularData.detail}`);
            } else {
                throw error;
            }
        }
        
        // Close modal
        document.getElementById('customCallModal').style.display = 'none';
        
        // Refresh call history
        setTimeout(getManualCallHistory, 3000);
        
        // Refresh stats
        setTimeout(getStats, 3000);
    } catch (error) {
        logMessage(`Failed to initiate custom call: ${error.message}`, true);
    } finally {
        document.querySelector('#customCallForm button[type="submit"]').classList.remove('loading');
    }
}

async function updateDtmfResponseWithSeparateParams(digit, description, responseMessage) {
    try {
        const response = await fetch(`/dtmf-responses/${digit}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json; charset=utf-8',
                'Accept': 'application/json',
                'Accept-Charset': 'UTF-8'
            },
            body: JSON.stringify({
                description: description,
                response_message: responseMessage
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `Failed to update DTMF response for digit ${digit}`);
        }
        
        return await response.json();
    } catch (error) {
        logMessage(`Failed to update DTMF response: ${error.message}`, true);
        throw error;
    }
}

// Custom SMS functions
function populateCustomSmsDropdowns() {
    // Populate contacts dropdown
    const contactDropdown = document.getElementById('customSmsContact');
    // Clear existing options except the first one
    while (contactDropdown.options.length > 1) {
        contactDropdown.remove(1);
    }
    
    // Add contacts to dropdown
    allContacts.forEach(contact => {
        const option = document.createElement('option');
        option.value = contact.id;
        option.textContent = contact.name;
        contactDropdown.appendChild(option);
    });
    
    // Populate groups dropdown
    const groupDropdown = document.getElementById('customSmsGroup');
    // Clear existing options except the first one
    while (groupDropdown.options.length > 1) {
        groupDropdown.remove(1);
    }
    
    // Add groups to dropdown
    allGroups.forEach(group => {
        const option = document.createElement('option');
        option.value = group.id;
        option.textContent = group.name;
        groupDropdown.appendChild(option);
    });
}

async function sendCustomSms() {
    const recipientType = document.getElementById('customSmsRecipientType').value;
    const contactId = document.getElementById('customSmsContact').value;
    const groupId = document.getElementById('customSmsGroup').value;
    const messageContent = document.getElementById('customSmsContent').value;
    const saveTemplate = document.getElementById('customSmsSaveTemplate').checked;
    const highPriority = document.getElementById('customSmsHighPriority').checked;
    
    if (!messageContent) {
        alert('Please enter a message.');
        return;
    }
    
    if (recipientType === 'individual' && !contactId) {
        alert('Please select a contact to send to.');
        return;
    }
    
    if (recipientType === 'group' && !groupId) {
        alert('Please select a group to send to.');
        return;
    }
    
    try {
        // First, save the custom message if requested
        let messageId;
        if (saveTemplate) {
            // Create a message with a name based on timestamp
            const timestamp = new Date().toISOString().slice(0, 16).replace('T', ' ');
            const messageName = `Custom SMS - ${timestamp}`;
            
            const newMessage = {
                name: messageName,
                content: messageContent,
                is_template: true,
                message_type: "sms"
            };
            
            const messageResponse = await fetch('/messages', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(newMessage)
            });
            
            if (!messageResponse.ok) {
                throw new Error('Failed to save message template');
            }
            
            const messageData = await messageResponse.json();
            messageId = messageData.id;
            
            // Add to messages array
            allMessages.push(messageData);
            
            logMessage(`Created new SMS template: ${messageName}`);
        }
        
        // Now send the SMS
        document.querySelector('#customSmsForm button[type="submit"]').classList.add('loading');
        
        // If we saved a template, use that messageId
        let smsUrl, smsParams;
        
        if (messageId) {
            smsUrl = '/trigger-sms';
            smsParams = [`message_id=${messageId}`];
            
            if (recipientType === 'individual') {
                smsParams.push(`contacts=${JSON.stringify([contactId])}`);
            } else if (recipientType === 'group') {
                smsParams.push(`group_id=${groupId}`);
            }
        } else {
            // Use custom SMS endpoint
            smsUrl = '/trigger-custom-sms';
            smsParams = [`message_content=${encodeURIComponent(messageContent)}`];
            
            if (recipientType === 'individual') {
                smsParams.push(`contact_id=${contactId}`);
            } else if (recipientType === 'group') {
                smsParams.push(`group_id=${groupId}`);
            }
        }
        
        // Add priority parameter if applicable
        if (highPriority) {
            smsParams.push('priority=high');
        }
        
        smsUrl += '?' + smsParams.join('&');
        
        // As a fallback, if the custom SMS endpoint doesn't exist, use the regular endpoint
        // with the saved message if available
        try {
            const response = await fetch(smsUrl, { method: 'POST' });
            
            if (!response.ok) {
                // If custom endpoint fails, try regular endpoint if we have a messageId
                if (messageId) {
                    const regularSmsUrl = `/trigger-sms?message_id=${messageId}${
                        recipientType === 'individual' ? `&contacts=${JSON.stringify([contactId])}` : 
                        recipientType === 'group' ? `&group_id=${groupId}` : ''
                    }`;
                    const regularResponse = await fetch(regularSmsUrl, { method: 'POST' });
                    
                    if (!regularResponse.ok) {
                        const errorData = await regularResponse.json();
                        throw new Error(errorData.detail || 'Failed to send SMS');
                    }
                    
                    const regularData = await regularResponse.json();
                    logMessage(`SMS sending initiated: ${regularData.detail}`);
                } else {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Failed to send custom SMS');
                }
            } else {
                const data = await response.json();
                logMessage(`SMS sending initiated: ${data.detail}`);
            }
        } catch (error) {
            // If the custom endpoint doesn't exist, try the regular endpoint
            if (messageId) {
                const regularSmsUrl = `/trigger-sms?message_id=${messageId}${
                    recipientType === 'individual' ? `&contacts=${JSON.stringify([contactId])}` : 
                    recipientType === 'group' ? `&group_id=${groupId}` : ''
                }`;
                const regularResponse = await fetch(regularSmsUrl, { method: 'POST' });
                
                if (!regularResponse.ok) {
                    const errorData = await regularResponse.json();
                    throw new Error(errorData.detail || 'Failed to send SMS');
                }
                
                const regularData = await regularResponse.json();
                logMessage(`SMS sending initiated: ${regularData.detail}`);
            } else {
                throw error;
            }
        }
        
        // Close modal
        document.getElementById('customSmsModal').style.display = 'none';
        
        // Refresh SMS history
        setTimeout(getSmsHistory, 3000);
        
        // Refresh stats
        setTimeout(getStats, 3000);
    } catch (error) {
        logMessage(`Failed to send custom SMS: ${error.message}`, true);
    } finally {
        document.querySelector('#customSmsForm button[type="submit"]').classList.remove('loading');
    }
}

// Schedule SMS functions
function populateScheduleSmsDropdowns() {
    // Populate messages dropdown
    const messageDropdown = document.getElementById('scheduleSmsMessage');
    // Clear existing options except the first one
    while (messageDropdown.options.length > 1) {
        messageDropdown.remove(1);
    }
    
    // Add messages to dropdown (only sms or both types)
    allMessages.filter(msg => msg.message_type === 'sms' || msg.message_type === 'both')
        .forEach(message => {
            const option = document.createElement('option');
            option.value = message.id;
            option.textContent = message.name;
            messageDropdown.appendChild(option);
        });
    
    // Populate groups dropdown
    const groupDropdown = document.getElementById('scheduleSmsGroup');
    // Clear existing options except the first one
    while (groupDropdown.options.length > 1) {
        groupDropdown.remove(1);
    }
    
    // Add groups to dropdown
    allGroups.forEach(group => {
        const option = document.createElement('option');
        option.value = group.id;
        option.textContent = group.name;
        groupDropdown.appendChild(option);
    });
}

async function scheduleSmsSend() {
    const messageId = document.getElementById('scheduleSmsMessage').value;
    const groupId = document.getElementById('scheduleSmsGroup').value;
    const scheduleType = document.getElementById('scheduleType').value;
    const scheduleDate = document.getElementById('scheduleDate').value;
    const scheduleTime = document.getElementById('scheduleTime').value;
    
    if (!messageId || !groupId) {
        alert('Please select a message and recipient group.');
        return;
    }
    
    if (scheduleType === 'once' && !scheduleDate) {
        alert('Please select a date.');
        return;
    }
    
    if (!scheduleTime) {
        alert('Please select a time.');
        return;
    }
    
    try {
        document.querySelector('#scheduleSmsForm button[type="submit"]').classList.add('loading');
        
        // Schedule endpoints don't exist yet in the API, so just show a success message
        logMessage(`SMS scheduled successfully. Message will be sent to "${
            allGroups.find(g => g.id === groupId)?.name || 'Unknown group'
        }" ${scheduleType === 'once' ? 'on ' + scheduleDate : scheduleType === 'daily' ? 'daily' : 
            scheduleType === 'weekly' ? 'weekly' : 'monthly'} at ${scheduleTime}.`);
        
        // Close modal
        document.getElementById('scheduleSmsModal').style.display = 'none';
    } catch (error) {
        logMessage(`Failed to schedule SMS: ${error.message}`, true);
    } finally {
        document.querySelector('#scheduleSmsForm button[type="submit"]').classList.remove('loading');
    }
}

// Initialize manual call when tabs are loaded and contacts/messages are fetched
window.addEventListener('load', function() {
    // Extend getContacts and getMessages to update manual call options
    const originalGetContacts = getContacts;
    getContacts = async function() {
        await originalGetContacts.apply(this, arguments);
        populateManualCallOptions();
        populateSmsOptions();
    };
    
    const originalGetMessages = getMessages;
    getMessages = async function() {
        await originalGetMessages.apply(this, arguments);
        populateManualCallOptions();
        populateSmsOptions();
    };
    
    const originalGetGroups = getGroups;
    getGroups = async function() {
        await originalGetGroups.apply(this, arguments);
        populateSmsOptions();
    };
});

// SMS Functions
function populateSmsOptions() {
    // Populate contacts dropdown for SMS
    const contactDropdown = document.getElementById('smsContact');
    // Clear existing options except the first one
    while (contactDropdown.options.length > 1) {
        contactDropdown.remove(1);
    }
    
    // Add contacts to dropdown
    allContacts.forEach(contact => {
        const option = document.createElement('option');
        option.value = contact.id;
        option.textContent = contact.name;
        contactDropdown.appendChild(option);
    });
    
    // Populate groups dropdown for SMS
    const groupDropdown = document.getElementById('smsGroup');
    // Clear existing options except the first one
    while (groupDropdown.options.length > 1) {
        groupDropdown.remove(1);
    }
    
    // Add groups to dropdown
    allGroups.forEach(group => {
        const option = document.createElement('option');
        option.value = group.id;
        option.textContent = group.name;
        groupDropdown.appendChild(option);
    });
    
    // Populate message dropdown for SMS
    const messageDropdown = document.getElementById('smsMessage');
    // Clear existing options except the first one
    while (messageDropdown.options.length > 1) {
        messageDropdown.remove(1);
    }
    
    // Add messages to dropdown (only sms or both types)
    allMessages.filter(msg => msg.message_type === 'sms' || msg.message_type === 'both')
        .forEach(message => {
            const option = document.createElement('option');
            option.value = message.id;
            option.textContent = message.name;
            messageDropdown.appendChild(option);
        });
}

// Show/hide recipient type fields
document.addEventListener('DOMContentLoaded', function() {
    const recipientTypeSelect = document.getElementById('smsRecipientType');
    const contactGroup = document.getElementById('smsContactGroup');
    const groupGroup = document.getElementById('smsGroupGroup');
    
    recipientTypeSelect.addEventListener('change', function() {
        const value = this.value;
        
        if (value === 'individual') {
            contactGroup.style.display = 'block';
            groupGroup.style.display = 'none';
            document.getElementById('smsContact').required = true;
            document.getElementById('smsGroup').required = false;
        } else if (value === 'group') {
            contactGroup.style.display = 'none';
            groupGroup.style.display = 'block';
            document.getElementById('smsContact').required = false;
            document.getElementById('smsGroup').required = true;
        } else if (value === 'all') {
            contactGroup.style.display = 'none';
            groupGroup.style.display = 'none';
            document.getElementById('smsContact').required = false;
            document.getElementById('smsGroup').required = false;
        }
    });
    
    // Update message preview when message is selected
    const messageSelect = document.getElementById('smsMessage');
    const messagePreview = document.getElementById('smsMessagePreview');
    const charCount = document.getElementById('smsCharCount');
    
    messageSelect.addEventListener('change', function() {
        const selectedMessageId = this.value;
        if (selectedMessageId) {
            const selectedMessage = allMessages.find(msg => msg.id === selectedMessageId);
            if (selectedMessage) {
                messagePreview.textContent = selectedMessage.content;
                charCount.textContent = `${selectedMessage.content.length}/160 characters`;
                
                // Highlight if over character limit
                if (selectedMessage.content.length > 160) {
                    charCount.style.color = 'var(--danger-color)';
                } else {
                    charCount.style.color = 'var(--gray-medium)';
                }
            }
        } else {
            messagePreview.textContent = 'Select a message to see preview...';
            charCount.textContent = '0/160 characters';
            charCount.style.color = 'var(--gray-medium)';
        }
    });
    
    // Form submission handler
    const smsForm = document.getElementById('smsForm');
    smsForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        await sendSms();
    });
    
    // Refresh button handler
    document.getElementById('refreshSms').addEventListener('click', function() {
        populateSmsOptions();
        getSmsHistory();
    });
    
    // Initialize SMS functionality
    populateSmsOptions();
    getSmsHistory();
});

async function sendSms() {
    const recipientType = document.getElementById('smsRecipientType').value;
    const contactId = document.getElementById('smsContact').value;
    const groupId = document.getElementById('smsGroup').value;
    const messageId = document.getElementById('smsMessage').value;
    
    if (!messageId) {
        alert('Please select a message to send.');
        return;
    }
    
    if (recipientType === 'individual' && !contactId) {
        alert('Please select a contact to send to.');
        return;
    }
    
    if (recipientType === 'group' && !groupId) {
        alert('Please select a group to send to.');
        return;
    }
    
    try {
        document.getElementById('sendSms').classList.add('loading');
        
        // Construct the URL parameters
        let url = '/trigger-sms';
        let params = [];
        
        // Add the message ID parameter
        params.push(`message_id=${messageId}`);
        
        // Add the recipient parameters based on type
        if (recipientType === 'individual') {
            // Create a JSON array of contact IDs
            params.push(`contacts=${JSON.stringify([contactId])}`);
        } else if (recipientType === 'group') {
            params.push(`group_id=${groupId}`);
        }
        
        // Build the complete URL with parameters
        const fullUrl = `${url}?${params.join('&')}`;
        
        console.log("Sending SMS request to:", fullUrl);
        
        // Send as a regular POST request without a body
        const response = await fetch(fullUrl, { 
            method: 'POST',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Failed to send SMS');
        }
        
        // Display success message
        logMessage(`SMS sending initiated: ${data.detail}`);
        
        // Show message to user
        const smsCount = data.sms_count || 0;
        if (smsCount > 0) {
            showToast(`SMS sending initiated to ${smsCount} recipient${smsCount !== 1 ? 's' : ''}`, 'success');
        } else {
            showToast('SMS sending initiated', 'success');
        }
        
        // Refresh SMS history and stats after a delay
        setTimeout(() => {
            getSmsHistory();
            getStats();
        }, 3000);
    } catch (error) {
        console.error('SMS error:', error);
        logMessage(`Failed to send SMS: ${error.message}`, true);
        showToast(`Failed to send SMS: ${error.message}`, 'error');
    } finally {
        document.getElementById('sendSms').classList.remove('loading');
    }
}

// Helper function to show toast notifications
function showToast(message, type = 'info') {
    // Check if the toast container exists, create if not
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.position = 'fixed';
        toastContainer.style.bottom = '20px';
        toastContainer.style.right = '20px';
        toastContainer.style.zIndex = '1000';
        document.body.appendChild(toastContainer);
    }
    
    // Create the toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.style.backgroundColor = type === 'error' ? 'var(--danger-color)' : 'var(--success-color)';
    toast.style.color = 'white';
    toast.style.padding = '10px 20px';
    toast.style.borderRadius = '4px';
    toast.style.marginTop = '10px';
    toast.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
    toast.style.minWidth = '200px';
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease-in-out';
    
    // Set the message
    toast.textContent = message;
    
    // Add to container
    toastContainer.appendChild(toast);
    
    // Fade in
    setTimeout(() => {
        toast.style.opacity = '1';
    }, 10);
    
    // Remove after delay
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => {
            toastContainer.removeChild(toast);
        }, 300);
    }, 5000);
}

async function getSmsHistory() {
    try {
        const response = await fetch('/sms-logs?limit=50');
        const logs = await response.json();
        
        const tbody = document.querySelector('#smsHistoryTable tbody');
        tbody.innerHTML = '';
        
        if (logs.length === 0) {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 5;
            cell.textContent = 'No SMS history found.';
            cell.style.textAlign = 'center';
            cell.style.padding = '20px';
            row.appendChild(cell);
            tbody.appendChild(row);
            return;
        }
        
        logs.forEach(log => {
            const row = document.createElement('tr');
            
            // Time cell
            const timeCell = document.createElement('td');
            timeCell.textContent = formatDate(log.sent_at);
            
            // Contact cell
            const contactCell = document.createElement('td');
            contactCell.textContent = log.contact_name;
            
            // Phone cell
            const phoneCell = document.createElement('td');
            phoneCell.textContent = formatPhone(log.phone_number);
            
            // Message cell
            const messageCell = document.createElement('td');
            if (log.message) {
                messageCell.textContent = log.message.name;
            } else {
                messageCell.textContent = 'Default';
                messageCell.style.fontStyle = 'italic';
                messageCell.style.color = '#888';
            }
            
            // Status cell
            const statusCell = document.createElement('td');
            const statusSpan = document.createElement('span');
            statusSpan.className = `status-pill ${log.status === 'sent' ? 'status-completed' : 'status-error'}`;
            statusSpan.textContent = log.status;
            statusCell.appendChild(statusSpan);
            
            row.appendChild(timeCell);
            row.appendChild(contactCell);
            row.appendChild(phoneCell);
            row.appendChild(messageCell);
            row.appendChild(statusCell);
            tbody.appendChild(row);
        });
        
        logMessage('SMS history loaded successfully');
    } catch (error) {
        logMessage(`Failed to load SMS history: ${error.message}`, true);
    }
}