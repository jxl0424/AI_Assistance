# JARVIS - AI Voice Assistant

A professional AI voice assistant built with Python, featuring speech recognition, 
natural language processing, and various productivity tools.

## Features

- Voice-activated AI assistant
- Speech-to-text with Whisper
- Text-to-speech with edge-tts
- Finance tracking with SQLite
- Reminder system (one-time, recurring, timers)
- Memory management
- Web search and weather
- Professional logging system
- GUI interface

## Project Structure

```
AI_Assistance/
├── src/                    # Source code
│   ├── core/              # Core components
│   │   ├── llm_core.py
│   │   ├── command_executor.py
│   │   └── logger_config.py
│   ├── modules/           # Feature modules
│   │   ├── speech_to_text.py
│   │   ├── tts_engine.py
│   │   ├── reminder_manager.py
│   │   └── ...
│   ├── utils/             # Utilities
│   │   ├── apps_config.py
│   │   └── config.py
│   └── main.py            # Entry point
├── config/                # Configuration
│   └── environment.yaml
├── docs/                  # Documentation
├── tests/                 # Test files
├── scripts/               # Utility scripts
├── logs/                  # Log files
└── data/                  # Data storage
```

## Installation

1. Create conda environment:
```bash
conda env create -f config/environment.yaml
conda activate jarvis_agent
```

2. Install Ollama and pull model:
```bash
ollama pull llama3.2
```

## Usage

```bash
python src/main.py
```

## Requirements

- Python 3.10+
- Ollama (for LLM)
- Microphone for voice input
- See config/environment.yaml for full dependencies

## Documentation

See `docs/` directory for detailed documentation.

## License

MIT License
