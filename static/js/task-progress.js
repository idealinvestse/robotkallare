/**
 * Task Progress Tracking System
 * 
 * This module provides functionality to track and display progress of various asynchronous tasks
 * like SMS sending, call batches, etc. in a user-friendly window.
 */

// Task Manager Singleton
const TaskManager = (function() {
    // Private properties
    const tasks = new Map(); // Stores all tasks by ID
    let nextTaskId = 1;
    
    // DOM elements (will be initialized on load)
    let progressWindow;
    let taskList;
    let minimizeButton;
    let noTasksMessage;
    
    // Task statuses
    const STATUS = {
        PENDING: 'pending',
        RUNNING: 'running',
        COMPLETED: 'completed',
        FAILED: 'failed'
    };
    
    // Private methods
    function initialize() {
        progressWindow = document.getElementById('taskProgressWindow');
        taskList = document.getElementById('taskList');
        minimizeButton = document.getElementById('minimizeProgressWindow');
        noTasksMessage = taskList.querySelector('.no-tasks-message');
        
        // Set up event listeners
        minimizeButton.addEventListener('click', toggleMinimize);
        document.querySelector('.progress-window-header').addEventListener('click', function(e) {
            if (e.target !== minimizeButton) {
                toggleMinimize();
            }
        });
        
        // Initialize WebSocket for real-time updates if needed
        initializeWebSocketConnection();
    }
    
    function toggleMinimize(e) {
        if (e) e.stopPropagation();
        progressWindow.classList.toggle('minimized');
        
        // Update button text
        minimizeButton.textContent = progressWindow.classList.contains('minimized') ? '+' : '-';
    }
    
    function initializeWebSocketConnection() {
        // This could be implemented later to get real-time updates from the server
        // For now, we'll update progress manually or via polling
    }
    
    function createTaskElement(task) {
        const taskElement = document.createElement('div');
        taskElement.className = 'task-item';
        taskElement.id = `task-${task.id}`;
        
        // Generate the percentage text
        const percentText = task.indeterminate ? '' : `${task.progress}%`;
        
        taskElement.innerHTML = `
            <div class="task-header">
                <div class="task-title">${task.title}</div>
                <div class="task-status ${task.status}">${formatStatus(task.status)}</div>
            </div>
            <div class="task-progress-bar">
                <div class="task-progress-fill ${task.status} ${task.indeterminate ? 'indeterminate' : ''}" style="width: ${task.progress}%"></div>
                <div class="task-progress-text">${percentText}</div>
            </div>
            <div class="task-details">${task.details}</div>
            <div class="task-log">
                ${task.log.map(entry => `
                    <div class="task-log-entry">
                        <span class="task-log-timestamp">${formatTime(entry.time)}</span>
                        <span class="task-log-message">${entry.message}</span>
                    </div>
                `).join('')}
            </div>
            <div class="toggle-logs">Show more</div>
        `;
        
        // Add click event to toggle expanded state
        const toggleBtn = taskElement.querySelector('.toggle-logs');
        toggleBtn.addEventListener('click', function() {
            taskElement.classList.toggle('expanded');
            this.textContent = taskElement.classList.contains('expanded') ? 'Show less' : 'Show more';
        });
        
        return taskElement;
    }
    
    function formatTime(timestamp) {
        const date = new Date(timestamp);
        const hours = date.getHours().toString().padStart(2, '0');
        const minutes = date.getMinutes().toString().padStart(2, '0');
        const seconds = date.getSeconds().toString().padStart(2, '0');
        return `${hours}:${minutes}:${seconds}`;
    }
    
    function formatStatus(status) {
        switch (status) {
            case STATUS.PENDING: return 'Pending';
            case STATUS.RUNNING: return 'Running';
            case STATUS.COMPLETED: return 'Completed';
            case STATUS.FAILED: return 'Failed';
            default: return status;
        }
    }
    
    function updateTaskElement(task) {
        const taskElement = document.getElementById(`task-${task.id}`);
        if (!taskElement) return;
        
        // Update status
        const statusElement = taskElement.querySelector('.task-status');
        statusElement.className = `task-status ${task.status}`;
        statusElement.textContent = formatStatus(task.status);
        
        // Update progress bar
        const progressFill = taskElement.querySelector('.task-progress-fill');
        progressFill.className = `task-progress-fill ${task.status}`;
        
        if (task.indeterminate) {
            progressFill.classList.add('indeterminate');
        } else {
            progressFill.classList.remove('indeterminate');
            progressFill.style.width = `${task.progress}%`;
            
            // Update the percentage text
            const progressText = taskElement.querySelector('.task-progress-text');
            if (progressText) {
                progressText.textContent = `${task.progress}%`;
            }
        }
        
        // Update details
        taskElement.querySelector('.task-details').textContent = task.details;
        
        // Update logs
        const logContainer = taskElement.querySelector('.task-log');
        if (logContainer && task.log && task.log.length > 0) {
            // Only show the latest entries if we have too many
            const logsToShow = task.log.slice(-15); // Show last 15 logs max
            
            logContainer.innerHTML = logsToShow.map(entry => `
                <div class="task-log-entry">
                    <span class="task-log-timestamp">${formatTime(entry.time)}</span>
                    <span class="task-log-message">${entry.message}</span>
                </div>
            `).join('');
            
            // Scroll to bottom to show latest logs
            logContainer.scrollTop = logContainer.scrollHeight;
        }
    }
    
    function cleanupCompletedTasks() {
        const now = Date.now();
        
        // Remove completed tasks after 30 seconds
        for (const [id, task] of tasks.entries()) {
            // Handle completed or failed tasks
            if ((task.status === STATUS.COMPLETED || task.status === STATUS.FAILED) && 
                now - task.updatedAt > 30000) {
                removeTask(id);
            }
            
            // Add a failsafe for stalled tasks
            // If a task has been running for more than 2 minutes without updates, mark it as completed
            if (task.status === STATUS.RUNNING && 
                now - task.updatedAt > 120000) {
                task.status = STATUS.COMPLETED;
                task.progress = 100;
                task.details += " (Completed automatically after timeout)";
                task.updatedAt = now;
                updateTaskElement(task);
            }
            
            // If a task has been pending for more than 60 seconds, mark it as failed
            if (task.status === STATUS.PENDING && 
                now - task.createdAt > 60000) {
                task.status = STATUS.FAILED;
                task.details = "Task failed to start after 60 seconds";
                task.updatedAt = now;
                updateTaskElement(task);
            }
        }
    }
    
    function updateNoTasksMessage() {
        if (tasks.size === 0) {
            noTasksMessage.style.display = 'block';
        } else {
            noTasksMessage.style.display = 'none';
        }
    }
    
    // Public API
    return {
        init: function() {
            // Wait for DOM to be ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', initialize);
            } else {
                initialize();
            }
            
            // Set up timer to clean up completed tasks
            setInterval(cleanupCompletedTasks, 10000);
        },
        
        createTask: function(title, type, details = '') {
            const taskId = nextTaskId++;
            const task = {
                id: taskId,
                title: title,
                type: type, // 'sms', 'call', 'import', etc.
                status: STATUS.PENDING,
                progress: 0,
                details: details,
                indeterminate: false,
                createdAt: Date.now(),
                updatedAt: Date.now(),
                log: [] // Array to store log entries
            };
            
            // Add initial log entry
            task.log.push({
                time: task.createdAt,
                message: 'Task created: ' + title
            });
            
            tasks.set(taskId, task);
            
            // Create and append the task element
            taskList.appendChild(createTaskElement(task));
            updateNoTasksMessage();
            
            return taskId;
        },
        
        startTask: function(taskId) {
            const task = tasks.get(taskId);
            if (!task) return;
            
            task.status = STATUS.RUNNING;
            task.updatedAt = Date.now();
            
            // Add log entry
            task.log.push({
                time: task.updatedAt,
                message: 'Task started'
            });
            
            updateTaskElement(task);
        },
        
        updateTaskProgress: function(taskId, progress, details = null) {
            const task = tasks.get(taskId);
            if (!task) return;
            
            const previousProgress = task.progress;
            task.progress = Math.max(0, Math.min(100, progress));
            if (details !== null) {
                task.details = details;
            }
            task.updatedAt = Date.now();
            
            // Add log entry if progress changed significantly or details changed
            if (Math.abs(task.progress - previousProgress) >= 5 || details !== null) {
                task.log.push({
                    time: task.updatedAt,
                    message: details || `Progress: ${task.progress}%`
                });
            }
            
            updateTaskElement(task);
        },
        
        setTaskIndeterminate: function(taskId, isIndeterminate) {
            const task = tasks.get(taskId);
            if (!task) return;
            
            task.indeterminate = isIndeterminate;
            task.updatedAt = Date.now();
            
            // Add log entry
            if (isIndeterminate) {
                task.log.push({
                    time: task.updatedAt,
                    message: 'Processing task with indeterminate progress'
                });
            } else {
                task.log.push({
                    time: task.updatedAt,
                    message: `Switched to determinate progress: ${task.progress}%`
                });
            }
            
            updateTaskElement(task);
        },
        
        completeTask: function(taskId, details = null) {
            const task = tasks.get(taskId);
            if (!task) return;
            
            task.status = STATUS.COMPLETED;
            task.progress = 100;
            if (details !== null) {
                task.details = details;
            }
            task.updatedAt = Date.now();
            
            // Add log entry
            task.log.push({
                time: task.updatedAt,
                message: 'Task completed: ' + (details || 'Successfully completed')
            });
            
            updateTaskElement(task);
        },
        
        failTask: function(taskId, details = null) {
            const task = tasks.get(taskId);
            if (!task) return;
            
            task.status = STATUS.FAILED;
            if (details !== null) {
                task.details = details;
            }
            task.updatedAt = Date.now();
            
            // Add log entry
            task.log.push({
                time: task.updatedAt,
                message: 'Task failed: ' + (details || 'Unknown error')
            });
            
            updateTaskElement(task);
        },
        
        // New method to add a log entry without changing other properties
        addLogEntry: function(taskId, message) {
            const task = tasks.get(taskId);
            if (!task) return;
            
            task.log.push({
                time: Date.now(),
                message: message
            });
            
            updateTaskElement(task);
        },
        
        removeTask: function(taskId) {
            const task = tasks.get(taskId);
            if (!task) return;
            
            // Remove the task element
            const taskElement = document.getElementById(`task-${taskId}`);
            if (taskElement) {
                taskElement.remove();
            }
            
            // Remove from tasks map
            tasks.delete(taskId);
            updateNoTasksMessage();
        },
        
        // Convenience methods for specific task types
        trackSmsTask: function(title, recipientCount) {
            const taskId = this.createTask(title, 'sms', `Preparing to send ${recipientCount} messages...`);
            this.startTask(taskId);
            this.setTaskIndeterminate(taskId, true);
            return taskId;
        },
        
        trackCallTask: function(title, recipientCount) {
            const taskId = this.createTask(title, 'call', `Preparing to call ${recipientCount} contacts...`);
            this.startTask(taskId);
            this.setTaskIndeterminate(taskId, true);
            return taskId;
        },
        
        trackImportTask: function(title, fileType, recordCount = null) {
            let details = `Preparing to import ${fileType} file`;
            if (recordCount) {
                details += ` with ${recordCount} records`;
            }
            const taskId = this.createTask(title, 'import', details);
            this.startTask(taskId);
            this.setTaskIndeterminate(taskId, true);
            return taskId;
        }
    };
})();

// Initialize the task manager
TaskManager.init();

// Add to global scope for other scripts to use
window.TaskManager = TaskManager;