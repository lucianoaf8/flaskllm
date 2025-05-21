# Review Task List for Next Phase of Flask LLM API

*Exported on: 2025-05-20, 10:41:13 p.m.*

## User

Review the task v2 attached so you konw whats left to be completed.Following the guidelines and prompt procumentation and plan accoridngly. Coninue from the next task item.

## Claude

### Flask LLM API: Next Phase Implementation Planning

#### Overview

Based on your task list v2, I can see we've made excellent progress on the core implementation of the Flask LLM API. The fundamental components are in place, including the application structure, authentication, error handling, LLM integration, and initial tests. Now it's time to move forward with the next set of tasks, focusing on API documentation, PythonAnywhere deployment, and client-side integration.

Let's create a detailed implementation plan for these next tasks, aligning with the project guidelines and documentation.

#### Implementation Plan for Remaining Tasks

##### 1. API Documentation

Swagger/OpenAPI documentation will provide an interactive interface for exploring and testing your API. This is particularly valuable for this project as it will make it easier to understand and use the API from client applications like Excel with Office Scripts.

Let's implement this using Flask-RESTX, which provides integrated Swagger UI:

Let's create a dedicated documentation structure that can be hosted alongside the API:

Create the necessary template files in a templates/docs directory with HTML documentation about your API.

`templates/docs`Let's create a dedicated endpoint that provides examples of how to use the API:

##### 2. PythonAnywhere Deployment

Now let's prepare for deployment to PythonAnywhere by creating the necessary configuration files and documentation.

Create a PythonAnywhere-specific WSGI file:

Let's create a comprehensive deployment guide:

- Navigate to the project directory:
bashcd flaskllm
##### 4. Set Up Virtual Environment

- Create a virtual environment:
bashpython3 -m venv venv
- Activate the virtual environment:
bashsource venv/bin/activate
- Install dependencies:
bashpip install -r requirements.txt
##### 5. Configure Environment Variables

- Create a .env file in your project directory:
bashtouch .env
`.env`- Open the file with the editor and add your environment variables:
ENVIRONMENT=production
DEBUG=False
API_TOKEN=your_secure_random_token
ALLOWED_ORIGINS=*
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4
REQUEST_TIMEOUT=30
MAX_PROMPT_LENGTH=4000
RATE_LIMIT_ENABLED=True
RATE_LIMIT=60
- Set proper permissions to protect your API keys:
bashchmod 600 .env
##### 6. Configure the WSGI File

- Go back to the Web tab in your dashboard
- Look for the WSGI configuration file path and click to edit it
- Replace the contents with the code from pythonanywhere_wsgi.py, but update the paths to match your username and setup
`pythonanywhere_wsgi.py`- Save the file
##### 7. Configure Static Files (If Needed)

- In the Web tab, scroll down to "Static files"
- Add a new mapping:

URL: /static/
Directory: /home/yourusername/flaskllm/static/
- URL: /static/
`/static/`- Directory: /home/yourusername/flaskllm/static/
`/home/yourusername/flaskllm/static/`##### 8. Set Up Log Files

- In the Web tab, note the path to your error log
- This will be useful for debugging any issues
##### 9. Reload Your Web App

- Click the "Reload" button in the Web tab
- Wait for the app to restart
##### 10. Test Your Deployment

- Test the health check endpoint:
https://yourusername.pythonanywhere.com/api/v1/health
- If everything is working, you should see a success response
#### Troubleshooting

##### Common Issues

- Import Errors:

Check that your virtual environment is set up correctly
Verify all dependencies are installed
- Check that your virtual environment is set up correctly
- Verify all dependencies are installed
- Authentication Failures:

Check that your .env file has the correct API_TOKEN
- Check that your .env file has the correct API_TOKEN
`.env`- LLM API Errors:

Verify your LLM provider API keys
Check for rate limits or service disruptions
- Verify your LLM provider API keys
- Check for rate limits or service disruptions
##### Viewing Logs

To view application logs:

- Navigate to the "Files" tab
- Look for log files in the specified directory from the Web tab
- Use tail -f in a Bash console to watch logs in real-time
`tail -f`##### Getting Help

If you encounter issues not covered here, check:

