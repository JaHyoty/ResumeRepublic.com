# LLM Configuration

This application uses OpenRouter.ai for LLM access with Claude Sonnet 4.0 (Claude 3.5 Sonnet) for resume generation.

## Setup

1. Get an API key from [OpenRouter.ai](https://openrouter.ai/)
2. Run the setup script:
   ```bash
   ./setup_openrouter.sh
   ```
   Or manually set the environment variables:
   ```bash
   export OPENROUTER_API_KEY="your-api-key-here"
   export OPENROUTER_LLM_MODEL="anthropic/claude-3.5-sonnet"
   ```

## Testing

Test your OpenRouter configuration:
```bash
python test_openrouter.py
```

## Model Used

- **Provider**: OpenRouter.ai
- **Model**: `anthropic/claude-3.5-sonnet` (Claude Sonnet 4.0)
- **Use Case**: Resume generation and optimization

## Features

- Professional resume writing with ATS optimization
- Keyword identification from job descriptions
- X,Y,Z format for achievements
- LaTeX template integration
- Comprehensive error handling

## Configuration

The LLM service is configured in `app/services/llm_service.py` and uses the following settings:

- **Model**: Configurable via `OPENROUTER_LLM_MODEL` (default: `anthropic/claude-3.5-sonnet`)
- **API Key**: Set via `OPENROUTER_API_KEY` environment variable
- **Timeout**: 60 seconds
- **Headers**: Minimal headers for OpenRouter compatibility

### Environment Variables

- `OPENROUTER_API_KEY`: Your OpenRouter API key (required)
- `OPENROUTER_LLM_MODEL`: Model to use (optional, defaults to Claude 3.5 Sonnet)

## Error Handling

The service includes comprehensive error handling for:
- API request failures
- Authentication errors
- Rate limiting
- Invalid responses
- Network timeouts
