PythonAnywhere deployment, and client-side integration.

Let's create a detailed implementation plan for these next tasks, aligning with the project guidelines and documentation.

## Implementation Plan for Remaining Tasks

### 1. API Documentation

#### A. Set up Swagger/OpenAPI Documentation

Swagger/OpenAPI documentation will provide an interactive interface for exploring and testing your API. This is particularly valuable for this project as it will make it easier to understand and use the API from client applications like Excel with Office Scripts.

Let's implement this using Flask-RESTX, which provides integrated Swagger UI:

```python
# api/v1/__init__.py
from flask import Blueprint
from flask_restx import Api

# Create blueprint
v1_blueprint = Blueprint('v1', __name__, url_prefix='/api/v1')

# Create API with Swagger documentation
api = Api(
    v1_blueprint,
    version='1.0',
    title='FlaskLLM API',
    description='A secure, scalable API for processing prompts with LLMs',
    doc='/docs',
    default='LLM',
    default_label='LLM API Operations',
    validate=True,
)
```

```python
# api/v1/routes.py
from flask import request, current_app
from flask_restx import Resource, fields

from . import api
from .schemas import PromptSchema, ResponseSchema
from core.auth import require_api_token
from llm.factory import get_llm_handler
from utils.rate_limiter import rate_limit

# Define models for Swagger documentation
prompt_model = api.model('Prompt', {
    'prompt': fields.String(required=True, description='The text to process', example='Summarize this meeting: we need to reduce hiring.'),
    'source': fields.String(required=False, description='Source of the prompt', enum=['email', 'meeting', 'document', 'chat', 'other'], example='meeting'),
    'language': fields.String(required=False, description='Target language code (ISO 639-1)', example='en'),
    'type': fields.String(required=False, description='Type of processing', enum=['summary', 'keywords', 'sentiment', 'entities', 'translation', 'custom'], example='summary')
})

response_model = api.model('Response', {
    'summary': fields.String(description='Processed response from LLM', example='The company plans to reduce hiring to cut costs.'),
    'processing_time': fields.Float(description='Time taken to process the request in seconds', example=1.25)
})

error_model = api.model('Error', {
    'error': fields.String(description='Error message'),
    'details': fields.String(description='Detailed explanation'),
    'code': fields.String(description='Error code')
})

# Register namespace
webhook_ns = api.namespace('webhook', description='Process prompts with LLM')

@webhook_ns.route('')
class Webhook(Resource):
    @webhook_ns.doc(security='apikey')
    @webhook_ns.expect(prompt_model)
    @webhook_ns.response(200, 'Success', response_model)
    @webhook_ns.response(400, 'Validation Error', error_model)
    @webhook_ns.response(401, 'Authentication Error', error_model)
    @webhook_ns.response(429, 'Rate Limit Exceeded', error_model)
    @webhook_ns.response(500, 'Server Error', error_model)
    @webhook_ns.response(502, 'LLM API Error', error_model)
    @require_api_token
    @rate_limit
    def post(self):
        """Process a prompt with the configured LLM provider"""
        start_time = time.time()

        # Validate input
        try:
            schema = PromptSchema()
            data = schema.load(request.json)
        except ValidationError as e:
            return {
                'error': 'Validation Error',
                'details': str(e),
                'code': 'VALIDATION_ERROR'
            }, 400

        # Process the prompt
        try:
            llm_handler = get_llm_handler()
            result = llm_handler.process_prompt(
                data['prompt'],
                data.get('source'),
                data.get('language'),
                data.get('type')
            )

            # Calculate processing time
            processing_time = time.time() - start_time

            # Return result
            return {
                'summary': result,
                'processing_time': round(processing_time, 2)
            }
        except Exception as e:
            current_app.logger.error(f"Error processing prompt: {str(e)}", exc_info=True)
            return {
                'error': 'LLM API Error',
                'details': str(e),
                'code': 'LLM_API_ERROR'
            }, 502
```

#### B. API Reference Documentation

