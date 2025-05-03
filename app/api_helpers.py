"""Helper functions for the API endpoints."""
import logging
import json
import uuid
from fastapi import BackgroundTasks, Depends, HTTPException, Request
from sqlmodel import Session

from app.database import get_session
from app.services.sms_service import SmsService
from app.services.call_service import CallService

logger = logging.getLogger(__name__)

async def send_sms_messages(
    request: Request,
    background_tasks: BackgroundTasks,
    session: Session
):
    """
    Parse request parameters and send SMS messages.
    
    Args:
        request: The HTTP request
        background_tasks: FastAPI background tasks
        session: Database session
        
    Returns:
        Dict with response details
    """
    # Extract parameters from query string
    params = dict(request.query_params)
    logger.info(f"SMS trigger parameters: {params}")
    
    # Initialize SMS service
    sms_service = SmsService(session)
    
    # Get required message_id parameter
    if 'message_id' not in params:
        raise HTTPException(status_code=400, detail="message_id is required")
    
    try:
        message_id = params['message_id']
        contacts_param = params.get('contacts')
        group_id_param = params.get('group_id')
        
        # Verify at least one recipient type
        if not contacts_param and not group_id_param:
            raise HTTPException(status_code=400, detail="Either contacts or group_id must be provided")
        
        # Parse contacts parameter if provided
        contact_list = None
        if contacts_param:
            try:
                import json
                contact_list = json.loads(contacts_param)
                if not isinstance(contact_list, list):
                    raise ValueError("contacts must be a JSON array")
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON format for contacts parameter")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error processing contacts: {str(e)}")
        
        # Parse group_id parameter if provided
        group_id = None
        if group_id_param:
            try:
                group_id = group_id_param
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid group_id format: {str(e)}")
        
        # Validate the UUID format but keep the original format (string or UUID)
        try:
            if isinstance(message_id, str):
                # Just validate the UUID format, but keep as string
                uuid_obj = uuid.UUID(message_id)
                logger.debug(f"Valid UUID string format for message_id: {message_id}")
            elif isinstance(message_id, uuid.UUID):
                # Already a UUID object, no need to convert
                logger.debug(f"message_id is already a UUID object: {message_id}")
            else:
                raise ValueError(f"Unexpected type for message_id: {type(message_id)}")
                
        except ValueError as e:
            logger.error(f"Invalid message_id format: {message_id}, error: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid message_id format: {str(e)}")
            
        # Convert group_id string to UUID if needed
        if group_id and isinstance(group_id, str):
            try:
                group_id = uuid.UUID(group_id)
            except ValueError as e:
                logger.error(f"Invalid group_id format: {group_id}, error: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Invalid group_id format: {str(e)}")
                
        # Validate contact_ids UUID format
        if contact_list:
            valid_contacts = []
            for cid in contact_list:
                try:
                    if isinstance(cid, str):
                        # Validate format but keep as string
                        uuid_obj = uuid.UUID(cid)
                        valid_contacts.append(cid)
                    else:
                        valid_contacts.append(cid)
                except ValueError as e:
                    logger.warning(f"Skipping invalid contact ID format: {cid}, error: {str(e)}")
                    
            if not valid_contacts:
                logger.error("No valid contact IDs found in the provided list")
                raise HTTPException(status_code=400, detail="No valid contact IDs provided")
                
            contact_list = valid_contacts
            logger.debug(f"Validated {len(contact_list)} contact IDs")
        
        # Add the SMS sending task to background tasks
        background_tasks.add_task(
            sms_service.send_message_to_contacts,
            message_id=message_id,
            contact_ids=contact_list,
            group_id=group_id
        )
        
        # Prepare response
        if contact_list:
            recipient_count = len(contact_list)
            recipient_type = "specific contacts"
        elif group_id:
            # Note: We could query the database to get the exact count,
            # but that would add overhead. For now, we'll use a general message.
            recipient_count = "multiple"
            recipient_type = "group"
        else:
            recipient_count = 0
            recipient_type = "unknown"
            
        # Build response
        response_detail = f"SMS sending initiated to {recipient_count} {recipient_type}"
        
        return {
            "detail": response_detail,
            "sms_count": recipient_count if isinstance(recipient_count, int) else 0
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in send_sms_messages: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

async def send_custom_sms_messages(
    request: Request,
    background_tasks: BackgroundTasks,
    session: Session
):
    """
    Parse request for custom SMS and send/schedule messages.
    
    Args:
        request: The HTTP request
        background_tasks: FastAPI background tasks
        session: Database session
        
    Returns:
        Dict with response details
    """
    # Initialize SMS service
    sms_service = SmsService(session)
    
    try:
        # Check if we have query parameters or a JSON body
        params = dict(request.query_params)
        
        if params and len(params) > 0:
            logger.debug(f"Processing custom SMS from query parameters: {params}")
            # Extract parameters from query string
            message_id = params.get('message_id')
            message_content = params.get('message_content')
            
            # Handle contact_id or recipients
            contact_id = params.get('contact_id')
            recipients = params.get('recipients')
            
            # Convert single contact_id to recipients list if provided
            if contact_id and not recipients:
                recipients = [contact_id]
            elif recipients and isinstance(recipients, str):
                try:
                    recipients = json.loads(recipients)
                except json.JSONDecodeError:
                    # If not valid JSON, treat as a single ID
                    recipients = [recipients]
                    
            group_id = params.get('group_id')
            save_as_template = params.get('save_as_template', 'false').lower() == 'true'
            template_name = params.get('template_name')
            schedule_time = params.get('schedule_time')
            retry_count = int(params.get('retry_count', '0'))
            retry_delay_minutes = int(params.get('retry_delay_minutes', '30'))
        else:
            # Try to read JSON body
            try:
                body = await request.json()
                logger.debug(f"Processing custom SMS from JSON body")
                
                # Extract parameters
                message_id = body.get('message_id')
                message_content = body.get('message_content')
                recipients = body.get('recipients')
                group_id = body.get('group_id')
                save_as_template = body.get('save_as_template', False)
                template_name = body.get('template_name')
                schedule_time = body.get('schedule_time')
                retry_count = body.get('retry_count', 0)
                retry_delay_minutes = body.get('retry_delay_minutes', 30)
            except json.JSONDecodeError:
                # Empty or invalid body
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid request: Please provide parameters either in query string or JSON body"
                )
        
        # Validate required parameters
        if not message_id and not message_content:
            raise HTTPException(status_code=400, detail="Either message_id or message_content must be provided")
            
        if not recipients and not group_id:
            raise HTTPException(status_code=400, detail="Either recipients or group_id must be provided")
            
        if save_as_template and not template_name:
            raise HTTPException(status_code=400, detail="template_name is required when save_as_template is true")
            
        # Add the SMS sending task to background tasks
        background_tasks.add_task(
            sms_service.send_custom_sms,
            message_id=message_id,
            message_content=message_content,
            contact_list=recipients,
            group_id=group_id,
            save_as_template=save_as_template,
            template_name=template_name,
            schedule_time=schedule_time,
            retry_count=retry_count,
            retry_delay_minutes=retry_delay_minutes
        )
        
        # Prepare response
        if schedule_time:
            return {
                "detail": f"SMS scheduled for delivery at {schedule_time}",
                "status": "scheduled"
            }
        else:
            # Immediate sending
            if recipients:
                recipient_count = len(recipients)
                recipient_type = "specific contacts"
            elif group_id:
                recipient_count = "multiple"
                recipient_type = "group"
            else:
                recipient_count = 0
                recipient_type = "unknown"
                
            return {
                "detail": f"SMS sending initiated to {recipient_count} {recipient_type}",
                "status": "sending"
            }
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in send_custom_sms_messages: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

