# Deploying to PythonAnywhere

This guide provides detailed instructions for deploying the FlaskLLM API to PythonAnywhere.

## Prerequisites

1. A PythonAnywhere account (free tier is fine for starting)
2. Git repository with your code
3. Your API keys and secrets

## Step 1: Create a PythonAnywhere Account

1. Go to [PythonAnywhere](https://www.pythonanywhere.com/) and create an account if you don't have one.
2. Verify your email and log in.

## Step 2: Set Up a Web App

1. Go to the Web tab in your dashboard.
2. Click "Add a new web app".
3. Choose the domain name (e.g., `yourusername.pythonanywhere.com`).
4. Select "Manual configuration" (not "Flask").
5. Choose Python 3.10 (or latest available).

## Step 3: Clone Your Repository

1. Open a Bash console from the PythonAnywhere dashboard.
2. Clone your repository:
   ```bash
   git clone https://github.com/yourusername/flaskllm.git
   ```
3. Create a virtual environment:
   ```bash
   cd flaskllm
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Step 4: Configure Environment Variables

1. Create a `.env` file:
   ```bash
   nano .env
   ```

2. Add your environment variables:
   ```
   OPENAI_API_KEY=your_openai_key
   API_TOKEN=your_api_token
   ```

3. Save the file (CTRL+X, then Y, then Enter).

## Step 5: Configure the WSGI File

1. Go to the Web tab and click on the WSGI configuration file link (e.g., `/var/www/yourusername_pythonanywhere_com_wsgi.py`).

2. Replace the contents with:
   ```python
   import sys
   import os

   # Add your project directory to the Python path
   path = '/home/yourusername/flaskllm'
   if path not in sys.path:
       sys.path.append(path)

   # Point to your virtual environment
   os.environ['VIRTUAL_ENV'] = '/home/yourusername/flaskllm/venv'
   os.environ['PATH'] = '/home/yourusername/flaskllm/venv/bin:' + os.environ['PATH']

   # Import your application
   from wsgi import application
   ```

3. Save the file.

## Step 6: Configure Static Files (if needed)

1. Go to the Web tab.
2. In the Static Files section, add:
   - URL: `/static/`
   - Directory: `/home/yourusername/flaskllm/static/`

## Step 7: Reload Your Web App

1. Go to the Web tab.
2. Click the "Reload" button for your web app.

## Step 8: Check the Error Logs

1. If you encounter issues, check the error logs in the Web tab.
2. Click on the "Error log" link to view any errors.

## Step 9: Test Your API

1. Use Postman or curl to test your API:
   ```bash
   curl -X POST -H "Content-Type: application/json" -H "X-API-Token: your_api_token" -d '{"prompt":"Test prompt"}' https://yourusername.pythonanywhere.com/api/v1/webhook
   ```

## Useful PythonAnywhere Features

1. **Scheduled Tasks**: Use for regular maintenance or cleanup tasks.
2. **Always-on Tasks**: Available in paid plans for background processes.
3. **Consoles**: Access Bash, Python, and other consoles for debugging.

## Updating Your Application

1. Open a Bash console.
2. Navigate to your project directory:
   ```bash
   cd flaskllm
   ```
3. Pull the latest changes:
   ```bash
   git pull
   ```
4. Install any new dependencies:
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```
5. Reload your web app from the Web tab.

## Security Considerations for PythonAnywhere

1. **Environment Variables**: Store sensitive data in your .env file, not in code.
2. **API Token**: Use a strong, unique token for your API.
3. **File Permissions**: Ensure sensitive files are not world-readable:
   ```bash
   chmod 600 .env
   ```
4. **HTTPS**: PythonAnywhere provides HTTPS by default, always use it.
5. **Rate Limiting**: Implement rate limiting to prevent abuse.
```

## Next Steps and Future Extensions

To continue enhancing your API after implementing these initial improvements:

### 1. Monitoring and Observability

- Implement application monitoring with Sentry or New Relic
- Add OpenTelemetry for distributed tracing
- Set up custom metrics collection for LLM response times and error rates

### 2. Advanced LLM Features

- Implement prompt templating for different use cases
- Add streaming responses for long-running requests
- Implement result caching for common prompts
- Add support for multiple LLM providers (OpenAI, Anthropic, etc.)

### 3. Security Enhancements

- Implement JWT-based authentication for more advanced use cases
- Add IP allowlisting for trusted sources
- Set up audit logging for security-sensitive operations

### 4. Integration Capabilities

- Add webhook endpoints for specific integrations (Google Calendar, etc.)
- Implement callback URLs for asynchronous processing
- Create specialized endpoints for different data sources

### 5. Infrastructure Improvements

- Set up automatic backups of configuration and logs
- Implement health checks and alerting
- Create CI/CD for automated testing and deployment

## Conclusion

This comprehensive plan transforms your basic API into a production-ready, secure, and scalable service. By implementing proper architecture, security measures, error handling, and testing, you'll create a robust foundation that can grow with your needs.

Start with the core improvements to structure, security, and error handling, then progressively implement the more advanced features. This approach ensures you're building on a solid foundation while continuing to enhance capabilities.
