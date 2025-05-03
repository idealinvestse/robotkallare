/**
 * GDial Settings UI
 * 
 * This JavaScript file handles all UI interactions for the settings page,
 * including loading, saving, and validating settings.
 */

// Utility function to show log messages
function logMessage(message, isError = false) {
    const output = document.getElementById('output');
    if (output) {
        const messageEl = document.createElement('div');
        messageEl.classList.add('log-message');
        
        if (isError) {
            messageEl.classList.add('error');
        }
        
        messageEl.textContent = message;
        output.appendChild(messageEl);
        
        // Scroll to the bottom
        output.scrollTop = output.scrollHeight;
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            messageEl.classList.add('fade-out');
            setTimeout(() => {
                output.removeChild(messageEl);
            }, 500);
        }, 5000);
    }
}

// Initialize settings navigation
function initializeSettingsNavigation() {
    const navButtons = document.querySelectorAll('.settings-nav-button');
    const sections = document.querySelectorAll('.settings-section');
    
    navButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons
            navButtons.forEach(btn => btn.classList.remove('active'));
            // Add active class to clicked button
            button.classList.add('active');
            
            // Hide all sections
            sections.forEach(section => section.classList.remove('active'));
            
            // Show the corresponding section
            const sectionName = button.getAttribute('data-settings-section');
            const section = document.getElementById(`${sectionName}-settings-section`);
            if (section) {
                section.classList.add('active');
            }
        });
    });
}

// Load all settings data
async function loadAllSettings() {
    try {
        // Show loading indicator
        document.querySelectorAll('.loading-indicator').forEach(el => {
            el.style.display = 'block';
        });
        
        // Load settings for each section
        await Promise.all([
            loadSystemSettings(),
            loadCallBotsSettings(),
            loadDtmfSettings(),
            loadSmsSettings(),
            loadNotificationSettings(),
            loadSecuritySettings()
        ]);
        
        logMessage('All settings loaded successfully');
    } catch (error) {
        logMessage(`Failed to load settings: ${error.message}`, true);
    } finally {
        // Hide loading indicators
        document.querySelectorAll('.loading-indicator').forEach(el => {
            el.style.display = 'none';
        });
    }
}

// General System Settings Functions
async function loadSystemSettings() {
    try {
        // Fetch settings groups
        const response = await fetch('/settings/system/groups');
        const groups = await response.json();
        
        // Get container element
        const container = document.getElementById('settingsGroupsContainer');
        container.innerHTML = ''; // Clear previous content
        
        // Create accordion for each group
        groups.forEach(group => {
            const groupDiv = document.createElement('div');
            groupDiv.classList.add('settings-group');
            
            // Create group header
            const header = document.createElement('div');
            header.classList.add('group-header');
            
            const groupName = document.createElement('h3');
            groupName.textContent = formatGroupName(group.group_name);
            header.appendChild(groupName);
            
            const toggleButton = document.createElement('button');
            toggleButton.classList.add('toggle-button');
            toggleButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>';
            header.appendChild(toggleButton);
            
            groupDiv.appendChild(header);
            
            // Create group content
            const content = document.createElement('div');
            content.classList.add('group-content');
            
            // Create form for settings
            const form = document.createElement('div');
            form.classList.add('form-grid');
            
            // Add each setting to the form
            group.settings.forEach(setting => {
                const formGroup = createSettingFormGroup(setting);
                form.appendChild(formGroup);
            });
            
            content.appendChild(form);
            groupDiv.appendChild(content);
            
            // Add to container
            container.appendChild(groupDiv);
            
            // Add toggle functionality
            header.addEventListener('click', () => {
                content.classList.toggle('expanded');
                toggleButton.classList.toggle('expanded');
            });
        });
        
        return groups;
    } catch (error) {
        logMessage(`Failed to load system settings: ${error.message}`, true);
        throw error;
    }
}

function formatGroupName(groupName) {
    // Convert snake_case or camelCase to Title Case with spaces
    return groupName
        .replace(/_/g, ' ')
        .replace(/([A-Z])/g, ' $1')
        .replace(/^./, str => str.toUpperCase())
        .trim();
}