Let's create a dedicated documentation structure that can be hosted alongside the API:

```python
# api/docs/__init__.py
from flask import Blueprint, render_template

docs_blueprint = Blueprint('docs', __name__, url_prefix='/docs', template_folder='templates')

@docs_blueprint.route('/')
def index():
    return render_template('docs/index.html')

@docs_blueprint.route('/reference')
def reference():
    return render_template('docs/reference.html')

@docs_blueprint.route('/examples')
def examples():
    return render_template('docs/examples.html')
```

Create the necessary template files in a `templates/docs` directory with HTML documentation about your API.

#### C. API Usage Examples

Let's create a dedicated endpoint that provides examples of how to use the API:

```python
# api/v1/routes.py (additional endpoint)
examples_ns = api.namespace('examples', description='API usage examples')

@examples_ns.route('')
class Examples(Resource):
    @examples_ns.doc(security='apikey')
    @require_api_token
    def get(self):
        """Get examples of how to use the API"""
        return {
            'examples': [
                {
                    'name': 'Process email summary',
                    'description': 'Extract key information from an email',
                    'request': {
                        'method': 'POST',
                        'url': '/api/v1/webhook',
                        'headers': {
                            'Content-Type': 'application/json',
                            'X-API-Token': '[your-api-token]'
                        },
                        'body': {
                            'prompt': 'Please summarize this email: We need to schedule a meeting to discuss Q3 results.',
                            'source': 'email',
                            'type': 'summary'
                        }
                    },
                    'response': {
                        'summary': 'A meeting needs to be scheduled to discuss Q3 results.',
                        'processing_time': 1.25
                    }
                },
                # Add more examples here
            ]
        }
```

### 2. PythonAnywhere Deployment

Now let's prepare for deployment to PythonAnywhere by creating the necessary configuration files and documentation.

#### A. WSGI Configuration File

Create a PythonAnywhere-specific WSGI file:

```python
# pythonanywhere_wsgi.py
import sys
import os

# Add the project directory to the system path
project_path = '/home/yourusername/flaskllm'
if project_path not in sys.path:
    sys.path.append(project_path)

# Configure virtual environment
os.environ['VIRTUAL_ENV'] = '/home/yourusername/flaskllm/venv'
os.environ['PATH'] = '/home/yourusername/flaskllm/venv/bin:' + os.environ['PATH']

# Import the application
from wsgi import application
```

#### B. Deployment Documentation

Let's create a comprehensive deployment guide:

```markdown
# PythonAnywhere Deployment Guide

This guide walks through the process of deploying the FlaskLLM API to PythonAnywhere.

## Prerequisites

1. PythonAnywhere account (Free or paid plan)
2. Git repository with the FlaskLLM API code
3. LLM API keys (OpenAI, Anthropic, etc.)

## Deployment Steps

### 1. Create a PythonAnywhere Account

If you don't already have one, sign up at [PythonAnywhere](https://www.pythonanywhere.com/).

### 2. Set Up a Web App

1. Log in to your PythonAnywhere dashboard
2. Navigate to the Web tab
3. Click "Add a new web app"
4. Choose "Manual configuration" (not "Flask")
5. Select "Python 3.10"
6. Click "Next"

### 3. Clone the Repository

1. Open a Bash console from the dashboard
2. Clone your repository:
   ```bash
   git clone https://github.com/yourusername/flaskllm.git
   ```
3. Navigate to the project directory:
   ```bash
   cd flaskllm
   ```

### 4. Set Up Virtual Environment

1. Create a virtual environment:
   ```bash
   python3 -m venv venv
   ```
2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 5. Configure Environment Variables

1. Create a `.env` file in your project directory:
   ```bash
   touch .env
   ```
2. Open the file with the editor and add your environment variables:
   ```
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
   ```
3. Set proper permissions to protect your API keys:
   ```bash
   chmod 600 .env
   ```

### 6. Configure the WSGI File

1. Go back to the Web tab in your dashboard
2. Look for the WSGI configuration file path and click to edit it
3. Replace the contents with the code from `pythonanywhere_wsgi.py`, but update the paths to match your username and setup
4. Save the file

### 7. Configure Static Files (If Needed)

1. In the Web tab, scroll down to "Static files"
2. Add a new mapping:
   - URL: `/static/`
   - Directory: `/home/yourusername/flaskllm/static/`

### 8. Set Up Log Files

1. In the Web tab, note the path to your error log
2. This will be useful for debugging any issues

### 9. Reload Your Web App

1. Click the "Reload" button in the Web tab
2. Wait for the app to restart

### 10. Test Your Deployment

1. Test the health check endpoint:
   ```
   https://yourusername.pythonanywhere.com/api/v1/health
   ```
2. If everything is working, you should see a success response

## Troubleshooting

### Common Issues

1. **Import Errors**:
   - Check that your virtual environment is set up correctly
   - Verify all dependencies are installed

2. **Authentication Failures**:
   - Check that your `.env` file has the correct API_TOKEN

3. **LLM API Errors**:
   - Verify your LLM provider API keys
   - Check for rate limits or service disruptions

### Viewing Logs

To view application logs:
1. Navigate to the "Files" tab
2. Look for log files in the specified directory from the Web tab
3. Use `tail -f` in a Bash console to watch logs in real-time

### Getting Help

If you encounter issues not covered here, check:
- PythonAnywhere's help documentation
- Flask documentation
- Project issues in the GitHub repository
```

