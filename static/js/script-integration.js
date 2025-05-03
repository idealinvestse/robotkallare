/**
 * Integration functions for task progress tracking
 * 
 * This script contains functions that patch into the existing codebase
 * to add task progress tracking functionality.
 */

// Wait for both the main script and TaskManager to initialize
document.addEventListener('DOMContentLoaded', function() {
    // Make sure our integration happens after the main script initializes
    setTimeout(initializeProgressTracking, 500);
});

function initializeProgressTracking() {
    // Patch SMS sending functionality
    patchSmsForm();
    patchCustomSmsForm();
    
    // Patch call functionality
    patchEmergencyCalls();
    patchManualCalls();
    patchCustomCalls();
    
    // Patch other async operations
    patchContactImport();
    patchGroupOperations();
    
    console.log('Task progress tracking integration complete');
}

function patchSmsForm() {
    const smsForm = document.getElementById('smsForm');
    if (!smsForm) return;
    
    // Store the original submit handler
    const originalSubmit = smsForm.onsubmit;
    
    // Replace with our patched version
    smsForm.onsubmit = function(e) {
        e.preventDefault();
        
        // Extract recipient info for progress tracking
        const recipientType = document.getElementById('smsRecipientType').value;
        let recipientInfo = "Unknown recipients";
        let recipientCount = "?";
        
        switch(recipientType) {
            case 'individual':
                const contactSelect = document.getElementById('smsContact');
                recipientInfo = contactSelect.options[contactSelect.selectedIndex].text;
                recipientCount = 1;
                break;
            case 'group':
                const groupSelect = document.getElementById('smsGroup');
                recipientInfo = groupSelect.options[groupSelect.selectedIndex].text;
                // We'll update this count later
                recipientCount = "group";
                break;
            case 'all':
                recipientInfo = "All Contacts";
                // We'll update this count later
                recipientCount = "all";
                break;
        }
        
        // Create the progress task
        const messageSelect = document.getElementById('smsMessage');
        const messageText = messageSelect.options[messageSelect.selectedIndex].text;
        
        const taskId = TaskManager.trackSmsTask(
            `SMS: ${messageText}`, 
            typeof recipientCount === 'number' ? recipientCount : '...'
        );
        
        // Call the original handler
        const originalResult = originalSubmit.call(this, e);
        
        // Set up API monitoring to track progress
        monitorSmsProgress(taskId, recipientType, recipientInfo);
        
        return originalResult;
    };
}

function patchCustomSmsForm() {
    const customSmsForm = document.getElementById('customSmsForm');
    if (!customSmsForm) return;
    
    const originalSubmit = customSmsForm.onsubmit;
    
    customSmsForm.onsubmit = function(e) {
        e.preventDefault();
        
        // Extract recipient info
        const recipientType = document.getElementById('customSmsRecipientType').value;
        let recipientInfo = "Unknown recipients";
        let recipientCount = "?";
        
        switch(recipientType) {
            case 'individual':
                const contactSelect = document.getElementById('customSmsContact');
                recipientInfo = contactSelect.options[contactSelect.selectedIndex].text;
                recipientCount = 1;
                break;
            case 'group':
                const groupSelect = document.getElementById('customSmsGroup');
                recipientInfo = groupSelect.options[groupSelect.selectedIndex].text;
                recipientCount = "group";
                break;
            case 'all':
                recipientInfo = "All Contacts";
                recipientCount = "all";
                break;
        }
        
        // Get message preview
        const messagePreview = document.getElementById('customSmsContent').value.substring(0, 30) + "...";
        
        // Create the progress task
        const taskId = TaskManager.trackSmsTask(
            `Custom SMS: ${messagePreview}`, 
            typeof recipientCount === 'number' ? recipientCount : '...'
        );
        
        // Call the original handler
        const originalResult = originalSubmit.call(this, e);
        
        // Set up API monitoring
        monitorSmsProgress(taskId, recipientType, recipientInfo);
        
        return originalResult;
    };
}

function patchEmergencyCalls() {
    const dialerButton = document.getElementById('triggerDialer');
    if (!dialerButton) return;
    
    const originalClickHandler = dialerButton.onclick;
    
    dialerButton.onclick = function(e) {
        // Extract recipient info
        const messageSelect = document.getElementById('messageSelector');
        const messageText = messageSelect.options[messageSelect.selectedIndex].text;
        
        const groupSelect = document.getElementById('groupSelector');
        const groupText = groupSelect.options[groupSelect.selectedIndex].text;
        
        // Create task
        const taskId = TaskManager.trackCallTask(`Emergency Call: ${messageText}`, `Group: ${groupText}`);
        
        // Call original handler
        if (originalClickHandler) {
            originalClickHandler.call(this, e);
        }
        
        // Monitor progress
        monitorCallProgress(taskId, messageText, groupText);
    };
}