function createSettingFormGroup(setting) {
    const formGroup = document.createElement('div');
    formGroup.classList.add('form-group');
    
    // Create label and input based on value type
    const label = document.createElement('label');
    label.setAttribute('for', `setting_${setting.key}`);
    label.textContent = formatSettingName(setting.key);
    
    let input;
    
    if (setting.value_type === 'boolean') {
        // Create checkbox for boolean values
        input = document.createElement('input');
        input.setAttribute('type', 'checkbox');
        input.setAttribute('id', `setting_${setting.key}`);
        input.setAttribute('name', setting.key);
        input.setAttribute('data-setting-key', setting.key);
        input.setAttribute('data-setting-type', setting.value_type);
        input.checked = (setting.value.toLowerCase() === 'true' || setting.value === '1' || setting.value === 'yes');
        
        // Wrap checkbox in label
        const checkboxLabel = document.createElement('label');
        checkboxLabel.classList.add('checkbox-label');
        checkboxLabel.appendChild(input);
        const span = document.createElement('span');
        span.textContent = formatSettingName(setting.key);
        checkboxLabel.appendChild(span);
        
        formGroup.appendChild(checkboxLabel);
    } else if (setting.value_type === 'int' || setting.value_type === 'float') {
        // Create number input
        formGroup.appendChild(label);
        
        input = document.createElement('input');
        input.setAttribute('type', 'number');
        input.setAttribute('id', `setting_${setting.key}`);
        input.setAttribute('name', setting.key);
        input.setAttribute('data-setting-key', setting.key);
        input.setAttribute('data-setting-type', setting.value_type);
        input.value = setting.value;
        
        if (setting.value_type === 'int') {
            input.setAttribute('step', '1');
        } else {
            input.setAttribute('step', '0.1');
        }
        
        formGroup.appendChild(input);
    } else if (setting.key.toLowerCase().includes('password') || setting.key.toLowerCase().includes('token') || setting.key.toLowerCase().includes('secret')) {
        // Create password input for sensitive data
        formGroup.appendChild(label);
        
        input = document.createElement('input');
        input.setAttribute('type', 'password');
        input.setAttribute('id', `setting_${setting.key}`);
        input.setAttribute('name', setting.key);
        input.setAttribute('data-setting-key', setting.key);
        input.setAttribute('data-setting-type', setting.value_type);
        input.value = setting.value;
        
        formGroup.appendChild(input);
    } else {
        // Create text input for everything else
        formGroup.appendChild(label);
        
        input = document.createElement('input');
        input.setAttribute('type', 'text');
        input.setAttribute('id', `setting_${setting.key}`);
        input.setAttribute('name', setting.key);
        input.setAttribute('data-setting-key', setting.key);
        input.setAttribute('data-setting-type', setting.value_type);
        input.value = setting.value;
        
        formGroup.appendChild(input);
    }
    
    // Add help text
    const helpText = document.createElement('div');
    helpText.classList.add('help-text');
    helpText.textContent = setting.description;
    formGroup.appendChild(helpText);
    
    return formGroup;
}

function formatSettingName(key) {
    // Convert snake_case to Title Case with spaces
    return key
        .replace(/_/g, ' ')
        .replace(/\b\w/g, char => char.toUpperCase());
}

async function saveSystemSettings() {
    try {
        const saveButton = document.getElementById('saveSystemSettings');
        saveButton.classList.add('loading');
        
        // Collect all visible settings
        const settings = {};
        const inputs = document.querySelectorAll('input[data-setting-key]');
        
        inputs.forEach(input => {
            const key = input.getAttribute('data-setting-key');
            const type = input.getAttribute('data-setting-type');
            
            let value;
            if (type === 'boolean') {
                value = input.checked ? 'true' : 'false';
            } else {
                value = input.value;
            }
            
            settings[key] = value;
        });
        
        // Send the update request
        const response = await fetch('/settings/system', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                settings: settings
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to update system settings');
        }
        
        const result = await response.json();
        console.log('Settings update result:', result);
        
        // Handle any "not_found" settings
        const notFoundSettings = Object.entries(result)
            .filter(([key, status]) => status === 'not_found')
            .map(([key]) => key);
            
        if (notFoundSettings.length > 0) {
            logMessage(`Some settings could not be found: ${notFoundSettings.join(', ')}`, true);
        } else {
            logMessage('System settings updated successfully');
        }
        
        // Reload settings to reflect changes
        await loadSystemSettings();
    } catch (error) {
        logMessage(`Failed to save system settings: ${error.message}`, true);
    } finally {
        const saveButton = document.getElementById('saveSystemSettings');
        saveButton.classList.remove('loading');
    }
}

