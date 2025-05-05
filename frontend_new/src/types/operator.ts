/**
 * Represents the possible states a contact can be in during an alert.
 */
export type ContactStatus = 
  | 'PENDING'         // Waiting to be processed
  | 'SCHEDULED'       // Attempt postponed, will retry later
  | 'RINGING_PRIMARY'   // Actively calling the primary number
  | 'RINGING_SECONDARY' // Actively calling the secondary number (if primary failed)
  | 'NO_ANSWER'       // Attempt(s) made, no answer received
  | 'CONFIRMED'       // Contact successfully acknowledged the alert
  | 'MANUAL_NEEDED'   // Requires operator intervention (e.g., bad number, special instructions)
  | 'ERROR';            // An unexpected error occurred during processing

/**
 * Represents a single contact within a group.
 */
export interface Contact {
  id: string; // Unique identifier for the contact
  name: string; // Full name of the contact
  primaryPhone: string; // Primary phone number
  secondaryPhone?: string; // Optional secondary phone number
  status: ContactStatus; // Current status of the contact
  lastAttemptTime?: string; // ISO timestamp of the last call/SMS attempt
  nextAttemptTime?: string; // ISO timestamp for the next scheduled attempt (if applicable)
  notes?: string; // Any operator notes
}

/**
 * Represents a group of contacts.
 */
export interface Group {
  id: string; // Unique identifier for the group
  name: string; // Name of the group (e.g., 'Building Supervisors')
  contacts: Contact[]; // List of contacts belonging to this group
  // Potentially add other group-specific info here later
}