- PythonAnywhere's help documentation
- Flask documentation
- Project issues in the GitHub repository
Let's create comprehensive documentation for Excel integration:

=processPrompt(A1, "summary", "excel")

##### 4. Next Tasks for Implementation

After completing the above tasks, you'll be ready to move on to:

- Enhanced Functionality

Implement caching for frequent requests
Add prompt templates
Set up streaming responses
- Implement caching for frequent requests
- Add prompt templates
- Set up streaming responses
- Monitoring and Analytics

Configure usage tracking
Implement cost monitoring
Set up error alerting
- Configure usage tracking
- Implement cost monitoring
- Set up error alerting
#### Implementation Strategy

Here's a recommended implementation strategy:

- Start with API Documentation

This will make testing and understanding your API easier for future development
The Swagger UI provides immediate visual feedback on your API design
- This will make testing and understanding your API easier for future development
- The Swagger UI provides immediate visual feedback on your API design
- Prepare Deployment Configuration

Configure all necessary files for PythonAnywhere
Test deployment on a development branch before going live
- Configure all necessary files for PythonAnywhere
- Test deployment on a development branch before going live
- Create Client Integration Examples

Develop and test the Office Script for Excel integration
Document usage patterns for end users
- Develop and test the Office Script for Excel integration
- Document usage patterns for end users
- Add Enhanced Features

Implement caching and other performance optimizations
Add more sophisticated prompt handling capabilities
- Implement caching and other performance optimizations
- Add more sophisticated prompt handling capabilities
#### Security Considerations

Throughout these implementations, maintain focus on security:

- API Documentation: Ensure sensitive information is not exposed in examples
- Deployment: Use secure environment variable handling for API keys
- Client Integration: Store API tokens securely and implement proper error handling
- Enhanced Features: Apply appropriate access controls to cached data
#### Testing Approach

For each component:

- API Documentation: Verify all endpoints are correctly documented and examples work as expected
- PythonAnywhere Deployment: Test the deployed application thoroughly, particularly authentication and error handling
- Office Scripts Integration: Test with various input types and error conditions
- Enhanced Features: Verify performance improvements and ensure they don't introduce security vulnerabilities
#### Conclusion

This implementation plan addresses the next set of tasks in your FlaskLLM API project, focusing on user-facing documentation, deployment, and client integration. By following this plan, you'll create a well-documented, properly deployed API that's ready for integration with Excel and other client applications.

Would you like me to dive deeper into any specific component of this plan or start implementing a particular section first?



## User

Output the updated task list with the completed tests checked.

## Claude

### FlaskLLM API - Updated Task List

#### 1. Project Planning & Architecture

- Define project requirements and goals
- Design overall architecture
- Create project guidelines document
- Create project documentation
- Define API contract and endpoints
- Design database schema (if applicable)
- Choose technology stack and dependencies
- Define development and deployment workflow
#### 2. Environment Setup

- Create GitHub repository
- Set up development environment
- Configure Python virtual environment
- Create initial project structure
- Set up Git hooks for linting and formatting
- Initialize config files (.env.example, .gitignore)
- Create requirements.txt with all dependencies
#### 3. Core Implementation

##### 3.1. Project Structure

- Set up package structure (api, core, llm, utils, tests)
- Create init.py files for all packages
##### 3.2. Core Components

- Implement app.py (application factory)
- Implement wsgi.py (WSGI entry point)
- Implement core/config.py (configuration management)
- Implement core/logging.py (logging setup)
- Implement core/exceptions.py (custom exceptions)
- Implement core/auth.py (authentication)
- Implement core/middleware.py (middleware setup)
##### 3.3. API Components

- Implement api/init.py (API setup)
- Implement api/v1/init.py (API v1 blueprint)
- Implement api/v1/routes.py (API routes)
- Implement api/v1/schemas.py (request/response schemas)
- Implement api/v1/validators.py (input validation - included in schemas.py)
##### 3.4. LLM Integration

- Implement llm/init.py
- Implement llm/factory.py (LLM provider factory)
- Implement llm/openai_handler.py (OpenAI integration)
- Implement llm/anthropic_handler.py (Claude integration)
##### 3.5. Utilities