function patchManualCalls() {
    const manualCallForm = document.getElementById('manualCallForm');
    if (!manualCallForm) return;
    
    const originalSubmit = manualCallForm.onsubmit;
    
    manualCallForm.onsubmit = function(e) {
        e.preventDefault();
        
        // Extract call info
        const contactSelect = document.getElementById('manualCallContact');
        const contactText = contactSelect.options[contactSelect.selectedIndex].text;
        
        const messageSelect = document.getElementById('manualCallMessage');
        const messageText = messageSelect.options[messageSelect.selectedIndex].text;
        
        // Create task
        const taskId = TaskManager.trackCallTask(`Manual Call: ${messageText}`, `To: ${contactText}`);
        
        // Call original handler
        const originalResult = originalSubmit.call(this, e);
        
        // Monitor progress
        monitorManualCallProgress(taskId, contactText);
        
        return originalResult;
    };
}

function patchCustomCalls() {
    const customCallForm = document.getElementById('customCallForm');
    if (!customCallForm) return;
    
    const originalSubmit = customCallForm.onsubmit;
    
    customCallForm.onsubmit = function(e) {
        e.preventDefault();
        
        // Extract info
        const contactSelect = document.getElementById('customCallContact');
        const contactText = contactSelect.options[contactSelect.selectedIndex].text;
        
        const messagePreview = document.getElementById('customCallMessageContent').value.substring(0, 30) + "...";
        
        // Create task
        const taskId = TaskManager.trackCallTask(`Custom Call: ${messagePreview}`, `To: ${contactText}`);
        
        // Call original handler
        const originalResult = originalSubmit.call(this, e);
        
        // Monitor progress
        monitorManualCallProgress(taskId, contactText);
        
        return originalResult;
    };
}

function patchContactImport() {
    // This would integrate with any contact import functionality
    // Left as a placeholder for future implementation
}

function patchGroupOperations() {
    // This would integrate with group-related operations
    // Left as a placeholder for future implementation
}

// Helper functions to monitor progress
function monitorSmsProgress(taskId, recipientType, recipientInfo) {
    // Poll the server for status updates
    pollSmsStatus(taskId, recipientType, recipientInfo);
}