### 3. Office Scripts Integration

Now let's create example scripts for Excel integration.

#### A. Office Script for Excel

```typescript
/**
 * FlaskLLM API Office Script for Excel
 * This script demonstrates how to integrate with the FlaskLLM API from Excel.
 */

/**
 * Process a prompt using the FlaskLLM API.
 * @param prompt The text to process
 * @param type The type of processing (summary, keywords, etc.)
 * @param source The source of the prompt (email, meeting, etc.)
 * @customfunction
 */
async function processPrompt(
  prompt: string,
  type: string = "summary",
  source: string = "excel"
): Promise<string> {
  try {
    // API configuration
    const apiUrl = "https://yourusername.pythonanywhere.com/api/v1/webhook";
    const apiToken = "your_api_token"; // Store this securely

    // Request configuration
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Token": apiToken
      },
      body: JSON.stringify({
        prompt: prompt,
        type: type,
        source: source,
        language: "en"
      })
    });

    // Check for errors
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(`API error: ${errorData.error || response.status}`);
    }

    // Process response
    const result = await response.json();
    return result.summary;
  } catch (error) {
    console.error("Error processing prompt:", error);
    return `Error: ${error.message}`;
  }
}

/**
 * Main function to process selected cell content with the LLM API.
 */
async function main(workbook: ExcelScript.Workbook) {
  // Get the active worksheet
  const sheet = workbook.getActiveWorksheet();

  // Get the selected range
  const selectedRange = workbook.getSelectedRange();

  if (!selectedRange) {
    console.log("No cells selected. Please select a cell with content to process.");
    return;
  }

  // Get the content from the selected cell
  const content = selectedRange.getText();

  if (!content) {
    console.log("Selected cell is empty. Please select a cell with content.");
    return;
  }

  // Show processing message
  console.log("Processing content with LLM API...");

  try {
    // Process the content
    const result = await processPrompt(content, "summary", "excel");

    // Write the result to the cell to the right of the selected cell
    const resultCell = sheet.getCell(
      selectedRange.getRowIndex(),
      selectedRange.getColumnIndex() + 1
    );
    resultCell.setValue(result);

    console.log("Processing complete!");
  } catch (error) {
    console.error("Error:", error.message);
  }
}
```

#### B. Documentation for Excel Integration

Let's create comprehensive documentation for Excel integration:

```markdown
# Excel Integration Guide

This guide explains how to integrate the FlaskLLM API with Microsoft Excel using Office Scripts.

## Prerequisites

1. Microsoft Excel (web version or desktop with Office Scripts support)
2. Access to the FlaskLLM API with a valid API token
3. Basic familiarity with Excel and Office Scripts

## Setup Instructions

### 1. Add the Office Script to Excel

1. Open Excel (web version or desktop)
2. Navigate to the "Automate" tab
3. Click "New Script"
4. Delete any template code
5. Paste the provided Office Script code
6. Update the `apiUrl` and `apiToken` values with your specific configuration
7. Save the script with a name (e.g., "FlaskLLM Processor")

### 2. Configure API Access

1. Ensure your API token is properly configured
2. If using a corporate environment, verify network permissions allow access to the API endpoint

### 3. Using the Script

#### Method 1: Run the Script Directly

1. Select a cell containing text you want to process
2. Navigate to the "Automate" tab
3. Select your "FlaskLLM Processor" script
4. Click "Run"
5. The processed result will appear in the cell to the right of your selection

#### Method 2: Use the Custom Function

The script also defines a custom function that can be used in your Excel formulas:

1. In any cell, enter a formula like:
   ```
   =processPrompt(A1, "summary", "excel")
   ```
2. The function will process the content in cell A1 using the FlaskLLM API
3. Parameters:
   - First parameter: Cell reference with content to process
   - Second parameter: Type of processing (summary, keywords, etc.)
   - Third parameter: Source of the content

## Example Use Cases

1. **Email Processing**: Copy email content into Excel and process it to extract key points
2. **Meeting Notes**: Summarize meeting notes in a structured format
3. **Document Analysis**: Extract entities or keywords from document text
4. **Content Translation**: Translate content to different languages

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Verify your API token is correct
   - Check that the token is being included in the request headers

2. **Connection Issues**:
   - Ensure your network allows connections to the API endpoint
   - Check that the API server is running and accessible

3. **Processing Errors**:
   - Check content length (the API has a maximum prompt length)
   - Verify the API service is functioning correctly

### Getting Help

If you encounter issues not covered here, contact your API administrator or check the API documentation.
```

### 4. Next Tasks for Implementation

After completing the above tasks, you'll be ready to move on to:

1. **Enhanced Functionality**
   - Implement caching for frequent requests
   - Add prompt templates
   - Set up streaming responses

2. **Monitoring and Analytics**
   - Configure usage tracking
   - Implement cost monitoring
   - Set up error alerting

## Implementation Strategy

Here's a recommended implementation strategy:

1. **Start with API Documentation**
   - This will make testing and understanding your API easier for future development
   - The Swagger UI provides immediate visual feedback on your API design

2. **Prepare Deployment Configuration**
   - Configure all necessary files for PythonAnywhere
   - Test deployment on a development branch before going live

3. **Create Client Integration Examples**
   - Develop and test the Office Script for Excel integration
   - Document usage patterns for end users

4. **Add Enhanced Features**
   - Implement caching and other performance optimizations
   - Add more sophisticated prompt handling capabilities

## Security Considerations

Throughout these implementations, maintain focus on security:

1. **API Documentation**: Ensure sensitive information is not exposed in examples
2. **Deployment**: Use secure environment variable handling for API keys
3. **Client Integration**: Store API tokens securely and implement proper error handling
4. **Enhanced Features**: Apply appropriate access controls to cached data

## Testing Approach

For each component:

1. **API Documentation**: Verify all endpoints are correctly documented and examples work as expected
2. **PythonAnywhere Deployment**: Test the deployed application thoroughly, particularly authentication and error handling
3. **Office Scripts Integration**: Test with various input types and error conditions
4. **Enhanced Features**: Verify performance improvements and ensure they don't introduce security vulnerabilities

## Conclusion

This implementation plan addresses the next set of tasks in your FlaskLLM API project, focusing on user-facing documentation, deployment, and client integration. By following this plan, you'll create a well-documented, properly deployed API that's ready for integration with Excel and other client applications.

Would you like me to dive deeper into any specific component of this plan or start implementing a particular section first?