async def make_calls(
    request: Request,
    background_tasks: BackgroundTasks,
    session: Session
):
    """
    Parse request and initiate calls.
    
    Args:
        request: The HTTP request
        background_tasks: FastAPI background tasks
        session: Database session
        
    Returns:
        Dict with response details
    """
    # Initialize Call service
    call_service = CallService(session)
    
    # Extract parameters from query string
    params = dict(request.query_params)
    logger.info(f"Call trigger parameters: {params}")
    
    try:
        # Extract required parameters
        if 'message_id' not in params:
            raise HTTPException(status_code=400, detail="message_id is required")
            
        message_id = params['message_id']
        contacts_param = params.get('contacts')
        group_id_param = params.get('group_id')
        call_run_name = params.get('call_run_name', 'Emergency Call Run')
        call_run_description = params.get('call_run_description', 'Initiated from API')
        
        # Verify at least one recipient type
        if not contacts_param and not group_id_param:
            raise HTTPException(status_code=400, detail="Either contacts or group_id must be provided")
        
        # Parse contacts parameter if provided
        contact_list = None
        if contacts_param:
            try:
                import json
                contact_list = json.loads(contacts_param)
                if not isinstance(contact_list, list):
                    raise ValueError("contacts must be a JSON array")
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON format for contacts parameter")
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error processing contacts: {str(e)}")
        
        # Parse group_id parameter if provided
        group_id = None
        if group_id_param:
            try:
                group_id = group_id_param
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid group_id format: {str(e)}")
        
        # Add the call task to background tasks
        background_tasks.add_task(
            call_service.dial_contacts,
            contacts=contact_list,
            group_id=group_id,
            message_id=message_id,
            call_run_name=call_run_name,
            call_run_description=call_run_description
        )
        
        # Prepare response
        if contact_list:
            recipient_count = len(contact_list)
            recipient_type = "specific contacts"
        elif group_id:
            recipient_count = "multiple"
            recipient_type = "group"
        else:
            recipient_count = 0
            recipient_type = "unknown"
            
        # Build response
        response_detail = f"Call sending initiated to {recipient_count} {recipient_type}"
        
        return {
            "detail": response_detail,
            "call_count": recipient_count if isinstance(recipient_count, int) else 0,
            "status": "initiated"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in make_calls: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

async def make_manual_call(
    request: Request,
    background_tasks: BackgroundTasks,
    session: Session
):
    """
    Make a manual call to a specific contact.
    
    Args:
        request: The HTTP request
        background_tasks: FastAPI background tasks
        session: Database session
        
    Returns:
        Dict with response details
    """
    # Initialize Call service
    call_service = CallService(session)
    
    try:
        # Read request body
        body = await request.json()
        
        # Extract required parameters
        contact_id = body.get('contact_id')
        message_id = body.get('message_id')
        phone_id = body.get('phone_id')
        call_run_id = body.get('call_run_id')
        
        # Validate required parameters
        if not contact_id:
            raise HTTPException(status_code=400, detail="contact_id is required")
            
        if not message_id:
            raise HTTPException(status_code=400, detail="message_id is required")
        
        # Add the call task to background tasks
        background_tasks.add_task(
            call_service.make_manual_call,
            contact_id=contact_id,
            message_id=message_id,
            phone_id=phone_id,
            call_run_id=call_run_id
        )
        
        return {
            "detail": "Manual call initiated",
            "contact_id": contact_id,
            "message_id": message_id,
            "status": "initiated"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in make_manual_call: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")