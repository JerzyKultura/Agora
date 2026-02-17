# Agora Colab Quick Start

This example demonstrates a production-ready Agora workflow for Google Colab.

## Installation

```python
# Install Agora with telemetry support
!pip install "git+https://github.com/JerzyKultura/Agora.git#egg=agora[telemetry]"

# Install optional dependencies
!pip install openai  # For real OpenAI integration
!pip install nest-asyncio  # For Colab async support
```

## Setup

```python
# Set your API keys (optional)
import os
os.environ["AGORA_API_KEY"] = "your-agora-api-key"
os.environ["OPENAI_API_KEY"] = "your-openai-api-key"  # Optional
```

## Run the Example

```python
# Run the demo
!python colab_demo.py
```

## Features Demonstrated

✅ **Proper Initialization** - Telemetry setup with cloud upload  
✅ **Error Handling** - Graceful fallbacks when APIs are unavailable  
✅ **Real API Integration** - OpenAI integration with mock fallback  
✅ **Multi-Node Workflow** - 4-node pipeline with clear data flow  
✅ **Shared State Management** - Proper data passing between nodes  
✅ **Async/Await Patterns** - Production-ready async execution  
✅ **Colab Compatibility** - nest_asyncio for notebook environments  

## Workflow Structure

```
FetchUserInput → EnrichPrompt → GenerateResponse → FormatOutput
```

1. **FetchUserInput**: Validates and prepares user input
2. **EnrichPrompt**: Adds context and instructions
3. **GenerateResponse**: Calls OpenAI API (or uses mock)
4. **FormatOutput**: Formats final output with metadata

## Customization

Modify the `initial_input` in the `main()` function to change the question:

```python
initial_input = {
    "user_prompt": "Your custom question here"
}
```

## Telemetry

All workflow execution is automatically tracked and uploaded to Agora Cloud when `enable_cloud_upload=True`. View your workflows at your Agora dashboard.
