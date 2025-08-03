"""Environment variable validation for GDial application.

This module ensures that all required environment variables are set before
the application starts, preventing runtime failures due to missing configuration.
"""
import os
import sys
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class EnvironmentValidator:
    """Validates required environment variables at application startup."""
    
    # Critical variables required for all environments
    REQUIRED_VARS = [
        "SECRET_KEY",
        "TWILIO_ACCOUNT_SID", 
        "TWILIO_AUTH_TOKEN",
        "TWILIO_FROM_NUMBER"
    ]
    
    # Additional variables required in production
    PRODUCTION_REQUIRED = [
        "DATABASE_URL",
        "RABBITMQ_URL",
        "PUBLIC_URL"
    ]
    
    # Variables that should not have default/example values
    FORBIDDEN_VALUES = {
        "SECRET_KEY": [
            "a_very_secret_key_needs_to_be_set_in_env_for_production",
            "your_secret_key_here",
            "change_me",
            "secret"
        ]
    }
    
    @classmethod
    def validate_startup(cls) -> None:
        """Validate all required environment variables at startup.
        
        Exits the application with error code 1 if validation fails.
        """
        missing_vars = []
        invalid_vars = []
        
        # Check required variables
        for var in cls.REQUIRED_VARS:
            value = os.getenv(var)
            if not value:
                missing_vars.append(var)
            elif var in cls.FORBIDDEN_VALUES:
                if value in cls.FORBIDDEN_VALUES[var]:
                    invalid_vars.append(f"{var} (using default/example value)")
        
        # Check production-specific variables
        if os.getenv("ENVIRONMENT") == "production":
            for var in cls.PRODUCTION_REQUIRED:
                if not os.getenv(var):
                    missing_vars.append(var)
        
        # Report validation results
        if missing_vars or invalid_vars:
            print("❌ ENVIRONMENT VALIDATION FAILED")
            print("=" * 50)
            
            if missing_vars:
                print("\n🚫 Missing required environment variables:")
                for var in missing_vars:
                    print(f"   - {var}")
            
            if invalid_vars:
                print("\n⚠️  Invalid environment variable values:")
                for var in invalid_vars:
                    print(f"   - {var}")
            
            print("\n📋 Setup Instructions:")
            print("1. Copy .env.example to .env")
            print("2. Fill in all required values")
            print("3. Restart the application")
            print("\nFor more information, see the README.md file.")
            
            logger.error("Environment validation failed. Application cannot start.")
            sys.exit(1)
        
        print("✅ Environment validation passed")
        logger.info("All required environment variables are properly configured")
    
    @classmethod
    def get_missing_vars(cls) -> List[str]:
        """Get list of missing required variables without exiting.
        
        Returns:
            List of missing variable names
        """
        missing_vars = []
        
        for var in cls.REQUIRED_VARS:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if os.getenv("ENVIRONMENT") == "production":
            for var in cls.PRODUCTION_REQUIRED:
                if not os.getenv(var):
                    missing_vars.append(var)
        
        return missing_vars
    
    @classmethod
    def validate_variable(cls, var_name: str, value: str) -> bool:
        """Validate a specific environment variable.
        
        Args:
            var_name: Name of the environment variable
            value: Value to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not value:
            return False
        
        if var_name in cls.FORBIDDEN_VALUES:
            return value not in cls.FORBIDDEN_VALUES[var_name]
        
        return True