// Call Bots Settings Functions
async function loadCallBotsSettings() {
    try {
        // First load basic settings from system settings
        const response = await fetch('/settings/system');
        const allSettings = await response.json();
        
        // Basic call bot settings
        const callBotsCount = allSettings.find(s => s.key === 'call_bots_count');
        const callsPerBot = allSettings.find(s => s.key === 'calls_per_bot');
        
        if (callBotsCount && document.getElementById('callBotsCount')) {
            document.getElementById('callBotsCount').value = callBotsCount.value;
        }
        
        if (callsPerBot && document.getElementById('callsPerBot')) {
            document.getElementById('callsPerBot').value = callsPerBot.value;
        }
        
        // Load advanced scaling settings
        const queueMaxSize = allSettings.find(s => s.key === 'queue_max_size');
        const queueScalingFactor = allSettings.find(s => s.key === 'queue_scaling_factor');
        const workerStartupTime = allSettings.find(s => s.key === 'worker_startup_time');
        const callRetryAttempts = allSettings.find(s => s.key === 'call_retry_attempts');
        const callRetryDelay = allSettings.find(s => s.key === 'call_retry_delay');
        const callTimeout = allSettings.find(s => s.key === 'call_timeout_sec');
        
        if (queueMaxSize && document.getElementById('queueMaxSize')) {
            document.getElementById('queueMaxSize').value = queueMaxSize.value;
        }
        
        if (queueScalingFactor && document.getElementById('queueScalingFactor')) {
            document.getElementById('queueScalingFactor').value = queueScalingFactor.value;
        }
        
        if (workerStartupTime && document.getElementById('workerStartupTime')) {
            document.getElementById('workerStartupTime').value = workerStartupTime.value;
        }
        
        if (callRetryAttempts && document.getElementById('callRetryAttempts')) {
            document.getElementById('callRetryAttempts').value = callRetryAttempts.value;
        }
        
        if (callRetryDelay && document.getElementById('callRetryDelay')) {
            document.getElementById('callRetryDelay').value = callRetryDelay.value;
        }
        
        if (callTimeout && document.getElementById('callTimeout')) {
            document.getElementById('callTimeout').value = callTimeout.value;
        }
        
        // Load scaling rules
        const minReplicas = allSettings.find(s => s.key === 'min_replicas');
        const maxReplicas = allSettings.find(s => s.key === 'max_replicas');
        const scalingMetric = allSettings.find(s => s.key === 'scaling_metric');
        const scaleDownDelay = allSettings.find(s => s.key === 'scale_down_delay');
        
        if (minReplicas && document.getElementById('minReplicas')) {
            document.getElementById('minReplicas').value = minReplicas.value;
        }
        
        if (maxReplicas && document.getElementById('maxReplicas')) {
            document.getElementById('maxReplicas').value = maxReplicas.value;
        }
        
        if (scalingMetric && document.getElementById('scalingMetric')) {
            document.getElementById('scalingMetric').value = scalingMetric.value;
        }
        
        if (scaleDownDelay && document.getElementById('scaleDownDelay')) {
            document.getElementById('scaleDownDelay').value = scaleDownDelay.value;
        }
        
        // Load queue settings
        const queueType = allSettings.find(s => s.key === 'queue_type');
        const queueHost = allSettings.find(s => s.key === 'queue_host');
        const queuePort = allSettings.find(s => s.key === 'queue_port');
        const queueName = allSettings.find(s => s.key === 'queue_name');
        
        if (queueType && document.getElementById('queueType')) {
            document.getElementById('queueType').value = queueType.value;
        }
        
        if (queueHost && document.getElementById('queueHost')) {
            document.getElementById('queueHost').value = queueHost.value;
        }
        
        if (queuePort && document.getElementById('queuePort')) {
            document.getElementById('queuePort').value = queuePort.value;
        }
        
        if (queueName && document.getElementById('queueName')) {
            document.getElementById('queueName').value = queueName.value;
        }
        
        // Setup form submission handler
        const form = document.getElementById('callBotsSettingsForm');
        if (form) {
            form.addEventListener('submit', saveCallBotsSettings);
        }
        
    } catch (error) {
        logMessage(`Failed to load call bots settings: ${error.message}`, true);
        throw error;
    }
}