- Implement utils/init.py
- Implement utils/rate_limiter.py (rate limiting)
- Implement utils/security.py (security helpers)
- Implement utils/validation.py (general validators - included in other modules)
#### 4. Testing

##### 4.1. Test Setup

- Configure pytest in conftest.py
- Set up test fixtures and utilities in tests/conftest.py
- Create test environment configuration
##### 4.2. Unit Tests

- Implement tests for core/config.py
- Implement tests for core/auth.py
- Implement tests for core/exceptions.py
- Implement tests for llm/factory.py
- Implement tests for llm/openai_handler.py
- Implement tests for api/v1/validators.py
- Implement tests for utils/rate_limiter.py
##### 4.3. Integration Tests

- Implement tests for authentication flow
- Implement tests for API routes
- Implement tests for error handling
- Implement tests for rate limiting
- Implement tests for LLM integration
- Implement end-to-end API tests
##### 4.4. Test Automation

- Set up test running script
- Set up GitHub Actions for CI/CD
- Configure test coverage reporting
- Set up pre-commit hooks for running tests
#### 5. Security Review

- Perform security audit of authentication mechanism
- Review input validation and sanitization
- Check for sensitive data exposure
- Verify proper CORS configuration
- Test rate limiting effectiveness
- Review secure headers configuration
- Audit token management
- Check dependency vulnerabilities
#### 6. Performance Optimization

- Implement caching for frequent requests
- Configure connection pooling
- Optimize response serialization
- Implement request timeouts
- Configure proper logging levels for production
- Add request compression (if needed)
- Optimize database queries (if applicable)
#### 7. Documentation

##### 7.1. Code Documentation

- Document all modules with docstrings
- Include type hints for all functions
- Add inline comments for complex logic
- Create module-level documentation
##### 7.2. Project Documentation

- Create README.md with project overview
- Create CONTRIBUTING.md guidelines
- Develop API documentation with examples
- Document environment variables and configuration
- Create deployment guide
- Create troubleshooting guide
##### 7.3. API Documentation

- Set up Swagger/OpenAPI documentation
- Generate API reference documentation
- Create API usage examples
#### 8. PythonAnywhere Deployment

##### 8.1. Preparation

- Create PythonAnywhere account
- Configure PythonAnywhere web app
- Set up virtual environment on PythonAnywhere
- Upload or clone code to PythonAnywhere
##### 8.2. Configuration

- Set up WSGI configuration file
- Configure environment variables
- Configure static files (if applicable)
- Set up proper file permissions
- Configure log rotation
##### 8.3. Deployment

- Install dependencies on PythonAnywhere
- Test deployment locally before activating
- Activate web app
- Verify health endpoint
- Test API functionality
- Set up scheduled tasks (if needed)
##### 8.4. Post-Deployment

- Set up monitoring
- Configure error alerting
- Test failover procedures
- Document deployment process
- Create maintenance procedures
#### 9. Office Scripts Integration

##### 9.1. Excel Integration

- Create Office Script for Excel
- Implement API client in TypeScript
- Add error handling and retries
- Test with different prompt types
- Document Office Script usage
##### 9.2. Power Automate Integration (Optional)

- Create Power Automate flow
- Configure authentication
- Set up error handling
- Test integration with Excel
- Document Power Automate setup
#### 10. External Integrations

##### 10.1. Google Calendar Integration

- Set up Google Cloud Project

 Create new project in Google Cloud Console
 Enable Google Calendar API
 Configure OAuth consent screen
 Create OAuth 2.0 credentials
 Download and secure credentials JSON file
- Create new project in Google Cloud Console
- Enable Google Calendar API
- Configure OAuth consent screen
- Create OAuth 2.0 credentials
- Download and secure credentials JSON file
- Implement Authentication Flow

 Create auth module for Google OAuth
 Implement token acquisition and refresh logic
 Set up secure token storage
 Create authentication callback endpoint
- Create auth module for Google OAuth
- Implement token acquisition and refresh logic
- Set up secure token storage
- Create authentication callback endpoint
- Core Calendar Implementation

 Create integrations/google_calendar.py module
 Implement calendar service client
 Create event mapping functions (convert LLM output to calendar events)
 Implement event creation/modification methods
 Add timezone handling