function pollSmsStatus(taskId, recipientType, recipientInfo) {
    // First update with some initial progress
    TaskManager.updateTaskProgress(
        taskId, 
        10, 
        `Sending messages to ${recipientInfo}...`
    );
    
    // Add more detailed log entries
    TaskManager.addLogEntry(taskId, `Preparing message delivery for ${recipientInfo}`);
    TaskManager.addLogEntry(taskId, `Message type: SMS`);
    
    // Variables to track progress and avoid duplicate logs
    let task_has_first_log = false;
    let last_successful = 0;
    let last_failed = 0;
    
    // Keep track of when we started
    const startTime = Date.now();
    
    // Function to check SMS logs and update progress
    function checkSmsProgress() {
        fetch('/sms-logs?limit=50')
            .then(response => response.json())
            .then(data => {
                // Get recent SMS logs from the last minute
                const recentLogs = data.filter(log => {
                    const logTime = new Date(log.sent_at).getTime();
                    return (logTime > startTime - 60000); // Within last minute
                });
                
                if (recentLogs.length === 0) {
                    // If no recent logs found but we've been waiting more than 15 seconds
                    if (Date.now() - startTime > 15000) {
                        // Check if task is still running or should be marked complete
                        fetch('/stats')
                            .then(response => response.json())
                            .then(statsData => {
                                if (!statsData.sms_in_progress) {
                                    // Task is no longer running according to server
                                    TaskManager.completeTask(taskId, `SMS sending to ${recipientInfo} completed`);
                                    return; // Exit the polling loop
                                } else {
                                    // Still in progress but no logs yet
                                    TaskManager.updateTaskProgress(
                                        taskId, 
                                        20, 
                                        `Preparing messages for ${recipientInfo}...`
                                    );
                                    setTimeout(checkSmsProgress, 2000);
                                }
                            })
                            .catch(error => {
                                console.error("Error checking stats:", error);
                                setTimeout(checkSmsProgress, 3000);
                            });
                    } else {
                        // Still early in the process, check again soon
                        TaskManager.updateTaskProgress(
                            taskId, 
                            15, 
                            `Initializing message delivery...`
                        );
                        setTimeout(checkSmsProgress, 1500);
                    }
                    return;
                }
                
                // We have logs, calculate progress based on successful vs total
                const totalExpected = recipientType === 'individual' ? 1 : 
                                     (recipientType === 'group' ? recentLogs.length : recentLogs.length);
                const successful = recentLogs.filter(log => log.status === 'sent').length;
                const failed = recentLogs.filter(log => log.status === 'failed').length;
                const processed = successful + failed;
                const estimatedProgress = Math.min(95, Math.floor((processed / totalExpected) * 100));
                
                // If this is the first time we're seeing logs, add a detail
                if (processed > 0 && !task_has_first_log) {
                    TaskManager.addLogEntry(taskId, `Message delivery started, processing ${totalExpected} messages`);
                    task_has_first_log = true;
                }
                
                // Add log entries for new messages
                if (successful > last_successful) {
                    const newSuccessful = successful - last_successful;
                    TaskManager.addLogEntry(
                        taskId, 
                        `${newSuccessful} message${newSuccessful > 1 ? 's' : ''} delivered successfully`
                    );
                    last_successful = successful;
                }
                
                if (failed > last_failed) {
                    const newFailed = failed - last_failed;
                    TaskManager.addLogEntry(
                        taskId,
                        `${newFailed} message${newFailed > 1 ? 's' : ''} failed to deliver`
                    );
                    last_failed = failed;
                }
                
                if (processed >= totalExpected || estimatedProgress >= 95 || (Date.now() - startTime > 30000)) {
                    // Task should be complete or timed out
                    if (failed > 0) {
                        // Add detailed completion log
                        TaskManager.addLogEntry(
                            taskId,
                            `Operation completed: ${successful} of ${totalExpected} messages delivered successfully`
                        );
                        if (failed > 0) {
                            TaskManager.addLogEntry(
                                taskId,
                                `${failed} messages failed to deliver`
                            );
                        }
                        
                        TaskManager.completeTask(
                            taskId, 
                            `Completed with ${successful} successful and ${failed} failed messages`
                        );
                    } else {
                        TaskManager.addLogEntry(
                            taskId,
                            `All ${successful} messages delivered successfully to ${recipientInfo}`
                        );
                        
                        TaskManager.completeTask(
                            taskId, 
                            `Successfully delivered all ${successful} messages to ${recipientInfo}`
                        );
                    }
                } else {
                    // Still in progress
                    TaskManager.updateTaskProgress(
                        taskId, 
                        estimatedProgress, 
                        `Sent ${processed} of ${totalExpected} messages... ${successful} successful, ${failed} failed`
                    );
                    setTimeout(checkSmsProgress, 2000);
                }
            })
            .catch(error => {
                console.error("Error checking SMS logs:", error);
                // Error fetching logs, check again after a delay
                setTimeout(checkSmsProgress, 3000);
            });
    }
    
    // Start the polling process
    checkSmsProgress();
}