async function saveCallBotsSettings(e) {
    e.preventDefault();
    
    try {
        const submitButton = document.querySelector('#callBotsSettingsForm button[type="submit"]');
        if (submitButton) {
            submitButton.classList.add('loading');
        }
        
        // Collect all the settings from the form
        const settings = {};
        
        // Basic settings
        const callBotsCount = document.getElementById('callBotsCount');
        const callsPerBot = document.getElementById('callsPerBot');
        
        if (!callBotsCount || !callsPerBot) {
            throw new Error('Required call bots setting elements not found');
        }
        
        settings['call_bots_count'] = callBotsCount.value;
        settings['calls_per_bot'] = callsPerBot.value;
        
        // Advanced scaling settings
        const queueMaxSize = document.getElementById('queueMaxSize');
        const queueScalingFactor = document.getElementById('queueScalingFactor');
        const workerStartupTime = document.getElementById('workerStartupTime');
        const callRetryAttempts = document.getElementById('callRetryAttempts');
        const callRetryDelay = document.getElementById('callRetryDelay');
        const callTimeout = document.getElementById('callTimeout');
        
        if (queueMaxSize) settings['queue_max_size'] = queueMaxSize.value;
        if (queueScalingFactor) settings['queue_scaling_factor'] = queueScalingFactor.value;
        if (workerStartupTime) settings['worker_startup_time'] = workerStartupTime.value;
        if (callRetryAttempts) settings['call_retry_attempts'] = callRetryAttempts.value;
        if (callRetryDelay) settings['call_retry_delay'] = callRetryDelay.value;
        if (callTimeout) settings['call_timeout_sec'] = callTimeout.value;
        
        // Scaling rules
        const minReplicas = document.getElementById('minReplicas');
        const maxReplicas = document.getElementById('maxReplicas');
        const scalingMetric = document.getElementById('scalingMetric');
        const scaleDownDelay = document.getElementById('scaleDownDelay');
        
        if (minReplicas) settings['min_replicas'] = minReplicas.value;
        if (maxReplicas) settings['max_replicas'] = maxReplicas.value;
        if (scalingMetric) settings['scaling_metric'] = scalingMetric.value;
        if (scaleDownDelay) settings['scale_down_delay'] = scaleDownDelay.value;
        
        // Queue settings
        const queueType = document.getElementById('queueType');
        const queueHost = document.getElementById('queueHost');
        const queuePort = document.getElementById('queuePort');
        const queueName = document.getElementById('queueName');
        
        if (queueType) settings['queue_type'] = queueType.value;
        if (queueHost) settings['queue_host'] = queueHost.value;
        if (queuePort) settings['queue_port'] = queuePort.value;
        if (queueName) settings['queue_name'] = queueName.value;
        
        // Send the update request
        const response = await fetch('/settings/system', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                settings: settings
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to update call bots settings');
        }
        
        const result = await response.json();
        console.log('Settings update result:', result);
        
        // Check for settings that could not be found
        const notFoundSettings = Object.entries(result)
            .filter(([key, status]) => status === 'not_found')
            .map(([key]) => key);
            
        if (notFoundSettings.length > 0) {
            logMessage(`Some settings could not be found: ${notFoundSettings.join(', ')}. They will be created.`, true);
        }
        
        // Reload the settings to reflect changes
        await loadCallBotsSettings();
        
        logMessage('Call bots settings updated successfully');
    } catch (error) {
        logMessage(`Failed to save call bots settings: ${error.message}`, true);
    } finally {
        const submitButton = document.querySelector('#callBotsSettingsForm button[type="submit"]');
        if (submitButton) {
            submitButton.classList.remove('loading');
        }
    }
}

