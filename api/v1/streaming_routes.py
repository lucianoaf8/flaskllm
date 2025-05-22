# api/v1/routes.py
from flask import Response, stream_with_context

@api_v1.route('/stream', methods=['POST'])
@require_api_token
def stream_prompt():
    """
    Process a prompt with the configured LLM provider and stream the response.

    Returns:
        Streamed response from LLM
    """
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

    try:
        # Get custom parameters
        custom_params = request.json.get('parameters', {})

        # Get LLM handler
        llm_handler = get_llm_handler()

        # Start the streaming response
        def generate():
            try:
                # Process the prompt with streaming enabled
                for chunk in llm_handler.process_prompt(
                    prompt=data['prompt'],
                    source=data.get('source'),
                    language=data.get('language'),
                    type=data.get('type'),
                    stream=True,
                    **custom_params
                ):
                    yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            except Exception as e:
                logger.error(f"Streaming error: {str(e)}", exc_info=True)
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

            # End the stream
            yield "data: [DONE]\n\n"

        # Return the streamed response
        return Response(
            stream_with_context(generate()),
            content_type='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'  # Disable buffering in Nginx
            }
        )
    except Exception as e:
        logger.error(f"Error processing prompt: {str(e)}", exc_info=True)
        return {
            'error': 'LLM API Error',
            'details': str(e),
            'code': 'LLM_API_ERROR'
        }, 502