function monitorCallProgress(taskId, messageText, groupText) {
    // First update
    TaskManager.updateTaskProgress(
        taskId, 
        5, 
        `Initiating calls for "${messageText}"...`
    );
    
    // Add detailed logs
    TaskManager.addLogEntry(taskId, `Preparing emergency call notification for ${groupText}`);
    TaskManager.addLogEntry(taskId, `Message: "${messageText}"`);
    TaskManager.addLogEntry(taskId, `Call system initializing...`);
    
    // Variables to track progress and avoid duplicate logs
    let lastCompletedCount = 0;
    let lastAnsweredCount = 0;
    let lastStage = '';
    
    // Keep track of when we started
    const startTime = Date.now();
    
    // Function to check call logs and update progress
    function checkCallProgress() {
        // First check if there's an active call run
        fetch('/stats')
            .then(response => response.json())
            .then(statsData => {
                // Check if we have an active call run
                if (statsData.current_call_run && statsData.current_call_run.status === 'in_progress') {
                    const callRun = statsData.current_call_run;
                    const totalCalls = callRun.total_calls || 0;
                    const completedCalls = callRun.completed_calls || 0;
                    const answeredCalls = callRun.answered_calls || 0;
                    
                    // Calculate progress
                    const progressPercent = totalCalls > 0 ? 
                        Math.min(95, Math.floor((completedCalls / totalCalls) * 100)) : 20;
                    
                    // Log update for call initiation
                    if (lastStage !== 'calls-initialized' && totalCalls > 0) {
                        TaskManager.addLogEntry(
                            taskId,
                            `Call batch initialized with ${totalCalls} total calls queued`
                        );
                        lastStage = 'calls-initialized';
                    }
                    
                    // Log new completed calls
                    if (completedCalls > lastCompletedCount) {
                        const newCompletedCalls = completedCalls - lastCompletedCount;
                        TaskManager.addLogEntry(
                            taskId,
                            `${newCompletedCalls} new call${newCompletedCalls > 1 ? 's' : ''} completed (${completedCalls}/${totalCalls} total)`
                        );
                        lastCompletedCount = completedCalls;
                    }
                    
                    // Log new answered calls
                    if (answeredCalls > lastAnsweredCount) {
                        const newAnsweredCalls = answeredCalls - lastAnsweredCount;
                        TaskManager.addLogEntry(
                            taskId,
                            `${newAnsweredCalls} new call${newAnsweredCalls > 1 ? 's' : ''} answered successfully`
                        );
                        lastAnsweredCount = answeredCalls;
                    }
                    
                    // Update task
                    TaskManager.updateTaskProgress(
                        taskId,
                        progressPercent,
                        `Completed ${completedCalls} of ${totalCalls} calls, ${answeredCalls} answered`
                    );
                    
                    // Check again after a delay, unless completed
                    if (completedCalls >= totalCalls && totalCalls > 0) {
                        TaskManager.addLogEntry(
                            taskId,
                            `Call batch completed: ${totalCalls} total calls processed`
                        );
                        TaskManager.addLogEntry(
                            taskId,
                            `Call statistics: ${answeredCalls} answered, ${completedCalls - answeredCalls} not answered`
                        );
                        
                        TaskManager.completeTask(
                            taskId,
                            `Completed all ${totalCalls} calls, ${answeredCalls} answered`
                        );
                    } else {
                        setTimeout(checkCallProgress, 2000);
                    }
                } else if (statsData.last_call_run && 
                           statsData.last_call_run.completed_at && 
                           new Date(statsData.last_call_run.completed_at).getTime() > startTime) {
                    // Call run is completed
                    const callRun = statsData.last_call_run;
                    TaskManager.completeTask(
                        taskId,
                        `Completed ${callRun.completed_calls} calls, ${callRun.answered_calls} answered`
                    );
                } else if (Date.now() - startTime > 30000) {
                    // It's been 30 seconds with no completion, mark as completed anyway
                    TaskManager.completeTask(
                        taskId,
                        `Call batch to ${groupText} appears to be complete`
                    );
                } else {
                    // No active call run found yet, check call logs
                    fetch('/call-logs?limit=20')
                        .then(response => response.json())
                        .then(logsData => {
                            // Check for recent calls
                            const recentLogs = logsData.filter(log => {
                                const logTime = new Date(log.started_at).getTime();
                                return (logTime > startTime - 60000); // Within last minute
                            });
                            
                            if (recentLogs.length > 0) {
                                // We have some call logs, update progress
                                const progress = Math.min(85, 20 + recentLogs.length * 5);
                                TaskManager.updateTaskProgress(
                                    taskId,
                                    progress,
                                    `Processing calls: ${recentLogs.length} calls initiated`
                                );
                            } else {
                                // No logs yet, still initializing
                                TaskManager.updateTaskProgress(
                                    taskId,
                                    15,
                                    `Preparing to place calls...`
                                );
                            }
                            
                            // Check again after a delay
                            setTimeout(checkCallProgress, 2000);
                        })
                        .catch(error => {
                            console.error("Error checking call logs:", error);
                            setTimeout(checkCallProgress, 3000);
                        });
                }
            })
            .catch(error => {
                console.error("Error checking stats:", error);
                // Error fetching stats, check again after a delay
                setTimeout(checkCallProgress, 3000);
            });
    }
    
    // Start the polling process
    checkCallProgress();
}