// DTMF Settings Functions
async function loadDtmfSettings() {
    try {
        const response = await fetch('/settings/dtmf');
        const dtmfSettings = await response.json();
        
        // Populate form - only if elements exist
        const maxAttempts = document.getElementById('maxAttempts');
        const inputTimeout = document.getElementById('inputTimeout');
        const confirmResponse = document.getElementById('confirmResponse');
        const retryOnInvalid = document.getElementById('retryOnInvalid');
        const additionalDigits = document.getElementById('additionalDigits');
        const universalGather = document.getElementById('universalGather');
        const repeatMessageDigit = document.getElementById('repeatMessageDigit');
        const confirmReceiptDigit = document.getElementById('confirmReceiptDigit');
        const requestCallbackDigit = document.getElementById('requestCallbackDigit');
        const transferToLiveAgentDigit = document.getElementById('transferToLiveAgentDigit');
        const dtmfMenuStyle = document.getElementById('dtmfMenuStyle');
        const interDigitTimeout = document.getElementById('interDigitTimeout');
        const allowMessageSkip = document.getElementById('allowMessageSkip');
        
        if (maxAttempts) maxAttempts.value = dtmfSettings.max_attempts;
        if (inputTimeout) inputTimeout.value = dtmfSettings.input_timeout;
        if (confirmResponse) confirmResponse.checked = dtmfSettings.confirm_response;
        if (retryOnInvalid) retryOnInvalid.checked = dtmfSettings.retry_on_invalid;
        if (additionalDigits) additionalDigits.value = dtmfSettings.additional_digits || '';
        if (universalGather) universalGather.checked = dtmfSettings.universal_gather;
        if (repeatMessageDigit) repeatMessageDigit.value = dtmfSettings.repeat_message_digit;
        if (confirmReceiptDigit) confirmReceiptDigit.value = dtmfSettings.confirm_receipt_digit;
        if (requestCallbackDigit) requestCallbackDigit.value = dtmfSettings.request_callback_digit;
        if (transferToLiveAgentDigit) transferToLiveAgentDigit.value = dtmfSettings.transfer_to_live_agent_digit;
        if (dtmfMenuStyle) dtmfMenuStyle.value = dtmfSettings.dtmf_menu_style;
        if (interDigitTimeout) interDigitTimeout.value = dtmfSettings.inter_digit_timeout;
        if (allowMessageSkip) allowMessageSkip.checked = dtmfSettings.allow_message_skip;
    } catch (error) {
        logMessage(`Failed to load DTMF settings: ${error.message}`, true);
    }
}

async function saveDtmfSettings(e) {
    e.preventDefault();
    
    try {
        const submitButton = document.querySelector('#dtmfSettingsForm button[type="submit"]');
        if (submitButton) {
            submitButton.classList.add('loading');
        }
        
        // Collect values from form
        const maxAttempts = document.getElementById('maxAttempts').value;
        const inputTimeout = document.getElementById('inputTimeout').value;
        const confirmResponse = document.getElementById('confirmResponse').checked;
        const retryOnInvalid = document.getElementById('retryOnInvalid').checked;
        const additionalDigits = document.getElementById('additionalDigits').value;
        const universalGather = document.getElementById('universalGather').checked;
        const repeatMessageDigit = document.getElementById('repeatMessageDigit').value;
        const confirmReceiptDigit = document.getElementById('confirmReceiptDigit').value;
        const requestCallbackDigit = document.getElementById('requestCallbackDigit').value;
        const transferToLiveAgentDigit = document.getElementById('transferToLiveAgentDigit').value;
        const dtmfMenuStyle = document.getElementById('dtmfMenuStyle').value;
        const interDigitTimeout = document.getElementById('interDigitTimeout').value;
        const allowMessageSkip = document.getElementById('allowMessageSkip').checked;
        
        // Build update object
        const updateData = {
            max_attempts: parseInt(maxAttempts),
            input_timeout: parseInt(inputTimeout),
            confirm_response: confirmResponse,
            retry_on_invalid: retryOnInvalid,
            additional_digits: additionalDigits,
            universal_gather: universalGather,
            repeat_message_digit: repeatMessageDigit,
            confirm_receipt_digit: confirmReceiptDigit,
            request_callback_digit: requestCallbackDigit,
            transfer_to_live_agent_digit: transferToLiveAgentDigit,
            dtmf_menu_style: dtmfMenuStyle,
            inter_digit_timeout: parseInt(interDigitTimeout),
            allow_message_skip: allowMessageSkip
        };
        
        // Send the update request
        const response = await fetch('/settings/dtmf', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updateData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to update DTMF settings');
        }
        
        logMessage('DTMF settings updated successfully');
    } catch (error) {
        logMessage(`Failed to save DTMF settings: ${error.message}`, true);
    } finally {
        const submitButton = document.querySelector('#dtmfSettingsForm button[type="submit"]');
        if (submitButton) {
            submitButton.classList.remove('loading');
        }
    }
}