- Create integrations/google_calendar.py module
- Implement calendar service client
- Create event mapping functions (convert LLM output to calendar events)
- Implement event creation/modification methods
- Add timezone handling
- API Extension

 Create /api/v1/calendar endpoint
 Update schemas.py with calendar event models
 Implement intelligent routing from webhook to calendar
 Add calendar-specific validation
- Create /api/v1/calendar endpoint
- Update schemas.py with calendar event models
- Implement intelligent routing from webhook to calendar
- Add calendar-specific validation
- Testing & Validation

 Create unit tests for calendar functionality
 Set up integration tests with Google Calendar API
 Test event creation with various input formats
 Implement error handling for calendar-specific issues
- Create unit tests for calendar functionality
- Set up integration tests with Google Calendar API
- Test event creation with various input formats
- Implement error handling for calendar-specific issues
- Documentation & Configuration

 Document calendar integration process
 Add Google Calendar specific environment variables
 Create calendar integration usage examples
 Document OAuth scopes and permissions
- Document calendar integration process
- Add Google Calendar specific environment variables
- Create calendar integration usage examples
- Document OAuth scopes and permissions
##### 10.2. beforesunset.ai Integration (Future)

- Research beforesunset.ai API capabilities
- Design integration approach
- Implement authentication
- Create task mapping functionality
- Add beforesunset.ai endpoint
##### 10.3. Enhanced Functionality

- Add support for streaming responses
- Implement prompt templates
- Add support for custom LLM parameters
- Implement file processing capabilities
- Add support for conversation history
- Implement user-specific customizations
##### 10.4. Monitoring and Analytics

- Set up usage tracking
- Implement cost monitoring for LLM usage
- Create performance dashboards
- Set up error tracking and alerting
- Implement user activity logging
#### 11. Maintenance and Updates

##### 11.1. Ongoing Maintenance

- Schedule regular dependency updates
- Implement token rotation procedure
- Set up automated backups
- Create incident response procedures
- Develop scaling plan for increased usage
##### 11.2. Version Management

- Define versioning strategy for API
- Document deprecation process
- Create release notes template
- Set up semantic versioning
- Plan for backward compatibility
#### 12. Final Review

- Conduct final security review
- Perform load testing
- Complete documentation review
- Verify all tests pass
- Create user acceptance test plan
- Finalize deployment checklist


## User

Provide this:10.1. Google Calendar Integration

 Set up Google Cloud Project

 Create new project in Google Cloud Console
 Enable Google Calendar API
 Configure OAuth consent screen
 Create OAuth 2.0 credentials
 Download and secure credentials JSON file


 Implement Authentication Flow

 Create auth module for Google OAuth
 Implement token acquisition and refresh logic
 Set up secure token storage
 Create authentication callback endpoint


 Core Calendar Implementation

 Create integrations/google_calendar.py module
 Implement calendar service client
 Create event mapping functions (convert LLM output to calendar events)
 Implement event creation/modification methods
 Add timezone handling


 API Extension

 Create /api/v1/calendar endpoint
 Update schemas.py with calendar event models
 Implement intelligent routing from webhook to calendar
 Add calendar-specific validation


 Testing & Validation

 Create unit tests for calendar functionality
 Set up integration tests with Google Calendar API
 Test event creation with various input formats
 Implement error handling for calendar-specific issues


 Documentation & Configuration

 Document calendar integration process
 Add Google Calendar specific environment variables
 Create calendar integration usage examples
 Document OAuth scopes and permissions

## Claude

### Google Calendar Integration for FlaskLLM API

#### Overview

We'll be integrating Google Calendar with the FlaskLLM API to allow the API to create, update, and manage calendar events based on natural language processing. This integration will enable features like automatically scheduling meetings from email or chat summaries, creating calendar events from meeting notes, and updating event details based on follow-up communications.

#### Architecture

The Google Calendar integration will consist of several key components:

- Google OAuth Authentication Module: Handles authentication and authorization with Google's APIs
- Calendar Service Client: Interfaces with the Google Calendar API
- Event Mapping Logic: Converts LLM outputs to structured calendar events
- API Endpoints: New endpoints for calendar operations
- Persistence Layer: Securely stores OAuth tokens and user preferences
Here's how these components will work together:

#### Implementation

##### 1. Set up Google Cloud Project

##### 2. Implement Authentication Flow

This is implemented in the GoogleOAuth class above, with the get_credentials method handling refresh logic when tokens expire.

`GoogleOAuth``get_credentials`The GoogleTokenStorage class above provides a file-based storage implementation for development. For production, you'd want to enhance this with database storage and encryption:

`GoogleTokenStorage`##### 3. Core Calendar Implementation



## User

Continue

## Claude

The GoogleCalendarService class in the code above provides this functionality.

`GoogleCalendarService`The EventMapper class in the code above handles converting LLM output to calendar events.

`EventMapper`The GoogleCalendarService class includes methods for creating, updating, and deleting events.

`GoogleCalendarService`Timezone handling is implemented throughout the code using the pytz library.

`pytz`##### 4. API Extension

Calendar-specific validation is implemented in the CalendarEventSchema, CalendarEventTimeSchema, and CalendarEventAttendeeSchema classes above.

`CalendarEventSchema``CalendarEventTimeSchema``CalendarEventAttendeeSchema`##### 5. Testing & Validation



## User

Continue

## Claude

This is covered in the test_process_text_to_calendar test above, which tests the end-to-end flow of converting natural language to a calendar event.

`test_process_text_to_calendar`Error handling is implemented throughout the code with specific error types and HTTP status codes. The CalendarError exception is defined in core/exceptions.py:

`CalendarError``core/exceptions.py`##### 6. Documentation & Configuration

flaskllm/config/credentials/google_calendar_credentials.json

GOOGLE_CREDENTIALS_FILE=/path/to/google_calendar_credentials.json
DEFAULT_TIMEZONE=America/New_York

config/credentials/*.json

GET /api/v1/calendar/auth

GET /api/v1/calendar/events

Creates a new calendar event.

Headers:

- X-API-Token: API token for authentication
`X-API-Token`Request Body:

Response:

Process natural language text with the LLM and create a calendar event.

Headers:

- X-API-Token: API token for authentication
`X-API-Token`Request Body:

Response:

Revokes the application's access to Google Calendar.

Headers:

- X-API-Token: API token for authentication
`X-API-Token`Response:

#### Using the Webhook for Calendar Events

You can also create calendar events through the main webhook endpoint by specifying the type as calendar_event:

`calendar_event`Headers:

- X-API-Token: API token for authentication
`X-API-Token`Request Body:

Response:
Same as the /api/v1/calendar/process-text endpoint.

`/api/v1/calendar/process-text`#### Error Handling

The API returns appropriate error codes for different failure scenarios:

- 400 Bad Request: Invalid input or parsing errors
`400 Bad Request`- 401 Unauthorized: Authentication failure
`401 Unauthorized`- 403 Forbidden: Insufficient permissions to access the calendar
`403 Forbidden`- 404 Not Found: Calendar or event not found
`404 Not Found`- 500 Internal Server Error: Unexpected errors
`500 Internal Server Error`Example error response:

### Google Calendar Integration

GOOGLE_CREDENTIALS_FILE=/path/to/google_calendar_credentials.json
DEFAULT_TIMEZONE=America/New_York

### Optional: For secure token storage

GOOGLE_TOKEN_ENCRYPTION_KEY=your_secure_encryption_key_for_tokens



## User

Continue

## Claude

#### Additional Configuration Files

##### 1. Update core/exceptions.py with Calendar Error

`core/exceptions.py`##### 2. Update .gitignore for Calendar Credentials

`.gitignore`##### 3. Update requirements.txt

`requirements.txt`##### 4. Update config.py for Calendar Settings

`config.py`#### Conclusion

This implementation provides a comprehensive Google Calendar integration for the FlaskLLM API, allowing users to:

- Authenticate with Google Calendar
- Process natural language text to extract event details
- Create, update, and delete calendar events
- Manage calendar access
The code includes proper error handling, validation, and security measures, as well as thorough testing and documentation. The implementation follows best practices for OAuth authentication, including secure token storage and refresh logic.

By integrating with Google Calendar, the FlaskLLM API can now automatically schedule meetings and create events based on the content processed by the LLM, adding significant value to the application.
