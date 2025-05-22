# Example of properly mocking OpenAI in a test
@patch("flaskllm.llm.openai_handler.OpenAI")
def test_openai_handler_process_prompt(mock_openai):
    # Setup mock response
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]
    mock_client.chat.completions.create.return_value = mock_response
    
    # Create handler and call process_prompt
    handler = OpenAIHandler(api_key="test_key")
    result = handler.process_prompt("Test prompt")
    
    # Verify result
    assert result == "Test response"
    mock_client.chat.completions.create.assert_called_once()