// SMS Settings Functions
async function loadSmsSettings() {
    try {
        const response = await fetch('/settings/sms');
        const smsSettings = await response.json();
        
        // Populate form - only if elements exist
        const includeSenderName = document.getElementById('includeSenderName');
        const messagePrefix = document.getElementById('messagePrefix');
        const messageSuffix = document.getElementById('messageSuffix');
        const maxLength = document.getElementById('maxLength');
        const splitLongMessages = document.getElementById('splitLongMessages');
        const batchDelayMs = document.getElementById('batchDelayMs');
        const batchSize = document.getElementById('batchSize');
        const statusCallbackUrl = document.getElementById('statusCallbackUrl');
        
        if (includeSenderName) includeSenderName.checked = smsSettings.include_sender_name;
        if (messagePrefix) messagePrefix.value = smsSettings.message_prefix;
        if (messageSuffix) messageSuffix.value = smsSettings.message_suffix;
        if (maxLength) maxLength.value = smsSettings.max_length;
        if (splitLongMessages) splitLongMessages.checked = smsSettings.split_long_messages;
        if (batchDelayMs) batchDelayMs.value = smsSettings.batch_delay_ms;
        if (batchSize) batchSize.value = smsSettings.batch_size;
        if (statusCallbackUrl) statusCallbackUrl.value = smsSettings.status_callback_url || '';
    } catch (error) {
        logMessage(`Failed to load SMS settings: ${error.message}`, true);
    }
}

async function saveSmsSettings(e) {
    e.preventDefault();
    
    try {
        const submitButton = document.querySelector('#smsSettingsForm button[type="submit"]');
        if (submitButton) {
            submitButton.classList.add('loading');
        }
        
        // Collect values from form
        const includeSenderName = document.getElementById('includeSenderName').checked;
        const messagePrefix = document.getElementById('messagePrefix').value;
        const messageSuffix = document.getElementById('messageSuffix').value;
        const maxLength = document.getElementById('maxLength').value;
        const splitLongMessages = document.getElementById('splitLongMessages').checked;
        const batchDelayMs = document.getElementById('batchDelayMs').value;
        const batchSize = document.getElementById('batchSize').value;
        const statusCallbackUrl = document.getElementById('statusCallbackUrl').value;
        
        // Build update object
        const updateData = {
            include_sender_name: includeSenderName,
            message_prefix: messagePrefix,
            message_suffix: messageSuffix,
            max_length: parseInt(maxLength),
            split_long_messages: splitLongMessages,
            batch_delay_ms: parseInt(batchDelayMs),
            batch_size: parseInt(batchSize),
            status_callback_url: statusCallbackUrl || null
        };
        
        // Send the update request
        const response = await fetch('/settings/sms', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updateData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to update SMS settings');
        }
        
        logMessage('SMS settings updated successfully');
    } catch (error) {
        logMessage(`Failed to save SMS settings: ${error.message}`, true);
    } finally {
        const submitButton = document.querySelector('#smsSettingsForm button[type="submit"]');
        if (submitButton) {
            submitButton.classList.remove('loading');
        }
    }
}

// Notification Settings Functions
async function loadNotificationSettings() {
    try {
        const response = await fetch('/settings/notifications');
        const notificationSettings = await response.json();
        
        // Populate form - only if elements exist
        const adminEmail = document.getElementById('adminEmail');
        const notifyOnEmergency = document.getElementById('notifyOnEmergency');
        const notifyOnError = document.getElementById('notifyOnError');
        const failureThresholdPct = document.getElementById('failureThresholdPct');
        const dailyReports = document.getElementById('dailyReports');
        const weeklyReports = document.getElementById('weeklyReports');
        
        if (adminEmail) adminEmail.value = notificationSettings.admin_email || '';
        if (notifyOnEmergency) notifyOnEmergency.checked = notificationSettings.notify_on_emergency;
        if (notifyOnError) notifyOnError.checked = notificationSettings.notify_on_error;
        if (failureThresholdPct) failureThresholdPct.value = notificationSettings.failure_threshold_pct;
        if (dailyReports) dailyReports.checked = notificationSettings.daily_reports;
        if (weeklyReports) weeklyReports.checked = notificationSettings.weekly_reports;
    } catch (error) {
        logMessage(`Failed to load notification settings: ${error.message}`, true);
    }
}