function monitorManualCallProgress(taskId, contactText) {
    // Update initial status
    TaskManager.updateTaskProgress(taskId, 5, 'Initiating call...');
    
    // Add detailed logs
    TaskManager.addLogEntry(taskId, `Preparing manual call to ${contactText}`);
    TaskManager.addLogEntry(taskId, `Initializing call system...`);
    
    // Keep track of status for logging
    let lastStage = '';
    
    // Keep track of when we started
    const startTime = Date.now();
    
    // Function to check call logs for manual call
    function checkManualCallStatus() {
        fetch('/call-logs?limit=10')
            .then(response => response.json())
            .then(data => {
                // Look for recent calls to this contact
                const recentCalls = data.filter(call => {
                    const callTime = new Date(call.started_at).getTime();
                    // Check if the call was made after we started this task
                    // and matches our contact name
                    return callTime > startTime - 5000 && 
                           call.contact_name.includes(contactText);
                });
                
                if (recentCalls.length === 0) {
                    // No calls found yet, check if we've been waiting too long
                    if (Date.now() - startTime > 20000) {
                        // It's been too long, assume the call failed to initiate
                        TaskManager.failTask(taskId, `Call to ${contactText} failed to initiate`);
                    } else {
                        // Still waiting for the call to appear in logs
                        TaskManager.updateTaskProgress(taskId, 15, 'Preparing to dial...');
                        setTimeout(checkManualCallStatus, 2000);
                    }
                    return;
                }
                
                // We found a matching call
                const call = recentCalls[0]; // Use the most recent one
                
                // Check call status
                if (call.status === 'completed') {
                    // Log progress steps
                    TaskManager.addLogEntry(taskId, `Call connected successfully`);
                    TaskManager.addLogEntry(taskId, `Message delivered to ${contactText}`);
                    
                    // If there was a DTMF response
                    if (call.digits) {
                        TaskManager.addLogEntry(taskId, `Recipient pressed button ${call.digits} in response`);
                    }
                    
                    TaskManager.completeTask(taskId, `Call to ${contactText} completed successfully`);
                } else if (call.status === 'no-answer' || call.status === 'error') {
                    // Log failure details
                    if (call.status === 'no-answer') {
                        TaskManager.addLogEntry(taskId, `Call was not answered by ${contactText}`);
                    } else {
                        TaskManager.addLogEntry(taskId, `Call failed due to an error: ${call.status}`);
                    }
                    
                    TaskManager.failTask(taskId, `Call to ${contactText} failed: ${call.status}`);
                } else if (call.status === 'initiated') {
                    // Call is still in progress
                    if (lastStage !== 'connected') {
                        TaskManager.addLogEntry(taskId, `Call connected, delivering voice message...`);
                        lastStage = 'connected';
                    }
                    
                    TaskManager.updateTaskProgress(taskId, 50, 'Call connected, delivering message...');
                    setTimeout(checkManualCallStatus, 3000);
                } else {
                    // Some other status
                    TaskManager.addLogEntry(taskId, `Call status updated: ${call.status}`);
                    TaskManager.updateTaskProgress(taskId, 30, `Call status: ${call.status}`);
                    setTimeout(checkManualCallStatus, 2000);
                }
            })
            .catch(error => {
                console.error("Error checking call logs:", error);
                // Error fetching logs, check again after a delay
                setTimeout(checkManualCallStatus, 3000);
            });
    }
    
    // Start monitoring
    setTimeout(() => {
        TaskManager.updateTaskProgress(taskId, 20, 'Dialing...');
        checkManualCallStatus();
    }, 1000);
}

// Add demo functions for testing the task progress window
window.demoTaskProgress = {
    smsTask: function() {
        const taskId = TaskManager.trackSmsTask('Demo SMS Task', 25);
        monitorSmsProgress(taskId, 'group', 'Demo Group');
    },
    
    callTask: function() {
        const taskId = TaskManager.trackCallTask('Demo Call Task', 'Demo Group');
        monitorCallProgress(taskId, 'Test Emergency Message', 'Emergency Response Team');
    },
    
    importTask: function() {
        const taskId = TaskManager.trackImportTask('Demo Import', 'CSV', 150);
        
        let progress = 0;
        const interval = setInterval(() => {
            progress += 10;
            if (progress > 100) {
                clearInterval(interval);
                TaskManager.completeTask(taskId, 'Imported 150 contacts successfully');
            } else {
                TaskManager.updateTaskProgress(taskId, progress, `Imported ${Math.floor(progress * 1.5)} of 150 contacts`);
            }
        }, 800);
    },
    
    failedTask: function() {
        const taskId = TaskManager.createTask('Demo Failed Task', 'other', 'Initializing...');
        TaskManager.startTask(taskId);
        
        setTimeout(() => {
            TaskManager.updateTaskProgress(taskId, 35, 'Processing data...');
            
            setTimeout(() => {
                TaskManager.failTask(taskId, 'Operation failed: Database connection error');
            }, 2000);
        }, 1500);
    }
};