async function saveNotificationSettings(e) {
    e.preventDefault();
    
    try {
        const submitButton = document.querySelector('#notificationSettingsForm button[type="submit"]');
        if (submitButton) {
            submitButton.classList.add('loading');
        }
        
        // Collect values from form
        const adminEmail = document.getElementById('adminEmail').value;
        const notifyOnEmergency = document.getElementById('notifyOnEmergency').checked;
        const notifyOnError = document.getElementById('notifyOnError').checked;
        const failureThresholdPct = document.getElementById('failureThresholdPct').value;
        const dailyReports = document.getElementById('dailyReports').checked;
        const weeklyReports = document.getElementById('weeklyReports').checked;
        
        // Build update object
        const updateData = {
            admin_email: adminEmail || null,
            notify_on_emergency: notifyOnEmergency,
            notify_on_error: notifyOnError,
            failure_threshold_pct: parseInt(failureThresholdPct),
            daily_reports: dailyReports,
            weekly_reports: weeklyReports
        };
        
        // Send the update request
        const response = await fetch('/settings/notifications', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updateData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to update notification settings');
        }
        
        logMessage('Notification settings updated successfully');
    } catch (error) {
        logMessage(`Failed to save notification settings: ${error.message}`, true);
    } finally {
        const submitButton = document.querySelector('#notificationSettingsForm button[type="submit"]');
        if (submitButton) {
            submitButton.classList.remove('loading');
        }
    }
}

// Security Settings Functions
async function loadSecuritySettings() {
    try {
        const response = await fetch('/settings/security');
        securitySettings = await response.json();
        
        // Populate form - only if elements exist
        const forceHttps = document.getElementById('forceHttps');
        const sensitiveDataMasking = document.getElementById('sensitiveDataMasking');
        const autoLogoutInactiveMin = document.getElementById('autoLogoutInactiveMin');
        const maxLoginAttempts = document.getElementById('maxLoginAttempts');
        
        if (forceHttps) forceHttps.checked = securitySettings.force_https;
        if (sensitiveDataMasking) sensitiveDataMasking.checked = securitySettings.sensitive_data_masking;
        if (autoLogoutInactiveMin) autoLogoutInactiveMin.value = securitySettings.auto_logout_inactive_min;
        if (maxLoginAttempts) maxLoginAttempts.value = securitySettings.max_login_attempts;
    } catch (error) {
        logMessage(`Failed to load security settings: ${error.message}`, true);
    }
}

async function saveSecuritySettings(e) {
    e.preventDefault();
    
    try {
        const submitButton = document.querySelector('#securitySettingsForm button[type="submit"]');
        if (submitButton) {
            submitButton.classList.add('loading');
        }
        
        // Collect values from form
        const forceHttps = document.getElementById('forceHttps').checked;
        const sensitiveDataMasking = document.getElementById('sensitiveDataMasking').checked;
        const autoLogoutInactiveMin = document.getElementById('autoLogoutInactiveMin').value;
        const maxLoginAttempts = document.getElementById('maxLoginAttempts').value;
        
        // Build update object
        const updateData = {
            force_https: forceHttps,
            sensitive_data_masking: sensitiveDataMasking,
            auto_logout_inactive_min: parseInt(autoLogoutInactiveMin),
            max_login_attempts: parseInt(maxLoginAttempts)
        };
        
        // Send the update request
        const response = await fetch('/settings/security', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(updateData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to update security settings');
        }
        
        logMessage('Security settings updated successfully');
    } catch (error) {
        logMessage(`Failed to save security settings: ${error.message}`, true);
    } finally {
        const submitButton = document.querySelector('#securitySettingsForm button[type="submit"]');
        if (submitButton) {
            submitButton.classList.remove('loading');
        }
    }
}